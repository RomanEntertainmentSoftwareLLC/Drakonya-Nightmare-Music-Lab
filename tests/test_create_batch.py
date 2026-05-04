from app.tools.create_batch import create_batch


def test_create_batch_creates_expected_folders(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch(
        "Test Genre Batch",
        genre="anything",
        notes="test notes",
    )

    assert batch_dir.exists()
    assert (batch_dir / "README.md").exists()
    assert (batch_dir / "prompts" / "suno_prompts.md").exists()

    for folder in [
        "prompts",
        "jobs",
        "tracks",
        "winners",
        "slop",
        "covers",
        "videos",
        "release_package",
    ]:
        assert (batch_dir / folder).exists()
