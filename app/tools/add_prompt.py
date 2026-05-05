from __future__ import annotations

import argparse
from pathlib import Path

from app.tools.batch_status import find_batch


PROMPT_RELATIVE_PATH = Path("prompts") / "suno_prompts.md"


def add_prompt(
    batch_id: str,
    *,
    title: str,
    genre: str | None,
    prompt: str,
    instrumental: bool = False,
) -> Path:
    batch_dir = find_batch(batch_id)
    prompt_file = batch_dir / PROMPT_RELATIVE_PATH
    prompt_file.parent.mkdir(parents=True, exist_ok=True)

    if not prompt_file.exists():
        prompt_file.write_text(f"# Suno Prompts for {batch_dir.name}\n\n", encoding="utf-8")

    existing = prompt_file.read_text(encoding="utf-8")
    prefix = "" if existing.endswith("\n") else "\n"

    entry = "\n".join(
        [
            f"## {title.strip()}",
            "",
            f"Genre: {(genre or '').strip()}",
            f"Instrumental: {str(instrumental).lower()}",
            "",
            "Prompt:",
            "",
            prompt.strip(),
            "",
        ]
    )

    prompt_file.write_text(existing + prefix + entry, encoding="utf-8")
    return prompt_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a Suno prompt to a Drakonya batch prompt pack.")
    parser.add_argument("batch_id", help="Full or partial batch id/name")
    parser.add_argument("--title", required=True, help="Track title")
    parser.add_argument("--genre", default=None, help="Prompt genre/style bucket")
    parser.add_argument("--prompt", required=True, help="Full Suno prompt text")
    parser.add_argument("--instrumental", action="store_true", help="Mark this prompt as instrumental")
    args = parser.parse_args()

    prompt_file = add_prompt(
        args.batch_id,
        title=args.title,
        genre=args.genre,
        prompt=args.prompt,
        instrumental=args.instrumental,
    )
    print(f"Added prompt to: {prompt_file}")


if __name__ == "__main__":
    main()
