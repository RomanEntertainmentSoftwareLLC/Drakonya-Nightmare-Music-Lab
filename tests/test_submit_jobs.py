from app.core.jobs import JOB_STATUS_CREATED, JOB_STATUS_GENERATED, load_job
from app.tools.add_prompt import add_prompt
from app.tools.create_batch import create_batch
from app.tools.create_jobs_from_prompts import create_jobs_from_prompts
from app.tools.submit_batch_jobs import submit_batch_jobs
from app.tools.submit_job import submit_job


def test_submit_job_to_manual_provider_updates_provider_task(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    create_batch("Prototype Music Batch 001", genre="coding focus")
    add_prompt(
        "Prototype Music Batch 001",
        title="Code Rain Drive",
        genre="coding focus",
        prompt="Instrumental coding focus track with rain and soft synths.",
    )
    created = create_jobs_from_prompts("Prototype Music Batch 001")

    job = load_job(created[0])
    assert job.status == JOB_STATUS_CREATED

    updated = submit_job(job.job_id)

    assert updated.status == JOB_STATUS_GENERATED
    assert updated.provider == "manual_suno"
    assert updated.provider_task_id.startswith("manual-")
    assert updated.notes


def test_submit_batch_jobs_submits_only_created_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    monkeypatch.delenv("SUNO_PROVIDER", raising=False)

    create_batch("Prototype Music Batch 001", genre="TBD")
    add_prompt(
        "Prototype Music Batch 001",
        title="Code Rain Drive",
        genre="coding focus",
        prompt="Instrumental coding focus track with rain and soft synths.",
    )
    add_prompt(
        "Prototype Music Batch 001",
        title="Sleep Cloud",
        genre="sleep ambient",
        prompt="Peaceful sleep ambient track with soft pads.",
    )
    created = create_jobs_from_prompts("Prototype Music Batch 001")

    submitted = submit_batch_jobs("Prototype Music Batch 001", limit=1)
    assert len(submitted) == 1

    first = load_job(submitted[0])
    assert first.status == JOB_STATUS_GENERATED

    remaining_created = [job_id for job_id in created if load_job(job_id).status == JOB_STATUS_CREATED]
    assert len(remaining_created) == 1

    submitted_again = submit_batch_jobs("Prototype Music Batch 001")
    assert len(submitted_again) == 1
    assert load_job(submitted_again[0]).status == JOB_STATUS_GENERATED

    submitted_final = submit_batch_jobs("Prototype Music Batch 001")
    assert submitted_final == []
