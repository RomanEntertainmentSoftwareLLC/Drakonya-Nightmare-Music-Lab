import json

from app.core.jobs import list_jobs
from app.tools.add_prompt import add_prompt
from app.tools.create_batch import create_batch
from app.tools.create_jobs_from_prompts import create_jobs_from_prompts, parse_prompt_pack
from app.tools.jobs_status import jobs_status


def test_parse_prompt_pack_reads_add_prompt_format(tmp_path):
    prompt_file = tmp_path / "suno_prompts.md"
    prompt_file.write_text(
        "\n".join(
            [
                "# Suno Prompts",
                "",
                "## Code Rain Drive",
                "",
                "Genre: coding focus",
                "",
                "Prompt:",
                "",
                "Instrumental coding focus track with rain and soft synths.",
                "",
                "## Sleep Cloud",
                "",
                "Genre: sleep ambient",
                "",
                "Prompt:",
                "",
                "Peaceful sleep ambient track with soft pads.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    entries = parse_prompt_pack(prompt_file)

    assert len(entries) == 2
    assert entries[0]["title"] == "Code Rain Drive"
    assert entries[0]["genre"] == "coding focus"
    assert "rain" in entries[0]["prompt"]
    assert entries[1]["title"] == "Sleep Cloud"


def test_create_jobs_from_prompts_creates_jobs_and_index(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    batch_dir = create_batch("Prototype Music Batch 001", genre="TBD")
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

    created = create_jobs_from_prompts("Prototype Music Batch 001", provider="manual_suno")

    assert len(created) == 2
    jobs = list_jobs()
    assert len(jobs) == 2
    assert {job.title for job in jobs} == {"Code Rain Drive", "Sleep Cloud"}
    assert {job.batch_id for job in jobs} == {batch_dir.name}
    assert all(job.provider == "manual_suno" for job in jobs)

    index_path = batch_dir / "jobs" / "generation_jobs.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["batch_id"] == batch_dir.name
    assert index["total_prompt_entries"] == 2
    assert len(index["created_job_ids"]) == 2


def test_create_jobs_from_prompts_skips_duplicates_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    create_batch("Prototype Music Batch 001", genre="TBD")
    add_prompt(
        "Prototype Music Batch 001",
        title="Code Rain Drive",
        genre="coding focus",
        prompt="Instrumental coding focus track with rain and soft synths.",
    )

    first = create_jobs_from_prompts("Prototype Music Batch 001")
    second = create_jobs_from_prompts("Prototype Music Batch 001")

    assert len(first) == 1
    assert second == []
    assert len(list_jobs()) == 1


def test_jobs_status_filters_by_batch(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))

    create_batch("Prototype Music Batch 001", genre="TBD")
    add_prompt(
        "Prototype Music Batch 001",
        title="Code Rain Drive",
        genre="coding focus",
        prompt="Instrumental coding focus track with rain and soft synths.",
    )
    create_jobs_from_prompts("Prototype Music Batch 001")

    assert jobs_status("Prototype Music Batch 001") == 0
    output = capsys.readouterr().out
    assert "Jobs: 1" in output
    assert "created: 1" in output
    assert "Code Rain Drive" in output
