from pathlib import Path

from app.core.jobs import (
    attach_variant_audio,
    create_generation_job,
    load_job,
    select_winner,
)


def test_create_generation_job():
    job = create_generation_job(
        prompt="dark vampire techno",
        batch_id="BATCH-TEST",
        title="Test Song",
        genre="gothic techno",
    )

    loaded = load_job(job.job_id)

    assert loaded.job_id == job.job_id
    assert loaded.batch_id == "BATCH-TEST"
    assert len(loaded.variants) == 2
    assert loaded.variants[0].variant_id == "A"
    assert loaded.variants[1].variant_id == "B"


def test_attach_variants_and_select_winner(tmp_path: Path):
    job = create_generation_job(
        prompt="dark vampire techno",
        batch_id="BATCH-TEST",
        title="Test Song",
    )

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"fake a")
    b.write_bytes(b"fake b")

    attach_variant_audio(job.job_id, "A", a)
    updated = attach_variant_audio(job.job_id, "B", b)

    assert updated.status == "downloaded"

    selected = select_winner(job.job_id, "A", "A has better hook.")

    assert selected.status == "selected"
    assert selected.winner_variant_id == "A"

    variant_a = next(v for v in selected.variants if v.variant_id == "A")
    variant_b = next(v for v in selected.variants if v.variant_id == "B")

    assert variant_a.status == "APPROVED"
    assert variant_b.status == "SLOP_BIN"
