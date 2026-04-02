from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_summary(summary_path: Path) -> tuple[list[dict], list[dict]]:
    if not summary_path.exists():
        return [], []

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    return payload.get("results", []), payload.get("failures", [])


def resolve_path(project_root: Path, path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else (project_root / path).resolve()


def latest_activity_epoch(paths: list[Path], fallback_epoch: float) -> float:
    candidates = [fallback_epoch]
    for path in paths:
        if path.exists():
            candidates.append(path.stat().st_mtime)
    return max(candidates)


def terminate_process(process: subprocess.Popen[bytes], wait_seconds: int) -> None:
    process.terminate()
    try:
        process.wait(timeout=wait_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=wait_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the bulk scraping pipeline in multiple resumable rounds.",
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parent),
        help="Project root that contains bulk_scrape_artists.py.",
    )
    parser.add_argument(
        "--registry",
        default="lyrics/bulk/artist_registry.longrun_dedup135.json",
        help="Registry JSON path, relative to the project root unless absolute.",
    )
    parser.add_argument(
        "--summary-output",
        default="reports/discography/longrun/bulk_run_summary.longrun.json",
        help="Summary JSON path written by bulk_scrape_artists.py.",
    )
    parser.add_argument(
        "--status-path",
        default="reports/discography/longrun/longrun_status.json",
        help="Status JSON path updated after each round.",
    )
    parser.add_argument(
        "--meta-path",
        default="reports/discography/longrun/longrun_meta.json",
        help="Metadata JSON path for start and finish state.",
    )
    parser.add_argument(
        "--heartbeat-path",
        default="reports/discography/longrun/bulk_heartbeat.json",
        help="Heartbeat JSON path updated by bulk_scrape_artists.py.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=4,
        help="Maximum retry rounds.",
    )
    parser.add_argument(
        "--sleep-minutes-between-rounds",
        type=int,
        default=20,
        help="Minutes to wait between retry rounds when failures remain.",
    )
    parser.add_argument(
        "--stall-timeout-minutes",
        type=int,
        default=15,
        help="Terminate and retry if no heartbeat or summary update happens within this many minutes.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=20,
        help="Polling interval used by the stall watchdog.",
    )
    parser.add_argument(
        "--terminate-wait-seconds",
        type=int,
        default=10,
        help="Seconds to wait after terminate() before forcing kill().",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    project_root = Path(args.project_root).resolve()
    summary_path = resolve_path(project_root, args.summary_output)
    status_path = resolve_path(project_root, args.status_path)
    meta_path = resolve_path(project_root, args.meta_path)
    heartbeat_path = resolve_path(project_root, args.heartbeat_path)

    started_meta = {
        "project_root": str(project_root),
        "registry": args.registry,
        "summary_path": str(summary_path),
        "status_path": str(status_path),
        "heartbeat_path": str(heartbeat_path),
        "pid": os.getpid(),
        "started_at": timestamp(),
        "max_rounds": args.max_rounds,
        "sleep_minutes_between_rounds": args.sleep_minutes_between_rounds,
        "stall_timeout_minutes": args.stall_timeout_minutes,
        "poll_seconds": args.poll_seconds,
        "runner": sys.executable,
    }
    write_json(meta_path, started_meta)

    for round_index in range(1, args.max_rounds + 1):
        round_started_at = timestamp()
        print(f"[{round_started_at}] Starting bulk scrape round {round_index} of {args.max_rounds}", flush=True)
        if heartbeat_path.exists():
            heartbeat_path.unlink()

        command = [
            sys.executable,
            "-u",
            "bulk_scrape_artists.py",
            "--registry",
            args.registry,
            "--project-root",
            ".",
            "--overwrite",
            "--continue-on-error",
            "--skip-completed",
            "--normalize-manifests",
            "--summary-output",
            args.summary_output,
            "--heartbeat-path",
            args.heartbeat_path,
        ]
        child_env = os.environ.copy()
        child_env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(command, cwd=project_root, env=child_env)
        round_started_epoch = time.time()
        stalled = False
        last_activity_epoch = round_started_epoch

        while True:
            current_returncode = process.poll()
            last_activity_epoch = latest_activity_epoch([heartbeat_path, summary_path], round_started_epoch)
            if current_returncode is not None:
                break

            if time.time() - last_activity_epoch > args.stall_timeout_minutes * 60:
                print(
                    f"[{timestamp()}] No heartbeat or summary update for "
                    f"{args.stall_timeout_minutes} minute(s). Restarting the child process.",
                    flush=True,
                )
                terminate_process(process, args.terminate_wait_seconds)
                stalled = True
                break

            time.sleep(args.poll_seconds)

        result_returncode = process.returncode if process.returncode is not None else process.wait()

        results, failures = load_summary(summary_path)
        completed_count = sum(1 for item in results if item.get("status") == "completed")
        skipped_count = sum(1 for item in results if item.get("status") == "skipped")
        failed_count = sum(1 for item in results if item.get("status") == "failed")

        status = {
            "project_root": str(project_root),
            "registry": args.registry,
            "updated_at": timestamp(),
            "round": round_index,
            "max_rounds": args.max_rounds,
            "exit_code": result_returncode,
            "total_results": len(results),
            "completed": completed_count,
            "skipped": skipped_count,
            "failed_results": failed_count,
            "failure_count": len(failures),
            "stalled": stalled,
            "round_started_at": round_started_at,
            "last_activity_at": datetime.fromtimestamp(last_activity_epoch).astimezone().isoformat(),
            "summary_path": str(summary_path),
            "heartbeat_path": str(heartbeat_path),
        }
        write_json(status_path, status)

        print(
            f"[{timestamp()}] Round {round_index} finished "
            f"exit={result_returncode} completed={completed_count} "
            f"skipped={skipped_count} failures={len(failures)} stalled={stalled}",
            flush=True,
        )

        if result_returncode == 0 and not failures and not stalled:
            print(f"[{timestamp()}] Bulk scrape completed without remaining failures.", flush=True)
            break

        if round_index < args.max_rounds:
            print(
                f"[{timestamp()}] Sleeping {args.sleep_minutes_between_rounds} minute(s) before retry.",
                flush=True,
            )
            time.sleep(args.sleep_minutes_between_rounds * 60)

    finished_meta = {
        **started_meta,
        "finished_at": timestamp(),
    }
    write_json(meta_path, finished_meta)


if __name__ == "__main__":
    main()
