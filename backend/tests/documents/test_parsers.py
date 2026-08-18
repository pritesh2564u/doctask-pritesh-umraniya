from pathlib import Path

from app.documents.registry import create_default_registry


def test_txt_parser(tmp_path: Path):
    file_path = tmp_path / "example.txt"

    file_path.write_text(
        "Project Alpha\n"
        "API integration is delayed.\n",
        encoding="utf-8",
    )

    registry = create_default_registry()
    parser = registry.get_parser(file_path)

    document = parser.parse(file_path)

    assert document.filename == "example.txt"
    assert len(document.blocks) == 2
    assert document.blocks[0].text == "Project Alpha"
    assert document.blocks[1].location.line == 2