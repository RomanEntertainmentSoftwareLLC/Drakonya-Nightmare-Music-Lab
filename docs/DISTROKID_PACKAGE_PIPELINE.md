# DistroKid and YouTube Package Pipeline

Drakonya Nightmare Music Lab prepares releases before any distributor upload.

The goal is to package legitimate releases at a controlled cadence, not spam uploads.

## Current Cadence

- one DistroKid account for now
- one to two albums per week maximum
- no mass-upload bursts
- no artificial streaming
- no fake engagement
- no impersonation
- no misleading credits

## Package Readiness

A release package is ready for DistroKid and YouTube prep only when these gates are true:

    audio_ready
    cover_ready
    metadata_ready

The tool then prepares:

    data/releases/<release_id>/distrokid/upload_sheet.md
    data/releases/<release_id>/youtube/youtube_package.md
    data/releases/<release_id>/logs/package_prepare_log.json

And flips:

    distrokid_ready = true
    youtube_ready = true

## Automation Rule

The current package tool does not upload anything.

Future DistroKid browser automation should use the prepared upload sheet and release manifest, then fill forms at a human-reasonable cadence.

Final submit must remain gated by config until the form-fill sidecar is stable and account-safe.
