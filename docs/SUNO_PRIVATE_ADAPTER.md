# Suno Private Adapter

Drakonya Nightmare Music Lab will use a provider abstraction for music generation.

## Provider Options

- manual
- suno_private

## Current Default

SUNO_PROVIDER=manual

## Private Adapter Goal

The future `suno_private` provider will connect Drakonya to the user's own Suno account through a controlled local tool layer.

The AI agents will not log into Suno directly. They will call Drakonya functions such as:

- generate track
- check generation status
- download generated audio
- import generated track

## Guardrails

- No password committed to the repository.
- No cookies, tokens, or authorization headers committed.
- No captcha bypass.
- No stealth or anti-detection behavior.
- Stop if Suno shows login, security, or error screens.
- Hard batch and daily generation caps.
- Log every generation attempt.

## Planned Flow

Drakonya batch prompt
    -> provider.generate()
    -> Suno private sidecar
    -> generated track
    -> provider.download()
    -> data/tracks
    -> catalog / QA / release workflow
