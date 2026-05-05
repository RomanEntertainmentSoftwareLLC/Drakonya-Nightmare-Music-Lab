# Suno Download Bridge

This stage connects generated Suno downloads back into Drakonya jobs.

The current bridge is intentionally browser/manual-assist first:

1. Submit a local generation job to the private Suno provider.
2. The sidecar stages the prompt and tries to copy it to the clipboard.
3. The operator uses the dedicated Suno browser profile to generate the song.
4. Download the two Suno versions into:

       data/inbox/suno_downloads/

5. Fetch provider downloads for the job.
6. The tool attaches version A and version B to the Drakonya generation job.
7. The operator listens and selects the winner.

## Submit One Private Job

Start sidecar:

    python3 -m uvicorn sidecar.suno_sidecar:app --host 127.0.0.1 --port 8766

Open Suno profile:

    curl -X POST http://127.0.0.1:8766/suno/open -H "Content-Type: application/json" -d '{}'

Submit one local job to sidecar:

    SUNO_PROVIDER=suno_private SUNO_PRIVATE_ENABLED=true python3 -m app.tools.submit_batch_jobs "Prototype Music Batch 001" --limit 1

The sidecar returns a provider task id shaped like:

    SUNO-YYYYMMDD-HHMMSS-xxxxxxxx

## Download Inbox

Place downloaded Suno audio files into:

    data/inbox/suno_downloads/

The sidecar maps the first two matching/recent audio files to:

    version A
    version B

Supported audio extensions:

    mp3, wav, m4a, flac, aac, ogg

## Attach Downloads to Job

Once the files are downloaded:

    python3 -m app.tools.fetch_provider_downloads JOB-ID --provider suno_private --enable-private

Then check:

    python3 -m app.tools.jobs_status --batch "Prototype Music Batch 001"

## Safety

No password in repo.
No cookies in chat.
No CAPTCHA bypass.
No stealth behavior.
No high-volume burst generation.

This bridge stages and imports. Full browser-click automation comes later only after the manual prompt workflow is proven.
