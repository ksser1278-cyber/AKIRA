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


def resolve_path(project_root: Path, path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else (project_root / path).resolve()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def process_exists(pid: int | None) -> bool:
    if not pid:
        return False
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    return str(pid) in result.stdout


def latest_activity_epoch(paths: list[Path]) -> float | None:
    existing = [path.stat().st_mtime for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing)


def launch_runner(project_root: Path, launcher: dict) -> dict:
    log_dir = project_root / "reports" / "discography" / "longrun"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stdout_path = log_dir / f"bulk_longrun_{stamp}.stdout.log"
    stderr_path = log_dir / f"bulk_longrun_{stamp}.stderr.log"

    stdout_handle = stdout_path.open("w", encoding="utf-8")
    stderr_handle = stderr_path.open("w", encoding="utf-8")
    creationflags = 0x00000008 | 0x00000200 | 0x08000000

    command = [
        launcher.get("runner", sys.executable),
        "-u",
        str(project_root / "run_bulk_long.py"),
        "--registry",
        launcher.get("registry", "lyrics/bulk/artist_registry.longrun_dedup135.json"),
        "--max-rounds",
        str(launcher.get("max_rounds", 4)),
        "--sleep-minutes-between-rounds",
        str(launcher.get("sleep_minutes_between_rounds", 20)),
        "--stall-timeout-minutes",
        str(launcher.get("stall_timeout_minutes", 15)),
        "--poll-seconds",
        str(launcher.get("poll_seconds", 20)),
    ]
    proc = subprocess.Popen(
        command,
        cwd=str(project_root),
        stdout=stdout_handle,
        stderr=stderr_handle,
        creationflags=creationflags,
        close_fds=True,
    )
    restart_count = int(launcher.get("restart_count", 0)) + 1
    return {
        **launcher,
        "pid": proc.pid,
        "started_at": timestamp(),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "restart_count": restart_count,
        "last_restart_at": timestamp(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Watch the long-running bulk scrape and restart it if it stops unexpectedly.",
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parent),
        help="Project root that contains the long-run artifacts.",
    )
    parser.add_argument(
        "--launcher-path",
        default="reports/discography/longrun/bulk_longrun.launcher.json",
        help="Runner launcher JSON path.",
    )
    parser.add_argument(
        "--monitor-status-path",
        default="reports/discography/longrun/bulk_monitor_status.json",
        help="Supervisor status JSON path.",
    )
    parser.add_argument(
        "--monitor-meta-path",
        default="reports/discography/longrun/bulk_monitor_meta.json",
        help="Supervisor metadata JSON path.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=300,
        help="How often to inspect the runner.",
    )
    parser.add_argument(
        "--stale-minutes",
        type=int,
        default=60,
        help="Restart the runner if all activity files are older than this threshold.",
    )
    parser.add_argument(
        "--max-runtime-hours",
        type=int,
        default=21,
        help="How long the supervisor should keep monitoring before exiting.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    project_root = Path(args.project_root).resolve()
    launcher_path = resolve_path(project_root, args.launcher_path)
    monitor_status_path = resolve_path(project_root, args.monitor_status_path)
    monitor_meta_path = resolve_path(project_root, args.monitor_meta_path)
    started_at = time.time()

    meta = {
        "project_root": str(project_root),
        "launcher_path": str(launcher_path),
        "poll_seconds": args.poll_seconds,
        "stale_minutes": args.stale_minutes,
        "max_runtime_hours": args.max_runtime_hours,
        "pid": os.getpid(),
        "started_at": timestamp(),
        "runner": sys.executable,
    }
    write_json(monitor_meta_path, meta)

    while time.time() - started_at < args.max_runtime_hours * 3600:
        if not launcher_path.exists():
            raise FileNotFoundError(f"Runner launcher file not found: {launcher_path}")

        launcher = load_json(launcher_path)
        pid = launcher.get("pid")
        runner_alive = process_exists(pid)

        activity_paths = [
            resolve_path(project_root, "reports/discography/longrun/bulk_heartbeat.json"),
            resolve_path(project_root, "reports/discography/longrun/bulk_run_summary.longrun.json"),
            resolve_path(project_root, "reports/discography/longrun/longrun_status.json"),
        ]
        if launcher.get("stdout_log"):
            activity_paths.append(Path(launcher["stdout_log"]))
        if launcher.get("stderr_log"):
            activity_paths.append(Path(launcher["stderr_log"]))

        latest_epoch = latest_activity_epoch(activity_paths)
        stale = False
        if latest_epoch is not None:
            stale = (time.time() - latest_epoch) > args.stale_minutes * 60

        action = "observed"
        if not runner_alive or stale:
            launcher = launch_runner(project_root, launcher)
            write_json(launcher_path, launcher)
            pid = launcher.get("pid")
            runner_alive = process_exists(pid)
            latest_epoch = latest_activity_epoch(activity_paths)
            action = "restarted"

        status = {
            "timestamp": timestamp(),
            "runner_pid": pid,
            "runner_alive": runner_alive,
            "stale": stale,
            "action": action,
            "latest_activity_at": (
                datetime.fromtimestamp(latest_epoch).astimezone().isoformat()
                if latest_epoch is not None
                else None
            ),
            "launcher_path": str(launcher_path),
        }
        write_json(monitor_status_path, status)

        time.sleep(args.poll_seconds)

    finished_meta = {
        **meta,
        "finished_at": timestamp(),
    }
    write_json(monitor_meta_path, finished_meta)


if __name__ == "__main__":
    main()
