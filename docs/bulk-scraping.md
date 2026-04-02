# Bulk Scraping Workflow

## Goal

Run the existing lyric collection flow for multiple artists from one registry file instead of repeating single-artist commands by hand.

The batch path keeps the same safe order:

1. discover a primary discography manifest
2. scrape the primary lyric source
3. fetch Spotify metadata
4. backfill lyric-bearing gaps from a secondary source
5. apply any manual backfill manifest
6. write final merged coverage reports

## Registry

Start from:

- `lyrics/bulk/artist_registry.template.json`

Schema:

- `schemas/bulk_artist_registry.schema.json`

The registry paths are resolved relative to the project root, not relative to the registry file itself.

## Command

```powershell
python bulk_scrape_artists.py `
  --registry lyrics/bulk/artist_registry.template.json `
  --project-root . `
  --overwrite
```

Run only selected artists:

```powershell
python bulk_scrape_artists.py `
  --registry lyrics/bulk/artist_registry.template.json `
  --project-root . `
  --artists ado `
  --overwrite
```

## Practical Notes

- `request_delay_seconds` slows down per-page requests for safer large runs.
- `artist_delay_seconds` pauses between artists.
- The batch script still respects `robots.txt` because the underlying scraper does.
- The final report still separates `Primary Works Missing From Lyrics` from `Variant-Only Gaps`.
- For artists with known missing originals, keep a dedicated `manual_backfill_manifest` in the registry.

## Verified State

On March 12, 2026, the batch path was re-run for `Ado` from the registry template and finished with:

- strict coverage `72 / 82`
- lyric-bearing works coverage `72 / 72`

That confirms the batch collector reproduces the single-artist flow correctly.
