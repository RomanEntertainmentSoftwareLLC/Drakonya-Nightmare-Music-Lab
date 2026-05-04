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

## Current Browser Milestone

The first live browser endpoint is intentionally tiny:

    POST /suno/open

It only opens Suno in a dedicated local browser profile. It does not generate, download, bypass login, bypass CAPTCHA, or use stealth behavior.

The sidecar looks for a browser in this order:

    SUNO_BROWSER_BIN
    google-chrome
    chromium
    chromium-browser
    firefox

Default local paths:

    profile:  state/suno_browser_profile
    downloads: data/inbox/suno_downloads

These paths are local runtime state and should not be committed except for `.gitkeep` placeholders.

## Planned Flow

1. Drakonya creates a generation job.
2. Drakonya calls sidecar POST /suno/open if the browser is not already open.
3. User logs into Suno manually if needed.
4. Drakonya calls sidecar POST /suno/generate.
5. Sidecar submits prompt to Suno.
6. Suno generates two versions.
7. Sidecar downloads both.
8. Drakonya attaches version A and version B to the generation job.
9. Audio Curator selects winner.
10. Loser moves to slop_bin.

## Guardrails

- No password committed.
- No cookies committed.
- No tokens committed.
- No captcha bypass.
- No stealth evasion.
- Stop if Suno asks for login/security verification.
- Hard generation caps before live use.
