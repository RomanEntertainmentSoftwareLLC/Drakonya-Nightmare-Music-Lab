from app.core.jobs import attach_variant_audio, create_generation_job, load_job
from app.tools.select_job_winner import select_job_winner


def test_select_job_winner_marks_winner_and_copies_loser_to_slop(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"A")
    b.write_bytes(b"B")

    job = create_generation_job(
        prompt="test prompt",
        batch_id="BATCH-TEST",
        title="Test Track",
    )
    attach_variant_audio(job.job_id, "A", a)
    attach_variant_audio(job.job_id, "B", b)

    updated = select_job_winner(job.job_id, "A", notes="A wins")

    assert updated.status == "selected"
    assert updated.winner_variant_id == "A"

    loaded = load_job(job.job_id)
    assert loaded.winner_variant_id == "A"
    assert loaded.notes == "A wins"

    slop_files = list((tmp_path / "data" / "slop_bin").rglob("*.mp3"))
    assert len(slop_files) == 1
    assert slop_files[0].read_bytes() == b"B"


def test_select_job_winner_rejects_missing_audio(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    job = create_generation_job(
        prompt="test prompt",
        batch_id="BATCH-TEST",
        title="Test Track",
    )

    try:
        select_job_winner(job.job_id, "A")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit")
