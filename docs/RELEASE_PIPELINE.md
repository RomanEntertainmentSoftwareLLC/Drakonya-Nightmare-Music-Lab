# Drakonya Release Pipeline

Drakonya Nightmare Music Lab builds releases like a small AI-assisted music label.

The goal is not random song generation. The goal is a repeatable pipeline:

1. Research a marketable niche
2. Create a batch
3. Generate candidate tracks
4. Select winners
5. Build an album/release package
6. Add cover art and reusable artist/project logo assets
7. Prepare DistroKid metadata
8. Prepare YouTube metadata
9. Publish at a controlled cadence
10. Track results and double down on what works

## Release Cadence

Current operating target:

- one DistroKid account
- one to two albums per week maximum
- no mass-upload bursts
- no fake engagement
- no artificial streaming
- no impersonation
- no misleading credits

Automation must protect the account.

## Release Package Structure

Each album/release package lives under:

    data/releases/<release_id>/

Expected folders:

    audio/
    cover_art/
    metadata/
    distrokid/
    youtube/
    logs/

Expected key files:

    release_manifest.json
    README.md
    metadata/tracklist.md
    metadata/credits.md
    distrokid/upload_sheet.md
    youtube/youtube_package.md

## Cover Art and Logo Rule

Cover art must match the selected release lane.

Do not force gothic, horror, vampire, or nightmare aesthetics unless that lane is selected.

If an artist/project has an approved reusable logo, use that logo across releases instead of inventing a new logo every time.

## DistroKid Rule

The Publisher Analyst prepares DistroKid-ready metadata and upload sheets.

Later automation may use a DistroKid browser sidecar, but it must be paced, logged, and account-safe.

## Album Readiness Gates

A release is not ready until these gates are true:

- audio_ready
- cover_ready
- metadata_ready
- distrokid_ready
- youtube_ready

The first implementation starts as draft-only. Final publish automation comes later.
