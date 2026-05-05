# Brand and Logo Pipeline

Drakonya Nightmare Music Lab supports reusable artist, band, and project identities.

A logo is not a one-off album image. A logo is a stable brand asset.

The goal is:

1. Create an artist/project brand profile
2. Generate or import logo concepts
3. Let the operator approve one logo
4. Lock the approved logo as the reusable identity asset
5. Reuse that approved logo across album covers, YouTube thumbnails, avatars, and release packages
6. Regenerate only when the operator explicitly requests a rebrand

## Brand Folder Structure

Each artist or project lives under:

    data/brands/<brand_slug>/

Expected folders:

    logo/concepts/
    logo/approved/
    logo/exports/
    cover_overlays/
    references/

Expected files:

    brand_profile.json
    style_guide.md
    logo_prompt.md

## Logo Doctrine

The artwork agent must not invent a new fake logo for every album.

If `approved_logo_path` exists in the brand profile, album-cover workflows should use it unless the operator says otherwise.

The system may generate album-specific covers, but the artist/project logo should remain stable across releases.

## Genre Rule

A logo can match the artist/project identity, but the system is still genre-agnostic.

Do not force gothic, vampire, horror, or nightmare aesthetics unless the selected artist/project identity calls for it.

## Human Approval Rule

Logo locking is manual first.

The operator chooses the approved logo.

Later, AI visual QA may check logo consistency, readability, scalability, and whether the logo fits the selected brand lane.
