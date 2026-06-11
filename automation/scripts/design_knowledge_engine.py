#!/usr/bin/env python3
"""Design-Knowledge-Engine.

This script handles local file workflow only:
Image collection -> index -> placeholder analysis -> rename -> Markdown -> knowledge base archive.
No retrieval system, vector database, web service, user system, or permission system is implemented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "automation/config/settings.json"
INDEX_FILE = ROOT / "automation/database/image_index.json"
ANALYSIS_LOG = ROOT / "automation/logs/analysis.log"
ARCHIVE_LOG = ROOT / "automation/logs/archive.log"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def month() -> str:
    return datetime.now().strftime("%Y-%m")


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings() -> dict[str, Any]:
    settings = load_json(CONFIG_FILE, {})
    if not settings:
        raise FileNotFoundError(f"Missing config file: {CONFIG_FILE}")
    return settings


def root_path(relative: str) -> Path:
    return ROOT / relative


def settings_path(settings: dict[str, Any], key: str) -> Path:
    return root_path(settings["paths"][key])


def log_event(log_file: Path, event: str, payload: dict[str, Any]) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": now(), "event": event, **payload}
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_meta(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "width": None,
        "height": None,
        "format": path.suffix.lower().lstrip("."),
    }
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            meta.update({"width": img.width, "height": img.height, "format": img.format})
    except Exception:
        pass
    return meta


def safe_part(value: str) -> str:
    banned = '/\\:*?"<>|\n\r\t'
    result = value.strip()
    for char in banned:
        result = result.replace(char, "_")
    result = result.replace(" ", "_")
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("._ ") or "未分类"


def image_extensions(settings: dict[str, Any]) -> set[str]:
    return {ext.lower() for ext in settings.get("image_extensions", [])}


def is_image(path: Path, settings: dict[str, Any]) -> bool:
    return path.is_file() and path.suffix.lower() in image_extensions(settings)


def load_index() -> dict[str, Any]:
    index = load_json(INDEX_FILE, {"schema_version": 2, "updated_at": None, "images": {}})
    return migrate_index(index)


def save_index(index: dict[str, Any]) -> None:
    migrate_index(index)
    index["schema_version"] = 2
    index["updated_at"] = now()
    write_json(INDEX_FILE, index)


def existing_hash(index: dict[str, Any], digest: str) -> str | None:
    for image_id, record in index.get("images", {}).items():
        if (record.get("hash") == digest or record.get("sha256") == digest) and record.get("status") != "duplicate":
            return image_id
    return None


def event_history(record: dict[str, Any], event: str, extra: dict[str, Any] | None = None) -> None:
    history = record.setdefault("event_history", [])
    history.append({"time": now(), "event": event, **(extra or {})})


def make_image_id(digest: str | None = None) -> str:
    return make_uuid()


def make_uuid() -> str:
    return str(uuid.uuid4())


def ensure_scaffold(settings: dict[str, Any]) -> None:
    for key in settings.get("paths", {}):
        settings_path(settings, key).mkdir(parents=True, exist_ok=True)
    for category in settings["markdown"]["categories"].values():
        (settings_path(settings, "design_archive") / category).mkdir(parents=True, exist_ok=True)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        write_json(INDEX_FILE, {"schema_version": 2, "updated_at": None, "images": {}})
    ANALYSIS_LOG.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_LOG.touch(exist_ok=True)
    ARCHIVE_LOG.touch(exist_ok=True)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter:03d}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def next_sequence(prefix: str, suffix: str, folders: list[Path], width: int) -> int:
    max_seen = 0
    for folder in folders:
        if not folder.exists():
            continue
        for path in folder.rglob(f"{prefix}_*"):
            tail = path.stem.replace(prefix + "_", "")
            if tail.isdigit():
                max_seen = max(max_seen, int(tail))
    return max_seen + 1


def rename_target(settings: dict[str, Any], tags: list[str], suffix: str) -> str:
    rename_cfg = settings.get("rename", {})
    max_parts = int(rename_cfg.get("max_tag_parts", 3))
    width = int(rename_cfg.get("sequence_width", 3))
    parts = [safe_part(tag) for tag in tags if tag.strip()]
    if not parts:
        parts = [safe_part(tag) for tag in rename_cfg.get("default_tags", ["未分类", "图片", "待分析"])]
    prefix = "_".join(parts[:max_parts])
    folders = [
        settings_path(settings, "inbox_pending_analysis"),
        settings_path(settings, "inbox_pending_confirm"),
        settings_path(settings, "assets_reviewed"),
        settings_path(settings, "assets_archive"),
    ]
    seq = next_sequence(prefix, suffix, folders, width)
    return f"{prefix}_{seq:0{width}d}{suffix.lower()}"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def scan(settings: dict[str, Any]) -> int:
    ensure_scaffold(settings)
    index = load_index()
    inbox = settings_path(settings, "inbox_new")
    pending = settings_path(settings, "inbox_pending_analysis")
    raw_dir = settings_path(settings, "assets_raw") / today()
    rejected = settings_path(settings, "inbox_rejected")
    raw_dir.mkdir(parents=True, exist_ok=True)
    moved = 0

    for path in sorted(inbox.iterdir()):
        if not is_image(path, settings):
            continue
        digest = sha256(path)
        duplicate_of = existing_hash(index, digest)
        meta = image_meta(path)
        image_id = make_image_id(digest)

        if duplicate_of:
            target = unique_path(rejected / f"duplicate_{path.name}")
            shutil.move(str(path), target)
            record = {
                "id": image_id,
                "uuid": image_id,
                "schema_version": 2,
                "original_filename": path.name,
                "current_filename": target.name,
                "source_path": rel(path),
                "current_path": rel(target),
                "image_path": rel(target),
                "created_time": datetime.fromtimestamp(target.stat().st_ctime).isoformat(timespec="seconds"),
                "created_at": now(),
                "first_seen": now(),
                "updated_at": now(),
                "status": "duplicate",
                "duplicate_of": duplicate_of,
                "hash": digest,
                "sha256": digest,
                "tags": [],
                "auto_tags": [],
                "manual_tags": [],
                "analysis": {},
                "analysis_result_path": None,
                "analysis_json_path": None,
                "markdown_path": None,
                "asset_path": None,
                "chunked": false_value(),
                "embedded": false_value(),
                "future": future_fields(),
                **meta,
            }
            event_history(record, "Duplicate_Image_Event", {"duplicate_of": duplicate_of})
            index["images"][image_id] = record
            log_event(ANALYSIS_LOG, "Duplicate_Image_Event", {"image_id": image_id, "duplicate_of": duplicate_of})
            continue

        raw_copy = unique_path(raw_dir / path.name)
        shutil.copy2(path, raw_copy)
        target = unique_path(pending / path.name)
        shutil.move(str(path), target)

        record = {
            "id": image_id,
            "uuid": image_id,
            "schema_version": 2,
            "original_filename": path.name,
            "current_filename": target.name,
            "source_path": rel(path),
            "raw_backup_path": rel(raw_copy),
            "current_path": rel(target),
            "image_path": rel(target),
            "created_time": datetime.fromtimestamp(target.stat().st_ctime).isoformat(timespec="seconds"),
            "created_at": now(),
            "first_seen": now(),
            "updated_at": now(),
            "status": "pending_analysis",
            "hash": digest,
            "sha256": digest,
            "tags": [],
            "auto_tags": [],
            "manual_tags": [],
            "analysis": {},
            "analysis_result_path": None,
            "analysis_json_path": None,
            "markdown_path": None,
            "asset_path": None,
            "chunked": false_value(),
            "embedded": false_value(),
            "duplicate_of": None,
            "future": future_fields(),
            **meta,
        }
        event_history(record, "New_Image_Event")
        event_history(record, "Image_Indexed_Event")
        index["images"][image_id] = record
        moved += 1
        log_event(ANALYSIS_LOG, "New_Image_Event", {"image_id": image_id, "path": rel(target)})

    save_index(index)
    return moved


def future_fields() -> dict[str, Any]:
    return {
        "embedding_id": None,
        "vector_db_id": None,
        "agent_task_id": None,
        "rag_source_id": None,
        "chunk_ids": [],
        "model_versions": {},
        "reviewer": None,
        "score": None,
        "source_app": None,
        "source_project": None,
        "rights_status": None,
        "manual_notes": None,
        "linked_design_rule": None,
        "linked_success_case": None,
        "linked_failure_case": None,
    }


def false_value() -> bool:
    return False


def normalize_record(record: dict[str, Any], image_id: str | None = None) -> dict[str, Any]:
    digest = record.get("hash") or record.get("sha256")
    current_path = record.get("image_path") or record.get("current_path") or record.get("asset_path")
    created_at = record.get("created_at") or record.get("first_seen") or record.get("created_time") or now()
    record.setdefault("id", image_id or make_image_id(str(digest or uuid.uuid4())))
    record.setdefault("uuid", record["id"])
    record["schema_version"] = 2
    record.setdefault("hash", digest)
    record.setdefault("sha256", digest)
    record.setdefault("created_at", created_at)
    record.setdefault("updated_at", now())
    record.setdefault("status", "new")
    record.setdefault("tags", [])
    record.setdefault("auto_tags", [])
    record.setdefault("manual_tags", [])
    record.setdefault("analysis", {})
    record.setdefault("analysis_result_path", record.get("markdown_path"))
    record.setdefault("analysis_json_path", None)
    record.setdefault("markdown_path", None)
    record.setdefault("asset_path", None)
    record.setdefault("image_path", current_path)
    record.setdefault("current_path", current_path)
    record.setdefault("chunked", False)
    record.setdefault("embedded", False)
    record.setdefault("future", future_fields())
    for key, value in future_fields().items():
        record["future"].setdefault(key, value)
    return record


def migrate_index(index: dict[str, Any]) -> dict[str, Any]:
    index.setdefault("images", {})
    index["schema_version"] = 2
    for image_id, record in list(index["images"].items()):
        normalize_record(record, image_id=image_id)
    return index


def import_batch(settings: dict[str, Any]) -> int:
    ensure_scaffold(settings)
    index = load_index()
    source_dir = settings_path(settings, "source_batch")
    pending = settings_path(settings, "inbox_pending_analysis")
    imported = 0

    for path in sorted(source_dir.rglob("*")):
        if not is_image(path, settings):
            continue
        digest = sha256(path)
        duplicate_of = existing_hash(index, digest)
        image_id = make_image_id(digest)
        meta = image_meta(path)

        if duplicate_of:
            record = {
                "id": image_id,
                "uuid": image_id,
                "schema_version": 2,
                "original_filename": path.name,
                "current_filename": path.name,
                "source_path": rel(path),
                "current_path": rel(path),
                "image_path": rel(path),
                "created_time": datetime.fromtimestamp(path.stat().st_ctime).isoformat(timespec="seconds"),
                "created_at": now(),
                "first_seen": now(),
                "updated_at": now(),
                "status": "duplicate",
                "duplicate_of": duplicate_of,
                "hash": digest,
                "sha256": digest,
                "tags": [],
                "auto_tags": [],
                "manual_tags": [],
                "analysis": {},
                "analysis_result_path": None,
                "analysis_json_path": None,
                "markdown_path": None,
                "asset_path": None,
                "chunked": False,
                "embedded": False,
                "future": future_fields(),
                "source_collection": "image_batch",
                **meta,
            }
            event_history(record, "Batch_Duplicate_Event", {"duplicate_of": duplicate_of})
            index["images"][image_id] = record
            log_event(ANALYSIS_LOG, "Batch_Duplicate_Event", {"image_id": image_id, "duplicate_of": duplicate_of, "path": rel(path)})
            continue

        target = unique_path(pending / path.name)
        shutil.copy2(path, target)
        record = {
            "id": image_id,
            "uuid": image_id,
            "schema_version": 2,
            "original_filename": path.name,
            "current_filename": target.name,
            "source_path": rel(path),
            "batch_source_path": rel(path),
            "current_path": rel(target),
            "image_path": rel(target),
            "created_time": datetime.fromtimestamp(path.stat().st_ctime).isoformat(timespec="seconds"),
            "created_at": now(),
            "first_seen": now(),
            "updated_at": now(),
            "status": "new",
            "hash": digest,
            "sha256": digest,
            "tags": [],
            "auto_tags": [],
            "manual_tags": [],
            "analysis": {},
            "analysis_result_path": None,
            "analysis_json_path": None,
            "markdown_path": None,
            "asset_path": None,
            "duplicate_of": None,
            "chunked": False,
            "embedded": False,
            "future": future_fields(),
            "source_collection": "image_batch",
            **meta,
        }
        event_history(record, "Batch_Image_Imported_Event")
        event_history(record, "Image_Indexed_Event")
        event_history(record, "Image_Queued_For_Analysis_Event", {"queued_path": rel(target)})
        index["images"][image_id] = record
        imported += 1
        log_event(ANALYSIS_LOG, "Batch_Image_Imported_Event", {"image_id": image_id, "source": rel(path), "queued": rel(target)})

    save_index(index)
    return imported


def select_records(index: dict[str, Any], status: str, file_value: str | None) -> list[dict[str, Any]]:
    records = list(index.get("images", {}).values())
    if file_value:
        return [
            record
            for record in records
            if record.get("id") == file_value
            or record.get("current_filename") == file_value
            or Path(record.get("current_path", "")).name == file_value
        ]
    if status == "pending_analysis":
        return [record for record in records if record.get("status") in {"pending_analysis", "new"}]
    return [record for record in records if record.get("status") == status]


def markdown_content(record: dict[str, Any], image_path: Path, category: str = "04_待复核") -> str:
    tags = record.get("tags") or ["待分析"]
    tag_lines = "\n".join([f"  - design_language/{tag}" for tag in tags])
    image_link = rel(image_path)
    analysis = record.get("analysis", {})
    title = image_path.stem
    return f"""---
