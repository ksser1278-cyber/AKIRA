# Web Scraping Workflow

## Goal

Collect lyric pages from user-supplied URLs, save them as raw `.txt` files, generate a standard ingest manifest, and then feed the existing normalization and analysis pipeline.

## Why This Structure

The project still needs a stable ingest layer.  
So the web step is not a separate dead-end crawler. It writes into:

- `lyrics/raw/<artist_id>/`
- `lyrics/manifests/<artist_id>_manifest.json`

That means scraped pages and manually imported files share the same downstream path.

## Input

Prepare a web scrape manifest like:

```json
{
  "schema_version": "1.0",
  "artist_id": "ado",
  "artist_name": "Ado",
  "language": "ja",
  "source_type": "web_scrape",
  "collection_method": "Web scrape from user-supplied lyric URLs.",
  "raw_output_dir": "../raw/ado",
  "manifest_output_path": "../manifests/ado_manifest.json",
  "respect_robots_txt": true,
  "sources": [
    {
      "url": "https://example.com/lyrics-page",
      "track_id": "song_slug",
      "title": "Song Title",
      "extraction_mode": "auto",
      "selector": "div.lyrics"
    }
  ]
}
```

Template files:

- `lyrics/web/_template/web_manifest.template.json`
- `lyrics/web/ado_sources.template.json`

## Extraction Modes

- `auto`: selector if provided, then JSON-LD, then heuristic block search
- `selector`: use only the provided selector or selectors
- `json_ld`: use `lyrics` fields found in structured data
- `heuristic`: search likely lyric containers by class/id/text shape

## Built-In Site Presets

These domains are auto-detected even when `selector` is omitted:

- `uta-net.com` -> prefers `#kashi-area`
- `utaten.com` -> prefers the hiragana lyric body and removes furigana readings
- `petitlyrics.com` -> pulls the largest lyric block from `table#lyrics_list`

Live check on March 12, 2026:

- `utaten.com` preset worked
- `petitlyrics.com` preset worked
- `uta-net.com` is still useful as a reference source, but the current scraper stops if `robots.txt` blocks the page

You can also set `site_preset` explicitly to:

- `uta_net`
- `utaten`
- `petitlyrics`

## Commands

Scrape only:

```powershell
python scrape_web_lyrics.py `
  --web-manifest lyrics/web/ado_sources.template.json `
  --overwrite
```

Discover a full artist discography manifest first:

```powershell
python discover_discography.py `
  --artist-id ado `
  --artist-name Ado `
  --site utaten `
  --artist-url https://utaten.com/artist/lyric/39156
```

That writes a ready-to-run web manifest like:

- `lyrics/web/ado_discography.utaten.json`

Then scrape the full discovered discography:

```powershell
python scrape_web_lyrics.py `
  --web-manifest lyrics/web/ado_discography.utaten.json `
  --overwrite
```

Fetch Spotify discography metadata to check scrape coverage:

```powershell
python fetch_spotify_discography.py `
  --artist-name Ado

python compare_discography_coverage.py `
  --lyrics-manifest lyrics/manifests/ado_manifest.json `
  --spotify-discography data/spotify/ado_discography.json
```

If Spotify still shows lyric-bearing originals that are absent from the scraped manifest, add those URLs to a manual backfill manifest and rescrape them:

```powershell
python scrape_web_lyrics.py `
  --web-manifest lyrics/web/ado_manual_backfill.utaten.json
```

Current Ado practical flow on March 12, 2026:

- start with `lyrics/web/ado_discography.utaten.json`
- backfill Spotify gaps with `lyrics/web/ado_spotify_backfill.petitlyrics.json`
- add any remaining lyric-bearing originals to `lyrics/web/ado_manual_backfill.utaten.json`
- use `reports/discography/ado_coverage.merged.md` to confirm whether only remix or instrumental variants remain

Scrape and run the full artist pipeline:

```powershell
python run_artist_pipeline.py `
  --web-manifest lyrics/web/ado_sources.template.json `
  --overwrite-web
```

Scale this to multiple artists from one registry:

```powershell
python bulk_scrape_artists.py `
  --registry lyrics/bulk/artist_registry.template.json `
  --project-root . `
  --overwrite
```

## Safety Notes

- The scraper uses only user-supplied URLs. It does not search the web by itself.
- `robots.txt` is respected by default.
- If a site blocks scraping or returns noisy markup, add a page-specific selector.
- For the three recommended Japanese lyric sources above, try `extraction_mode=auto` first before adding selectors.
- For the current practical order, start with `UtaTen`, then `PetitLyrics`, and keep `Uta-Net` as a manual reference source unless permission is clear.
- The coverage report now separates `Primary Works Missing From Lyrics` from `Variant-Only Gaps`, so a lower strict match count does not automatically mean the lyric corpus is incomplete for training.
- For large runs, prefer the bulk registry plus `request_delay_seconds` instead of firing many single-artist commands back to back.
- Review copyright, licensing, and site terms before using scraped lyrics for anything beyond private research.
