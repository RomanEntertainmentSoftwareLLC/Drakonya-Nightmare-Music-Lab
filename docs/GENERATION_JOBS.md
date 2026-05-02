# Generation Jobs

Drakonya generation jobs represent one prompt that should produce two Suno versions.

## Flow

1. Create job with prompt.
2. Provider generates two versions.
3. Both versions are downloaded.
4. Audio Curator selects the better version.
5. Winner is marked APPROVED.
6. Loser is moved to slop_bin.

## API

POST /jobs/generate

GET /jobs

GET /jobs/{job_id}

POST /jobs/{job_id}/select-winner

## Rule

Every generated prompt should create a job so Drakonya can track which version won and which version became Electro Slop.
