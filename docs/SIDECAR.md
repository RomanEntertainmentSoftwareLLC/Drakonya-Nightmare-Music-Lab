# Suno Sidecar

The Suno sidecar is a separate local service that will eventually control the Suno generation workflow.

## Architecture

Ubuntu Drakonya API
    -> Suno sidecar
    -> dedicated Suno browser/session
    -> generated audio files
    -> Drakonya job variants A/B

## Why Separate?

The main Drakonya API should stay clean and platform-neutral.

The sidecar handles Suno-specific browser/session behavior.

## Planned Flow

1. Drakonya creates a generation job.
2. Drakonya calls sidecar POST /suno/generate.
3. Sidecar submits prompt to Suno.
4. Suno generates two versions.
5. Sidecar downloads both.
6. Drakonya attaches version A and version B to the generation job.
7. Audio Curator selects winner.
8. Loser moves to slop_bin.

## Guardrails

- No password committed.
- No cookies committed.
- No tokens committed.
- No captcha bypass.
- No stealth evasion.
- Stop if Suno asks for login/security verification.
- Hard generation caps before live use.
