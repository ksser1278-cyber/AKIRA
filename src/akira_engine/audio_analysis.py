from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from statistics import median


def load_audio_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def probe_audio_file(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
    payload = json.loads(result.stdout)
    format_info = payload.get("format", {})
    streams = payload.get("streams", [])
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})

    duration = format_info.get("duration") or audio_stream.get("duration")
    bit_rate = format_info.get("bit_rate") or audio_stream.get("bit_rate")

    return {
        "exists": True,
        "format_name": format_info.get("format_name"),
        "codec_name": audio_stream.get("codec_name"),
        "sample_rate_hz": _safe_int(audio_stream.get("sample_rate")),
        "channels": _safe_int(audio_stream.get("channels")),
        "channel_layout": audio_stream.get("channel_layout"),
        "duration_seconds": _safe_float(duration),
        "bit_rate": _safe_int(bit_rate),
        "size_bytes": _safe_int(format_info.get("size")),
    }


def analyze_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    missing_files = 0

    for track in manifest.get("tracks", []):
        source_path = Path(track["source_path"])
        if not source_path.exists():
            records.append(
                {
                    **track,
                    "exists": False,
                    "error": "file_not_found",
                }
            )
            missing_files += 1
            continue

        probe = probe_audio_file(source_path)
        loudness = measure_loudness(source_path)
        dynamics = measure_dynamics(source_path)
        energy_curve = measure_energy_curve(source_path, probe.get("duration_seconds"))
        records.append({**track, **probe, "loudness": loudness, "dynamics": dynamics, "energy_curve": energy_curve})

    durations = [record["duration_seconds"] for record in records if record.get("exists") and record.get("duration_seconds")]
    sample_rates = [record["sample_rate_hz"] for record in records if record.get("exists") and record.get("sample_rate_hz")]

    return {
        "schema_version": "1.0",
        "record_type": "audio_analysis_summary",
        "source_root": manifest.get("source_root"),
        "track_count": len(records),
        "missing_file_count": missing_files,
        "average_duration_seconds": round(sum(durations) / len(durations), 2) if durations else 0.0,
        "sample_rates_hz": sorted(set(sample_rates)),
        "tracks": records,
    }


def render_audio_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Audio Analysis Summary",
        "",
        f"- Source root: `{summary.get('source_root', '')}`",
        f"- Tracks: `{summary['track_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Average duration seconds: `{summary['average_duration_seconds']}`",
        f"- Sample rates: `{', '.join(str(rate) for rate in summary['sample_rates_hz'])}`",
        "",
    ]

    for track in summary["tracks"]:
        lines.append(f"## {track['track_id']}")
        lines.append(f"- Artist: `{track['artist_id']}`")
        lines.append(f"- Title: `{track['title']}`")
        lines.append(f"- File: `{track['source_filename']}`")
        if not track.get("exists"):
            lines.append("- Exists: `false`")
            lines.append(f"- Error: `{track.get('error', 'unknown')}`")
            lines.append("")
            continue
        lines.append(f"- Format: `{track.get('format_name', '')}`")
        lines.append(f"- Codec: `{track.get('codec_name', '')}`")
        lines.append(f"- Sample rate: `{track.get('sample_rate_hz', '')}`")
        lines.append(f"- Channels: `{track.get('channels', '')}`")
        lines.append(f"- Duration seconds: `{track.get('duration_seconds', '')}`")
        lines.append(f"- Bit rate: `{track.get('bit_rate', '')}`")
        lines.append(f"- Size bytes: `{track.get('size_bytes', '')}`")
        loudness = track.get("loudness", {})
        dynamics = track.get("dynamics", {})
        if loudness:
            lines.append(f"- Integrated loudness: `{loudness.get('integrated_lufs', '')}` LUFS")
            lines.append(f"- Loudness range: `{loudness.get('lra_lu', '')}` LU")
        if dynamics:
            lines.append(f"- RMS window count: `{dynamics.get('window_count', '')}`")
            lines.append(f"- RMS median: `{dynamics.get('rms_median_db', '')}` dB")
            lines.append(f"- RMS span: `{dynamics.get('rms_span_db', '')}` dB")
        energy_curve = track.get("energy_curve", {})
        if energy_curve:
            lines.append(f"- Early energy: `{energy_curve.get('early_rms_db', '')}` dB")
            lines.append(f"- Mid energy: `{energy_curve.get('mid_rms_db', '')}` dB")
            lines.append(f"- Late energy: `{energy_curve.get('late_rms_db', '')}` dB")
            lines.append(f"- End lift vs early: `{energy_curve.get('late_minus_early_db', '')}` dB")
            lines.append(f"- Peak zone: `{energy_curve.get('peak_zone', '')}`")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return round(float(value), 3) if value is not None else None
    except (TypeError, ValueError):
        return None


