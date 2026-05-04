from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from app.core.paths import project_root


def safe_slug(value: str) -> str:
    cleaned = []
    for char in value.lower().strip():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "untitled"


def make_batch_id(name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"BATCH-{stamp}-{safe_slug(name)}"


def create_batch(name: str, genre: str | None = None, notes: str | None = None) -> Path:
    batch_id = make_batch_id(name)
    batch_dir = project_root() / "data" / "batches" / batch_id

    folders = [
        batch_dir,
        batch_dir / "prompts",
        batch_dir / "jobs",
        batch_dir / "tracks",
        batch_dir / "winners",
        batch_dir / "slop",
        batch_dir / "covers",
        batch_dir / "videos",
        batch_dir / "release_package",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    readme = batch_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# {batch_id}",
                "",
                f"Name: {name}",
                f"Genre: {genre or ''}",
                "",
                "## Notes",
                "",
                notes or "",
                "",
                "## Workflow",
                "",
                "1. Add Suno prompts to prompts/",
                "2. Generate tracks",
                "3. Store generated audio in tracks/",
                "4. Move approved tracks to winners/",
                "5. Move rejected tracks to slop/",
                "6. Put cover/video assets in covers/ and videos/",
                "7. Put final metadata in release_package/",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (batch_dir / "prompts" / "suno_prompts.md").write_text(
        f"# Suno Prompts for {batch_id}\n\n",
        encoding="utf-8",
    )

    return batch_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Drakonya production batch folder.")
    parser.add_argument("name", help="Batch name, e.g. 'Dark Miami Synthwave Test'")
    parser.add_argument("--genre", default=None, help="Target genre")
    parser.add_argument("--notes", default=None, help="Optional notes")
    args = parser.parse_args()

    batch_dir = create_batch(args.name, genre=args.genre, notes=args.notes)
    print(f"Created batch: {batch_dir}")


if __name__ == "__main__":
    main()
