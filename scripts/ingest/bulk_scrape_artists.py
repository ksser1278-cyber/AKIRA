from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backfill_from_spotify import match_secondary_sources
from compare_discography_coverage import build_report
from src.akira_engine.discography import (
    build_discography_manifest_payload,
    discover_discography_manifest,
    discover_discography_sources,
    write_web_manifest,
)
from src.akira_engine.ingest import load_manifest, normalize_manifest
from src.akira_engine.manifest_tools import merge_lyric_manifests
from src.akira_engine.spotify import (
    SpotifyClient,
    build_artist_discography_snapshot,
    choose_best_artist_match,
    compare_lyric_manifest_to_spotify,
    write_json,
)
from src.akira_engine.web_scrape import load_web_manifest, scrape_web_manifest


@dataclass
class BulkArtistSummary:
    artist_id: str
    artist_name: str
    final_manifest: str
    spotify_snapshot: str
    strict_coverage: str
    primary_coverage: str
    final_report: str
    normalized_output: str | None = None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(base_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def write_coverage_report(
    output_path: Path,
    comparison: dict[str, Any],
    lyrics_manifest_path: Path,
    spotify_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_report(comparison, lyrics_manifest_path, spotify_path),
        encoding="utf-8",
    )


def persist_bulk_summary(
    output_path: Path,
    *,
    root_dir: Path,
    registry_path: Path,
    results: list[BulkArtistSummary],
    failures: list[dict[str, str]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_root": str(root_dir),
                "registry": str(registry_path),
                "results": [asdict(item) for item in results],
                "failures": failures,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_heartbeat(
    heartbeat_path: Path | None,
    *,
    stage: str,
    artist_entry: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    if heartbeat_path is None:
        return

    payload: dict[str, Any] = {
        "timestamp": time.time(),
        "stage": stage,
    }
    if artist_entry is not None:
        payload["artist_id"] = artist_entry.get("artist_id")
        payload["artist_name"] = artist_entry.get("artist_name")
    if details:
        payload["details"] = details

    write_json(heartbeat_path, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the large-scale lyric scraping pipeline from an artist registry."
    )
    parser.add_argument("--registry", required=True, type=Path, help="Path to the bulk artist registry JSON file.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used to resolve relative output paths. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--artists",
        help="Optional comma-separated list of artist_id values to run.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite already-scraped raw lyric files during bulk scraping.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing the remaining artists if one artist fails.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Optional JSON output path for the bulk run summary.",
    )
    parser.add_argument(
        "--skip-completed",
        action="store_true",
        help="Skip artists whose final manifest, Spotify snapshot, and final report already exist.",
    )
    parser.add_argument(
        "--normalize-manifests",
        action="store_true",
        help="Normalize each final lyric manifest after scraping completes.",
    )
    parser.add_argument(
        "--heartbeat-path",
        type=Path,
        help="Optional JSON heartbeat path updated throughout the bulk run.",
    )
    return parser.parse_args()


def expected_paths(root_dir: Path, artist_entry: dict[str, Any]) -> dict[str, Path]:
    artist_id = artist_entry["artist_id"]
    primary_site = artist_entry["primary_discovery"]["site"]
    primary_manifest = resolve_path(
        root_dir,
        artist_entry.get("primary_manifest") or f"lyrics/manifests/{artist_id}_manifest.json",
    )
    merged_manifest = resolve_path(
        root_dir,
        artist_entry.get("merged_manifest") or f"lyrics/manifests/{artist_id}_manifest.merged.json",
    )
    spotify_output = resolve_path(
        root_dir,
        artist_entry.get("spotify_output") or f"data/spotify/{artist_id}_discography.json",
    )
    final_report = resolve_path(
        root_dir,
        artist_entry.get("final_coverage_report") or f"reports/discography/{artist_id}_coverage.merged.md",
    )
    primary_web_manifest = resolve_path(
        root_dir,
        artist_entry.get("primary_web_manifest") or f"lyrics/web/{artist_id}_discography.{primary_site}.json",
    )
    needs_merged = bool(artist_entry.get("secondary_backfill") or artist_entry.get("manual_backfill_manifest"))
    final_manifest = merged_manifest if needs_merged else primary_manifest
    normalized_output = root_dir / "lyrics" / "normalized" / artist_id
    return {
        "primary_web_manifest": primary_web_manifest,
        "primary_manifest": primary_manifest,
        "merged_manifest": merged_manifest,
        "final_manifest": final_manifest,
        "spotify_output": spotify_output,
        "final_report": final_report,
        "normalized_output": normalized_output,
    }


def existing_artist_summary(root_dir: Path, artist_entry: dict[str, Any]) -> BulkArtistSummary:
    paths = expected_paths(root_dir, artist_entry)
    spotify_snapshot = load_json(paths["spotify_output"])
    final_manifest = load_manifest(paths["final_manifest"])
    comparison = compare_lyric_manifest_to_spotify(final_manifest, spotify_snapshot)
    normalized_output = paths["normalized_output"] if paths["normalized_output"].exists() else None
    return BulkArtistSummary(
        artist_id=artist_entry["artist_id"],
        artist_name=artist_entry["artist_name"],
        final_manifest=str(paths["final_manifest"]),
        spotify_snapshot=str(paths["spotify_output"]),
        strict_coverage=(
            f"{comparison['matched_count']}/{comparison['spotify_canonical_track_count']}"
        ),
        primary_coverage=(
            f"{comparison['primary_lyric_matched_count']}/"
            f"{comparison['spotify_primary_lyric_track_count']}"
        ),
        final_report=str(paths["final_report"]),
        normalized_output=str(normalized_output) if normalized_output else None,
    )


def is_artist_completed(root_dir: Path, artist_entry: dict[str, Any]) -> bool:
    paths = expected_paths(root_dir, artist_entry)
    required_paths = [paths["final_manifest"], paths["spotify_output"], paths["final_report"]]
    return all(path.exists() for path in required_paths)


def fetch_spotify_snapshot(
    client: SpotifyClient,
    *,
    artist_name: str,
    spotify_artist_id: str | None,
    spotify_lookup_name: str | None,
    market: str,
    include_groups: str,
    output_path: Path,
) -> Path:
    if spotify_artist_id:
        artist_id = spotify_artist_id
    else:
        matches = client.search_artist(spotify_lookup_name or artist_name)
        match = choose_best_artist_match(matches, spotify_lookup_name or artist_name)
        artist_id = match.artist_id

    snapshot = build_artist_discography_snapshot(
        client=client,
        artist_id=artist_id,
        market=market,
        include_groups=include_groups,
    )
    write_json(output_path, snapshot)
    return output_path


def run_artist_pipeline(
    *,
    root_dir: Path,
    artist_entry: dict[str, Any],
    defaults: dict[str, Any],
    spotify_client: SpotifyClient,
    overwrite: bool,
    normalize_outputs: bool,
    heartbeat_path: Path | None,
) -> BulkArtistSummary:
    artist_id = artist_entry["artist_id"]
    artist_name = artist_entry["artist_name"]
    language = artist_entry.get("language", defaults.get("language", "ja"))
    request_delay_seconds = float(
        artist_entry.get("request_delay_seconds", defaults.get("request_delay_seconds", 0.0))
    )
    market = artist_entry.get("spotify_market", defaults.get("spotify_market", "JP"))
    include_groups = artist_entry.get(
        "spotify_include_groups",
        defaults.get("spotify_include_groups", "album,single,compilation"),
    )

    primary = artist_entry["primary_discovery"]
    primary_site = primary["site"]
    primary_url = primary["artist_url"]
    primary_web_manifest = resolve_path(
        root_dir,
        artist_entry.get("primary_web_manifest") or f"lyrics/web/{artist_id}_discography.{primary_site}.json",
    )
    primary_manifest_path = resolve_path(
        root_dir,
        artist_entry.get("primary_manifest") or f"lyrics/manifests/{artist_id}_manifest.json",
    )
    write_heartbeat(
        heartbeat_path,
        stage="discover_primary",
        artist_entry=artist_entry,
        details={"site": primary_site, "artist_url": primary_url},
    )

    discover_discography_manifest(
        artist_id=artist_id,
        artist_name=artist_name,
        language=language,
        site=primary_site,
        artist_url=primary_url,
        output_path=primary_web_manifest,
        raw_output_dir=f"../raw/{artist_id}",
        manifest_output_path=f"../manifests/{primary_manifest_path.name}",
        request_delay_seconds=request_delay_seconds,
    )
    write_heartbeat(
        heartbeat_path,
        stage="scrape_primary",
        artist_entry=artist_entry,
        details={"web_manifest": str(primary_web_manifest)},
    )
    primary_scrape_summary = scrape_web_manifest(
        primary_web_manifest,
        overwrite=overwrite,
        progress_callback=lambda event: write_heartbeat(
            heartbeat_path,
            stage="scrape_primary_progress",
            artist_entry=artist_entry,
            details=event,
        ),
    )
    current_manifest_path = primary_scrape_summary.manifest_path

    spotify_output = resolve_path(
        root_dir,
        artist_entry.get("spotify_output") or f"data/spotify/{artist_id}_discography.json",
    )
    write_heartbeat(
        heartbeat_path,
        stage="spotify_snapshot",
        artist_entry=artist_entry,
        details={"output_path": str(spotify_output)},
    )
    spotify_path = fetch_spotify_snapshot(
        spotify_client,
        artist_name=artist_name,
        spotify_artist_id=artist_entry.get("spotify_artist_id"),
        spotify_lookup_name=artist_entry.get("spotify_artist_name"),
        market=market,
        include_groups=include_groups,
        output_path=spotify_output,
    )
    spotify_snapshot = load_json(spotify_path)

    initial_comparison = compare_lyric_manifest_to_spotify(load_manifest(current_manifest_path), spotify_snapshot)
    initial_report_path = resolve_path(
        root_dir,
        artist_entry.get("initial_coverage_report") or f"reports/discography/{artist_id}_coverage.md",
    )
    write_coverage_report(initial_report_path, initial_comparison, current_manifest_path, spotify_path)

    merged_manifest_path = resolve_path(
        root_dir,
        artist_entry.get("merged_manifest") or f"lyrics/manifests/{artist_id}_manifest.merged.json",
    )

    secondary = artist_entry.get("secondary_backfill")
    if secondary:
        write_heartbeat(
            heartbeat_path,
            stage="discover_secondary",
            artist_entry=artist_entry,
            details={"site": secondary["site"], "artist_url": secondary["artist_url"]},
        )
        secondary_sources = discover_discography_sources(
            secondary["site"],
            secondary["artist_url"],
            request_delay_seconds=request_delay_seconds,
        )
        matched_sources, _ = match_secondary_sources(
            initial_comparison["spotify_missing_from_lyrics"],
            secondary_sources,
        )
        if matched_sources:
            primary_payload = load_web_manifest(primary_web_manifest)
            supplemental_manifest = resolve_path(
                root_dir,
                artist_entry.get("secondary_manifest")
                or f"lyrics/manifests/{artist_id}_manifest.{secondary['site']}.json",
            )
            secondary_web_manifest = resolve_path(
                root_dir,
                artist_entry.get("secondary_web_manifest")
                or f"lyrics/web/{artist_id}_spotify_backfill.{secondary['site']}.json",
            )
            payload = build_discography_manifest_payload(
                artist_id=artist_id,
                artist_name=artist_name,
                language=language,
                site=f"spotify_backfill_{secondary['site']}",
                artist_url=secondary["artist_url"],
                raw_output_dir=primary_payload.get("raw_output_dir", f"../raw/{artist_id}"),
                manifest_output_path=f"../manifests/{supplemental_manifest.name}",
                sources=matched_sources,
                request_delay_seconds=request_delay_seconds,
            )
            write_web_manifest(secondary_web_manifest, payload)
            write_heartbeat(
                heartbeat_path,
                stage="scrape_secondary",
                artist_entry=artist_entry,
                details={"web_manifest": str(secondary_web_manifest)},
            )
            secondary_summary = scrape_web_manifest(
                secondary_web_manifest,
                overwrite=overwrite,
                progress_callback=lambda event: write_heartbeat(
                    heartbeat_path,
                    stage="scrape_secondary_progress",
                    artist_entry=artist_entry,
                    details=event,
                ),
            )
            current_manifest_path = merge_lyric_manifests(
                current_manifest_path,
                secondary_summary.manifest_path,
                merged_manifest_path,
            )

    manual_manifest = resolve_path(root_dir, artist_entry.get("manual_backfill_manifest"))
    if manual_manifest and manual_manifest.exists():
        write_heartbeat(
            heartbeat_path,
            stage="scrape_manual_backfill",
            artist_entry=artist_entry,
            details={"web_manifest": str(manual_manifest)},
        )
        manual_summary = scrape_web_manifest(
            manual_manifest,
            overwrite=overwrite,
            progress_callback=lambda event: write_heartbeat(
                heartbeat_path,
                stage="scrape_manual_progress",
                artist_entry=artist_entry,
                details=event,
            ),
        )
        current_manifest_path = merge_lyric_manifests(
            current_manifest_path,
            manual_summary.manifest_path,
            merged_manifest_path,
        )

    final_comparison = compare_lyric_manifest_to_spotify(load_manifest(current_manifest_path), spotify_snapshot)
    final_report_path = resolve_path(
        root_dir,
        artist_entry.get("final_coverage_report") or f"reports/discography/{artist_id}_coverage.merged.md",
    )
    write_coverage_report(final_report_path, final_comparison, current_manifest_path, spotify_path)

    normalized_output: str | None = None
    if normalize_outputs:
        write_heartbeat(
            heartbeat_path,
            stage="normalize_manifest",
            artist_entry=artist_entry,
            details={"manifest_path": str(current_manifest_path)},
        )
        normalized_summary = normalize_manifest(current_manifest_path, root_dir / "lyrics" / "normalized")
        normalized_output = str(normalized_summary.output_dir)

    write_heartbeat(
        heartbeat_path,
        stage="artist_complete",
        artist_entry=artist_entry,
        details={
            "final_manifest": str(current_manifest_path),
            "spotify_snapshot": str(spotify_path),
            "final_report": str(final_report_path),
        },
    )
    return BulkArtistSummary(
        artist_id=artist_id,
        artist_name=artist_name,
        final_manifest=str(current_manifest_path),
        spotify_snapshot=str(spotify_path),
        strict_coverage=(
            f"{final_comparison['matched_count']}/{final_comparison['spotify_canonical_track_count']}"
        ),
        primary_coverage=(
            f"{final_comparison['primary_lyric_matched_count']}/"
            f"{final_comparison['spotify_primary_lyric_track_count']}"
        ),
        final_report=str(final_report_path),
        normalized_output=normalized_output,
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    registry_path = args.registry.resolve()
    root_dir = args.project_root.resolve()
    heartbeat_path = args.heartbeat_path.resolve() if args.heartbeat_path else None
    registry = load_json(registry_path)
    defaults = registry.get("defaults", {})
    selected_artists = {item.strip() for item in (args.artists or "").split(",") if item.strip()}
    artist_delay_seconds = float(defaults.get("artist_delay_seconds", 0.0))
    summary_output = args.summary_output or (Path("reports") / "discography" / "bulk_run_summary.json")
    final_summary_path = summary_output if summary_output.is_absolute() else (root_dir / summary_output).resolve()

    spotify_client = SpotifyClient.from_env()
    results: list[BulkArtistSummary] = []
    failures: list[dict[str, str]] = []

    enabled_artists = [
        artist
        for artist in registry.get("artists", [])
        if artist.get("enabled", True)
        and (not selected_artists or artist["artist_id"] in selected_artists)
    ]

    for index, artist_entry in enumerate(enabled_artists, start=1):
        try:
            write_heartbeat(
                heartbeat_path,
                stage="artist_start",
                artist_entry=artist_entry,
                details={"index": index, "total_artists": len(enabled_artists)},
            )
            print(
                f"[{index}/{len(enabled_artists)}] Starting {artist_entry['artist_name']} "
                f"({artist_entry['artist_id']})",
                flush=True,
            )
            if args.skip_completed and is_artist_completed(root_dir, artist_entry):
                result = existing_artist_summary(root_dir, artist_entry)
                results.append(result)
                persist_bulk_summary(
                    final_summary_path,
                    root_dir=root_dir,
                    registry_path=registry_path,
                    results=results,
                    failures=failures,
                )
                print(
                    f"[{index}/{len(enabled_artists)}] {result.artist_name}: "
                    f"skipped existing strict={result.strict_coverage}, primary={result.primary_coverage}",
                    flush=True,
                )
                write_heartbeat(
                    heartbeat_path,
                    stage="artist_skipped",
                    artist_entry=artist_entry,
                    details={"strict_coverage": result.strict_coverage, "primary_coverage": result.primary_coverage},
                )
                if index < len(enabled_artists) and artist_delay_seconds > 0:
                    time.sleep(artist_delay_seconds)
                continue
            result = run_artist_pipeline(
                root_dir=root_dir,
                artist_entry=artist_entry,
                defaults=defaults,
                spotify_client=spotify_client,
                overwrite=args.overwrite,
                normalize_outputs=args.normalize_manifests,
                heartbeat_path=heartbeat_path,
            )
            results.append(result)
            print(
                f"[{index}/{len(enabled_artists)}] {result.artist_name}: "
                f"strict={result.strict_coverage}, primary={result.primary_coverage}",
                flush=True,
            )
            persist_bulk_summary(
                final_summary_path,
                root_dir=root_dir,
                registry_path=registry_path,
                results=results,
                failures=failures,
            )
        except Exception as exc:  # pragma: no cover - CLI-level guard
            failures.append({"artist_id": artist_entry["artist_id"], "error": str(exc)})
            write_heartbeat(
                heartbeat_path,
                stage="artist_error",
                artist_entry=artist_entry,
                details={"error": str(exc)},
            )
            persist_bulk_summary(
                final_summary_path,
                root_dir=root_dir,
                registry_path=registry_path,
                results=results,
                failures=failures,
            )
            print(f"[ERROR] {artist_entry['artist_id']}: {exc}", flush=True)
            if not args.continue_on_error:
                raise
        if index < len(enabled_artists) and artist_delay_seconds > 0:
            time.sleep(artist_delay_seconds)

    persist_bulk_summary(
        final_summary_path,
        root_dir=root_dir,
        registry_path=registry_path,
        results=results,
        failures=failures,
    )
    write_heartbeat(
        heartbeat_path,
        stage="bulk_complete",
        details={"summary_path": str(final_summary_path), "failure_count": len(failures)},
    )
    print(f"Summary: {final_summary_path}", flush=True)


if __name__ == "__main__":
    main()