def measure_loudness(path: Path) -> dict[str, Any]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-vn",
        "-i",
        str(path),
        "-filter_complex",
        "ebur128=framelog=verbose",
        "-f",
        "null",
        "NUL",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    text = (result.stdout or "") + "\n" + (result.stderr or "")

    integrated = None
    lra = None
    threshold = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("I:"):
            integrated = _extract_first_float(line)
        elif line.startswith("LRA:"):
            lra = _extract_first_float(line)
        elif line.startswith("Threshold:") and integrated is not None and threshold is None:
            threshold = _extract_first_float(line)

    return {
        "integrated_lufs": integrated,
        "lra_lu": lra,
        "threshold_lufs": threshold,
    }


def measure_dynamics(path: Path) -> dict[str, Any]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-vn",
        "-i",
        str(path),
        "-af",
        "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
        "-f",
        "null",
        "NUL",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    text = (result.stdout or "") + "\n" + (result.stderr or "")
    values: list[float] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("lavfi.astats.Overall.RMS_level="):
            value = line.split("=", 1)[1].strip()
            parsed = _safe_float(value)
            if parsed is not None and parsed > -120:
                values.append(parsed)

    if not values:
        return {
            "window_count": 0,
            "rms_min_db": None,
            "rms_max_db": None,
            "rms_median_db": None,
            "rms_span_db": None,
        }

    rms_min = min(values)
    rms_max = max(values)
    rms_median = round(median(values), 3)
    rms_span = round(rms_max - rms_min, 3)
    return {
        "window_count": len(values),
        "rms_min_db": round(rms_min, 3),
        "rms_max_db": round(rms_max, 3),
        "rms_median_db": rms_median,
        "rms_span_db": rms_span,
    }


def measure_energy_curve(path: Path, duration_seconds: float | None) -> dict[str, Any]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-vn",
        "-i",
        str(path),
        "-af",
        "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
        "-f",
        "null",
        "NUL",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    text = (result.stdout or "") + "\n" + (result.stderr or "")

    points: list[tuple[float, float]] = []
    current_time: float | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("frame:") and "pts_time:" in line:
            try:
                current_time = float(line.split("pts_time:", 1)[1].strip())
            except ValueError:
                current_time = None
        elif line.startswith("lavfi.astats.Overall.RMS_level=") and current_time is not None:
            parsed = _safe_float(line.split("=", 1)[1].strip())
            if parsed is not None and parsed > -120:
                points.append((current_time, parsed))

    if not points or not duration_seconds or duration_seconds <= 0:
        return {
            "point_count": len(points),
            "early_rms_db": None,
            "mid_rms_db": None,
            "late_rms_db": None,
            "late_minus_early_db": None,
            "peak_zone": None,
        }

    early_values = [value for time, value in points if time <= duration_seconds * 0.33]
    mid_values = [value for time, value in points if duration_seconds * 0.33 < time <= duration_seconds * 0.66]
    late_values = [value for time, value in points if time > duration_seconds * 0.66]

    early = _median_or_none(early_values)
    mid = _median_or_none(mid_values)
    late = _median_or_none(late_values)

    peak_time, _peak_value = max(points, key=lambda item: item[1])
    if peak_time <= duration_seconds * 0.33:
        peak_zone = "early"
    elif peak_time <= duration_seconds * 0.66:
        peak_zone = "mid"
    else:
        peak_zone = "late"

    return {
        "point_count": len(points),
        "early_rms_db": early,
        "mid_rms_db": mid,
        "late_rms_db": late,
        "late_minus_early_db": round(late - early, 3) if early is not None and late is not None else None,
        "peak_zone": peak_zone,
    }


def _extract_first_float(text: str) -> float | None:
    token = ""
    seen_digit = False
    for char in text:
        if char.isdigit() or char in {"-", "."}:
            token += char
            seen_digit = True
        elif seen_digit:
            break
    return _safe_float(token) if token else None


def _median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(median(values), 3)
