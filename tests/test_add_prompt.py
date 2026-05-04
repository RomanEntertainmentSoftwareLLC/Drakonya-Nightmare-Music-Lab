from pathlib import Path

from app.tools.add_prompt import add_prompt
from app.tools.create_batch import create_batch


def test_add_prompt_appends_to_batch_prompt_file(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Prototype Music Batch 001", genre="TBD")

    prompt_file = add_prompt(
        "Prototype Music Batch 001",
        title="Test Track 01",
        genre="undecided",
        prompt="Dark cinematic synth pulse with haunting vocal hooks.",
    )

    assert prompt_file == batch_dir / "prompts" / "suno_prompts.md"

    text = prompt_file.read_text(encoding="utf-8")
    assert "## Test Track 01" in text
    assert "Genre: undecided" in text
    assert "Dark cinematic synth pulse with haunting vocal hooks." in text
