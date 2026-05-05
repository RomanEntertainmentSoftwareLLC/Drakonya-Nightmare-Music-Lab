# Cover Art Pipeline

Drakonya Nightmare Music Lab supports album cover art as a first-class release asset.

The cover system is provider-agnostic.

It may start with manual cover creation, then later support AI image providers or local image models.

## Core Rule

Do not generate art automatically unless the operator explicitly requests it.

The first implementation creates cover requests, prompts, folders, manifests, and QA fields only.

## Cover Package Structure

Each release package may contain:

    cover_art/
      cover_manifest.json
      prompts/
        cover_prompt.md
      variants/
      approved/
      logo/

## Visual Lane Rule

Cover art must match the selected release lane.

Examples:

- sleep ambient should look calm, soft, and peaceful
- coding focus should look clean, techy, or atmospheric
- kids music should look colorful and friendly
- tropical music should look warm and bright
- gym/phonk should look intense and energetic
- dark gothic should look dark only when that lane is selected

Do not force gothic, horror, vampire, or nightmare imagery onto every release.

## Logo Reuse Rule

If an artist/project has an approved reusable logo, the cover workflow should reference that logo.

Do not invent a new fake logo per album.

Approved logos live under:

    data/brands/<brand_slug>/logo/approved/

Release cover workflows can reference approved logos through:

    release_manifest.json
    cover_art/cover_manifest.json

## Manual First

The first workflow is:

1. Create release package
2. Create optional brand/logo package
3. Create cover request
4. Generate or design cover manually outside the tool
5. Place variants into cover_art/variants/
6. Operator chooses approved cover
7. Later tool marks cover_ready

## Future Provider Layer

Future providers may include:

- manual_cover
- openai_image
- local_image
- future_provider

Provider selection must remain replaceable.
