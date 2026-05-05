# Album Build Pipeline

Drakonya Nightmare Music Lab builds albums/releases from approved winner tracks.

The goal is:

1. Generate A/B candidate tracks
2. Attach downloaded audio to jobs
3. Manually select winners
4. Build an album/release package from selected winners
5. Copy approved winner audio into release/audio/
6. Generate tracklist and credits
7. Update DistroKid and YouTube package notes
8. Mark release audio and metadata gates ready

## Manual First

The first implementation uses operator-approved winners.

AI audio judging comes later.

## Source

Winner tracks come from selected generation jobs:

    data/jobs/<job_id>.json

A job counts as album-ready when:

- status is selected
- winner_variant_id is set
- the winner variant has an existing audio_path

## Destination

Album tracks are copied into:

    data/releases/<release_id>/audio/

Metadata is updated under:

    data/releases/<release_id>/metadata/

DistroKid notes are updated under:

    data/releases/<release_id>/distrokid/

YouTube notes are updated under:

    data/releases/<release_id>/youtube/

## Readiness Gates

When at least one winner track is copied, the release manifest sets:

    audio_ready = true
    metadata_ready = true

Cover, DistroKid, and YouTube readiness remain separate gates.