type: 图片分析
project: Design-Knowledge-Engine
status: {record.get("status")}
category: {category}
image_id: {record.get("id")}
source: image-to-knowledge workflow
created: {now()}
tags:
  - type/image_analysis
{tag_lines}
links:
  - "[[{image_link}]]"
---

# {title}

## Title

{title}

## Tags

{", ".join(tags)}

## Design Language

{analysis.get("design_language", "Pending manual input.")}

## Silhouette

{analysis.get("silhouette", "Pending manual input.")}

## Color

{analysis.get("color", "Pending manual input.")}

## Knowledge Value

{analysis.get("knowledge_value", "Pending manual input.")}

## Source Image Link

[[{image_link}]]

## Image Embed

![[{image_link}]]

## File Info

| Field | Value |
| --- | --- |
| Image ID | `{record.get("id")}` |
| Original filename | `{record.get("original_filename")}` |
| Current filename | `{image_path.name}` |
| SHA256 | `{record.get("sha256")}` |
| Status | {record.get("status")} |
| Analysis result path | `{record.get("analysis_result_path") or ""}` |

## Manual Review

Keep:

Archive direction:

Notes:
"""


def analyze(settings: dict[str, Any], file_value: str | None, tags: list[str]) -> int:
    ensure_scaffold(settings)
    index = load_index()
    records = select_records(index, "pending_analysis", file_value)
    confirm_dir = settings_path(settings, "inbox_pending_confirm")
    count = 0

    for record in records:
        current = ROOT / record["current_path"]
        if not current.exists():
            record["status"] = "error"
            record["updated_at"] = now()
            event_history(record, "Error_Event", {"reason": "current_path missing"})
            continue

        final_tags = tags or record.get("manual_tags") or record.get("auto_tags") or settings["rename"]["default_tags"]
        new_name = rename_target(settings, final_tags, current.suffix)
        renamed = unique_path(confirm_dir / new_name)
        shutil.move(str(current), renamed)

        record["current_filename"] = renamed.name
        record["current_path"] = rel(renamed)
        record["image_path"] = rel(renamed)
        record["status"] = "pending_confirm"
        record["tags"] = final_tags
        record["manual_tags"] = tags or record.get("manual_tags", [])
        record["analysis"] = {
            "design_language": "Pending manual input.",
            "silhouette": "Pending manual input.",
            "color": "Pending manual input.",
            "knowledge_value": "Pending manual input.",
        }
        record["updated_at"] = now()
        event_history(record, "Image_Renamed_Event", {"new_name": renamed.name})
        event_history(record, "Image_Analyzed_Event", {"mode": "mvp_placeholder"})

        md_path = confirm_dir / f"{renamed.stem}.md"
        md_path.write_text(markdown_content(record, renamed), encoding="utf-8")
        record["markdown_path"] = rel(md_path)
        record["analysis_result_path"] = rel(md_path)
        record["analysis_json_path"] = None
        log_event(ANALYSIS_LOG, "Image_Analyzed_Event", {"image_id": record["id"], "path": rel(renamed)})
        count += 1

    save_index(index)
    return count


def regenerate_markdown(settings: dict[str, Any], file_value: str | None) -> int:
    ensure_scaffold(settings)
    index = load_index()
    records = select_records(index, "pending_confirm", file_value)
    count = 0
    for record in records:
        image_path = ROOT / record["current_path"]
        if not image_path.exists():
            continue
        md_path = ROOT / record.get("markdown_path", "")
        if not md_path.name:
            md_path = image_path.with_suffix(".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown_content(record, image_path), encoding="utf-8")
        record["markdown_path"] = rel(md_path)
        record["analysis_result_path"] = rel(md_path)
        record["updated_at"] = now()
        event_history(record, "Markdown_Generated_Event")
        count += 1
    save_index(index)
    return count


def confirm(settings: dict[str, Any], file_value: str, result: str) -> int:
    ensure_scaffold(settings)
    index = load_index()
    records = select_records(index, "pending_confirm", file_value)
    if not records:
        return 0

    categories = settings["markdown"]["categories"]
    confirmed = 0
    for record in records:
        image_path = ROOT / record["current_path"]
        md_path = ROOT / record.get("markdown_path", "")
        if not image_path.exists():
            record["status"] = "error"
            event_history(record, "Error_Event", {"reason": "image missing during confirm"})
            continue

        if result == "reject":
            target_image = unique_path(settings_path(settings, "inbox_rejected") / image_path.name)
            shutil.move(str(image_path), target_image)
            target_md = unique_path(settings_path(settings, "inbox_rejected") / f"{target_image.stem}.md")
            if md_path.exists():
                shutil.move(str(md_path), target_md)
            record["status"] = "rejected"
            record["current_path"] = rel(target_image)
            record["image_path"] = rel(target_image)
            record["current_filename"] = target_image.name
            record["markdown_path"] = rel(target_md) if target_md.exists() else None
            record["updated_at"] = now()
            event_history(record, "Human_Confirmed_Event", {"result": "reject"})
            log_event(ARCHIVE_LOG, "Image_Rejected_Event", {"image_id": record["id"], "path": rel(target_image)})
            confirmed += 1
            continue

        category = categories.get(result, categories["review"])
        reviewed_dir = settings_path(settings, "assets_reviewed") / month()
        archive_dir = settings_path(settings, "design_archive") / category
        reviewed_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        target_image = unique_path(reviewed_dir / image_path.name)
        shutil.move(str(image_path), target_image)
        target_md = unique_path(archive_dir / f"{target_image.stem}.md")

        record["status"] = "archived"
        record["asset_path"] = rel(target_image)
        record["current_path"] = rel(target_image)
        record["image_path"] = rel(target_image)
        record["current_filename"] = target_image.name
        record["markdown_path"] = rel(target_md)
        record["analysis_result_path"] = rel(target_md)
        record["updated_at"] = now()
        event_history(record, "Human_Confirmed_Event", {"result": result, "category": category})
        event_history(record, "Markdown_Archived_Event", {"markdown_path": rel(target_md)})

        target_md.write_text(markdown_content(record, target_image, category=category), encoding="utf-8")
        if md_path.exists() and md_path != target_md:
            md_path.unlink()
        log_event(ARCHIVE_LOG, "Markdown_Archived_Event", {"image_id": record["id"], "image": rel(target_image), "markdown": rel(target_md)})
        confirmed += 1

    save_index(index)
    return confirmed


def status() -> dict[str, int]:
    index = load_index()
    counts: dict[str, int] = {}
    for record in index.get("images", {}).values():
        state = record.get("status", "unknown")
        counts[state] = counts.get(state, 0) + 1
    return counts


def print_status() -> None:
    counts = status()
    if not counts:
        print("暂无图片索引。")
        return
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")


def watch(settings: dict[str, Any], interval: int) -> None:
    print(f"开始监听：{settings['paths']['inbox_new']}，间隔 {interval} 秒。按 Ctrl+C 停止。")
    while True:
        moved = scan(settings)
        if moved:
            print(f"{now()} 新增图片：{moved}")
        time.sleep(interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Design-Knowledge-Engine 本地图片流转 MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="创建目录并初始化索引文件")
    sub.add_parser("migrate-index", help="升级 image_index.json 到当前Field结构")
    sub.add_parser("scan", help="扫描 01_Inbox/01_未整理图片 并移动到待分析")
    sub.add_parser("import-batch", help="导入 sample_data/image_batch 到待分析流程")

    analyze_parser = sub.add_parser("analyze", help="分析待分析图片，重命名并生成待确认 Markdown")
    analyze_parser.add_argument("--file", help="指定Image ID或文件名；不填则处理全部 pending_analysis")
    analyze_parser.add_argument("--tags", nargs="*", default=[], help="用于重命名和 Markdown 的标签，例如：帝政 植物壁画 高腰线")

    rename_parser = sub.add_parser("rename", help="MVP中等同于 analyze：重命名并生成 Markdown")
    rename_parser.add_argument("--file", help="指定Image ID或文件名")
    rename_parser.add_argument("--tags", nargs="*", default=[], help="重命名标签")

    markdown_parser = sub.add_parser("markdown", help="重新生成待人工确认 Markdown")
    markdown_parser.add_argument("--file", help="指定Image ID或文件名；不填则处理全部 pending_confirm")

    confirm_parser = sub.add_parser("confirm", help="人工确认后归档到 Assets 和设计语言库")
    confirm_parser.add_argument("--file", required=True, help="Image ID或Current filename")
    confirm_parser.add_argument("--result", choices=["style", "success", "failure", "review", "reject"], default="review")

    sub.add_parser("status", help="输出 image_index.json Status统计")

    watch_parser = sub.add_parser("watch", help="轮询监听 Inbox 新图")
    watch_parser.add_argument("--interval", type=int, default=5, help="轮询秒数")

    return parser


def main(argv: list[str] | None = None) -> int:
    settings = load_settings()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        ensure_scaffold(settings)
        index = load_index()
        save_index(index)
        print("Design-Knowledge-Engine 初始化完成。")
        return 0
    if args.command == "migrate-index":
        index = load_index()
        save_index(index)
        print("image_index.json Field升级完成。")
        return 0
    if args.command == "scan":
        moved = scan(settings)
        print(f"扫描完成，新增图片：{moved}")
        return 0
    if args.command == "import-batch":
        count = import_batch(settings)
        print(f"批量导入完成，新增图片：{count}")
        return 0
    if args.command in {"analyze", "rename"}:
        count = analyze(settings, args.file, args.tags)
        print(f"分析完成，处理图片：{count}")
        return 0
    if args.command == "markdown":
        count = regenerate_markdown(settings, args.file)
        print(f"Markdown 生成完成：{count}")
        return 0
    if args.command == "confirm":
        count = confirm(settings, args.file, args.result)
        print(f"确认归档完成：{count}")
        return 0
    if args.command == "status":
        print_status()
        return 0
    if args.command == "watch":
        watch(settings, args.interval)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
