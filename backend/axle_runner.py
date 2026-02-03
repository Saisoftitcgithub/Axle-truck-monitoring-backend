"""
Axle detection runner: runs the existing YOLO axle script in a subprocess,
updates axle status via internal API calls, and records the result.
All runs locally (no Celery/Redis).
"""

import os
from typing import Optional
import re
import subprocess
import sys
from datetime import datetime, timezone

# Paths for the existing axle detection script and model (override via env if needed)
AXLE_MODEL_SCRIPT = os.environ.get(
    "AXLE_MODEL_SCRIPT",
    r"D:\Saisoft\Axle_Detection\Axle Detection with full truck\scripts\process_video_tracking.py",
)
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    r"D:\Saisoft\Axle_Detection\Axle Detection with full truck\runs\axle_truck_detection_full_optimized\weights\best.pt",
)
# Optional: video path for axle script (script requires --video). Set AXLE_VIDEO_PATH for real runs.
AXLE_VIDEO_PATH = os.environ.get("AXLE_VIDEO_PATH", "")
# Base URL for internal API calls (this FastAPI app)
API_BASE = os.environ.get("TRUCK_API_BASE", "http://127.0.0.1:8000")


def _call_update_axle_status(truck_id: str, axle_status: str) -> None:
    """POST /update-axle-status with axle_status=PROCESSING (or PENDING/DONE)."""
    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            f"{API_BASE}/update-axle-status",
            data=json.dumps({"truck_id": truck_id, "axle_status": axle_status}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201):
                print(f"[axle_runner] update-axle-status failed: {resp.status}", file=sys.stderr)
    except Exception as e:
        print(f"[axle_runner] Error calling update-axle-status: {e}", file=sys.stderr)


def _call_axle_detection(truck_id: str, axle_count: int, processed_time: str) -> None:
    """POST /axle-detection with truck_id, axle_count, processed_time."""
    try:
        import urllib.request
        import json
        payload = {
            "truck_id": truck_id,
            "axle_count": axle_count,
            "processed_time": processed_time,
        }
        req = urllib.request.Request(
            f"{API_BASE}/axle-detection",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201):
                print(f"[axle_runner] axle-detection failed: {resp.status}", file=sys.stderr)
    except Exception as e:
        print(f"[axle_runner] Error calling axle-detection: {e}", file=sys.stderr)


def _parse_axle_count_from_stdout(stdout: str) -> Optional[int]:
    """
    Parse axle count from script stdout. Script prints: 'Total unique axles tracked: N'
    """
    match = re.search(r"Total unique axles tracked:\s*(\d+)", stdout, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def run_axle_detection(truck_id: str) -> None:
    """
    Run the axle detection script in a subprocess for the given truck_id.
    - Calls POST /update-axle-status with axle_status=PROCESSING before running.
    - Runs the script with MODEL_PATH env and truck_id (and video path if set).
    - After subprocess finishes, parses axle count from stdout and calls POST /axle-detection.
    - On errors, logs and does not crash (caller is background task).
    """
    print(f"[axle_runner] Starting axle detection for truck_id={truck_id}")
    _call_update_axle_status(truck_id, "PROCESSING")

    # Script requires --video; use env or placeholder
    video_path = AXLE_VIDEO_PATH.strip() if AXLE_VIDEO_PATH else None
    if not video_path or not os.path.isfile(video_path):
        print(
            f"[axle_runner] AXLE_VIDEO_PATH not set or file missing; using placeholder. "
            "Set AXLE_VIDEO_PATH to a real video for axle detection.",
            file=sys.stderr,
        )
        video_path = video_path or "placeholder.mp4"

    env = os.environ.copy()
    env["MODEL_PATH"] = MODEL_PATH
    env["TRUCK_ID"] = truck_id

    cmd = [
        sys.executable,
        AXLE_MODEL_SCRIPT,
        "--video", video_path,
        "--model", MODEL_PATH,
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
            cwd=os.path.dirname(AXLE_MODEL_SCRIPT) or ".",
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        if result.returncode != 0:
            print(f"[axle_runner] Subprocess exited with code {result.returncode}", file=sys.stderr)
            print(f"[axle_runner] stderr: {stderr[:500]}", file=sys.stderr)
        axle_count = _parse_axle_count_from_stdout(stdout)
        if axle_count is None:
            axle_count = 0
            print(f"[axle_runner] Could not parse axle count from stdout; using 0", file=sys.stderr)
        processed_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _call_axle_detection(truck_id, axle_count, processed_time)
        print(f"[axle_runner] Done truck_id={truck_id} axle_count={axle_count}")
    except subprocess.TimeoutExpired:
        print(f"[axle_runner] Axle script timed out for truck_id={truck_id}", file=sys.stderr)
    except Exception as e:
        print(f"[axle_runner] Error running axle detection: {e}", file=sys.stderr)
