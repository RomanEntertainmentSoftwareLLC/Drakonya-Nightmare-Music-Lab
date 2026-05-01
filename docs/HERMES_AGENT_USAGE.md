# Hermes Agent Usage

This project uses Hermes directly.

Hermes does not currently use OpenClaw-style named-agent flags such as:

    hermes chat --agent market_scout

Instead, Drakonya agents are defined in:

    AGENTS.md

To talk to a specific agent later, run Hermes from the project root and name the role in the prompt.

Examples:

    cd /opt/drakonya-nightmare-music-lab

    hermes chat

Then ask:

    Use the Song Architect role from AGENTS.md. Create 10 Suno prompts for melodic vampire dubstep.

For one-shot mode later:

    hermes -z "Use the Market Scout role from AGENTS.md. Find 10 high-potential niches for gothic AI music."

## Current Safety Rule

Do not run Hermes yet.

This project is wired for future LLM use, but agent automation remains disabled until cost controls and logging are added.
