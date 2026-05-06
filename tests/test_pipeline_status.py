from app.core.jobs import attach_variant_audio, create_generation_job
from app.tools.pipeline_status import pipeline_status


def test_pipeline_status_prints_next_action_for_downloaded_job(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"A")
    b.write_bytes(b"B")

    job = create_generation_job(
        prompt="cyberpunk dubstep",
        batch_id="BATCH-TEST",
        title="Cyberbreaker",
        genre="dubstep",
        provider="suno_private",
    )
    attach_variant_audio(job.job_id, "A", a)
    attach_variant_audio(job.job_id, "B", b)

    assert pipeline_status() == 0
    output = capsys.readouterr().out

    assert "Drakonya Pipeline Status" in output
    assert "downloaded" in output
    assert "select-winner" in output
    assert job.job_id in output
