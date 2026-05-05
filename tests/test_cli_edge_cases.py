from app.core.paths import data_dir
from app.tools.cli_errors import reject_placeholder_job_id
from app.tools.jobs_status import jobs_status


def test_placeholder_job_id_gets_friendly_error():
    try:
        reject_placeholder_job_id("JOB-ID")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit")


def test_duplicate_batch_error_suggests_exact_batch_id(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batches = data_dir() / "batches"
    first = batches / "BATCH-20260505-111111-single-song-cyberbreaker"
    second = batches / "BATCH-20260505-222222-single-song-cyberbreaker"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    try:
        jobs_status("single-song-cyberbreaker")
    except SystemExit as exc:
        message = str(exc)
        assert "Multiple batches matched" in message
        assert "Use the exact batch folder name" in message
        assert "python3 -m app.tools.jobs_status --batch" in message
    else:
        raise AssertionError("Expected SystemExit")
