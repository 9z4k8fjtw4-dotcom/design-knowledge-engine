from pathlib import Path

from automation.scripts import design_knowledge_engine as engine


def test_runtime_paths_are_path_objects():
    assert isinstance(engine.ROOT, Path)
    assert isinstance(engine.CONFIG_FILE, Path)
    assert isinstance(engine.INDEX_FILE, Path)


def test_relative_paths_use_posix_format():
    path = engine.ROOT / "sample_output" / "knowledge_base" / "card.md"

    assert engine.rel(path) == "sample_output/knowledge_base/card.md"


def test_safe_part_removes_cross_platform_invalid_characters():
    value = 'garden:room\\card/name*?"<>|'

    assert engine.safe_part(value) == "garden_room_card_name"
