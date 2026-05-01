# LLM Safety

Drakonya Nightmare Music Lab is wired for future LLM/Hermes use, but automation is disabled by default.

## Default Rule

No paid LLM calls should run unless all of these are true:

- OPENAI_ENABLED=true
- DRAKONYA_AGENT_AUTOMATION=true
- OPENAI_API_KEY is present locally
- budget limits are configured

## Local-Only Secret File

Real API keys belong only in:

.env

The .env file must never be committed.

## Current Defaults

OPENAI_ENABLED=false
HERMES_ENABLED=false
DRAKONYA_AGENT_AUTOMATION=false
DRAKONYA_MAX_DAILY_LLM_USD=1.00
DRAKONYA_MAX_RUN_LLM_USD=0.10

## Project Rule

Build local-first. Do not test Hermes or OpenAI until cost logging and hard budget gates exist.
