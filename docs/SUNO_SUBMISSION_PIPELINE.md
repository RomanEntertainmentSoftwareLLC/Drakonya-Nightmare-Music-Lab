# Suno Submission Pipeline

Drakonya Nightmare Music Lab now separates prompt/job preparation from provider submission.

The intended path is:

1. Add prompts to a batch
2. Convert prompt pack entries into generation jobs
3. Submit created jobs to the configured provider
4. Later, the Suno sidecar handles live browser submission
5. Downloaded A/B tracks attach back to the job
6. Operator selects the winner

## Submit One Job

    python3 -m app.tools.submit_job JOB-ID

Provider override:

    python3 -m app.tools.submit_job JOB-ID --provider manual_suno

Future private sidecar mode:

    SUNO_PROVIDER=suno_private SUNO_PRIVATE_ENABLED=true python3 -m app.tools.submit_job JOB-ID

## Submit Batch Jobs

    python3 -m app.tools.submit_batch_jobs "Prototype Music Batch 001"

Submit only one job for a careful test:

    python3 -m app.tools.submit_batch_jobs "Prototype Music Batch 001" --limit 1

## Safety Rule

The default provider remains manual_suno.

The private Suno browser sidecar must be explicitly enabled with environment variables before use.

No password belongs in the repo.
No cookies belong in chat.
No CAPTCHA bypass.
No stealth behavior.
No high-volume burst submissions.
