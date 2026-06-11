from pathlib import Path

from automation.scripts import design_knowledge_engine as engine


def test_markdown_content_generates_card_fields():
    image_path = engine.ROOT / "sample_output/inbox/03_pending_confirm/garden_dress.png"
    record = {
        "id": "test-image-id",
        "status": "pending_confirm",
        "tags": ["Garden", "Floral", "Pastel"],
        "analysis": {
            "design_language": "Soft garden reference.",
            "silhouette": "A-line.",
            "color": "Cream, pink, sage.",
            "knowledge_value": "Useful for visual research.",
        },
        "original_filename": "garden_dress.png",
        "sha256": "abc123",
        "analysis_result_path": "",
    }

    content = engine.markdown_content(record, image_path, category="04_review")

    assert "# garden_dress" in content
    assert "Garden, Floral, Pastel" in content
    assert "Soft garden reference." in content
    assert "sample_output/inbox/03_pending_confirm/garden_dress.png" in content
    assert "test-image-id" in content


def test_sample_demo_markdown_exists():
    demo = Path("sample_output/garden_dress.md")

    assert demo.exists()
    assert "Garden Dress" in demo.read_text(encoding="utf-8")
