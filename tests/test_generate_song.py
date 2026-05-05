from app.core.jobs import load_job
from app.tools.generate_song import generate_song


def test_generate_song_creates_batch_prompt_job_and_submits_manual(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    job_id = generate_song(
        "brutal dubstep with a cyberpunk vibe",
        title="Cyberbreaker",
        genre="dubstep",
        provider="manual_suno",
        instrumental=True,
    )

    job = load_job(job_id)
    assert job.title == "Cyberbreaker"
    assert job.genre == "dubstep"
    assert job.instrumental is True
    assert job.provider == "manual_suno"
    assert job.provider_task_id
    assert job.status == "generated"


def test_generate_song_existing_batch(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    first = generate_song(
        "soft rain coding focus music",
        title="Rain Code",
        genre="coding focus",
    )
    first_job = load_job(first)

    second = generate_song(
        "gentle sleep ambient clouds",
        title="Sleep Cloud",
        genre="sleep ambient",
        batch=first_job.batch_id,
    )
    second_job = load_job(second)

    assert first_job.batch_id == second_job.batch_id
    assert second_job.title == "Sleep Cloud"
