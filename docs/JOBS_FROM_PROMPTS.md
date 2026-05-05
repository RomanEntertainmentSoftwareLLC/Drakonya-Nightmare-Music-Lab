# Jobs From Prompts Pipeline

Drakonya Nightmare Music Lab converts batch prompt packs into generation jobs.

The goal is:

1. Create or choose a batch
2. Add Suno prompts into prompts/suno_prompts.md
3. Convert each prompt entry into a generation job
4. Submit jobs to the selected provider later
5. Attach A/B audio versions after downloads exist
6. Select winners manually first

## Prompt Pack Format

The prompt writer creates entries shaped like this:

    ## Track Title

    Genre: coding focus

    Prompt:

    Full prompt text here.

The job builder parses those entries and creates one job per prompt.

## Duplicate Rule

By default, the job builder skips jobs that already exist for the same batch and title.

Use --allow-duplicates only when intentionally creating another job for the same title.

## Manual First

This tool does not submit anything to Suno.

It only creates local job records so the system has a clean queue.
