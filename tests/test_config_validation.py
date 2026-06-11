import json
from pathlib import Path


CONFIG = Path("automation/config/settings.example.json")


def test_example_config_uses_relative_paths():
    settings = json.loads(CONFIG.read_text(encoding="utf-8"))

    for value in settings["paths"].values():
        path = Path(value)
        assert not path.is_absolute()
        assert "\\" not in value


def test_example_config_has_required_runtime_paths():
    settings = json.loads(CONFIG.read_text(encoding="utf-8"))
    required = {
        "inbox_new",
        "inbox_pending_analysis",
        "inbox_pending_confirm",
        "inbox_rejected",
        "source_batch",
        "assets_raw",
        "assets_reviewed",
        "assets_archive",
        "design_archive",
        "logs",
        "database",
    }

    assert required.issubset(settings["paths"])
