"""
Axle detection runner: runs the existing YOLO axle script in a subprocess,
updates axle status via internal API calls, and records the result.
On failure or timeout, sets axle_status=FAILED. Retries internal HTTP calls.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from typing import Optional

AXLE_MODEL_SCRIPT = os.environ.get(
    "AXLE_MODEL_SCRIPT",
    r"D:\Saisoft\Axle_Detection\Axle Detection with full truck\scripts\process_video_tracking.py",
)
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    r"D:\Saisoft\Axle_Detection\Axle Detection with full truck\runs\axle_truck_detection_full_optimized\weights\best.pt",
)
AXLE_VIDEO_PATH = os.environ.get("AXLE_VIDEO_PATH", "")
API_BASE = os.environ.get("TRUCK_API_BASE", "http://127.0.0.1:8000")

HTTP_RETRIES = 3
HTTP_RETRY_DELAY_SEC = 2


def _call_update_axle_status(truck_id: str, axle_status: str) -> bool:
    """POST /update-axle-status. Returns True if success."""
    url = f"{API_BASE}/update-axle-status"
    data = json.dumps({"truck_id": truck_id, "axle_status": axle_status}).encode("utf-8")
    for attempt in range(HTTP_RETRIES):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    return True
                print(f"[axle_runner] update-axle-status failed: {resp.status} (attempt {attempt + 1})", file=sys.stderr)
        except Exception as e:
            print(f"[axle_runner] update-axle-status error (attempt {attempt + 1}): {e}", file=sys.stderr)
        if attempt < HTTP_RETRIES - 1:
            time.sleep(HTTP_RETRY_DELAY_SEC)
    return False


def _call_axle_detection(truck_id: str, axle_count: int, processed_time: str) -> bool:
    """POST /axle-detection. Returns True if success."""
    url = f"{API_BASE}/axle-detection"
    payload = {"truck_id": truck_id, "axle_count": axle_count, "processed_time": processed_time}
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(HTTP_RETRIES):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    return True
                print(f"[axle_runner] axle-detection failed: {resp.status} (attempt {attempt + 1})", file=sys.stderr)
        except Exception as e:
            print(f"[axle_runner] axle-detection error (attempt {attempt + 1}): {e}", file=sys.stderr)
        if attempt < HTTP_RETRIES - 1:
            time.sleep(HTTP_RETRY_DELAY_SEC)
    return False


def _parse_axle_count_from_stdout(stdout: str) -> Optional[int]:
    match = re.search(r"Total unique axles tracked:\s*(\d+)", stdout, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def run_axle_detection(truck_id: str) -> None:
    """
    Run axle detection script; on success update axle_count and set DONE.
    On failure or timeout set axle_status=FAILED. Internal HTTP calls are retried.
    """
    print(f"[axle_runner] Starting axle detection for truck_id={truck_id}")
    _call_update_axle_status(truck_id, "PROCESSING")

    video_path = AXLE_VIDEO_PATH.strip() if AXLE_VIDEO_PATH else None
    if not video_path or not os.path.isfile(video_path):
        print(
            "[axle_runner] AXLE_VIDEO_PATH not set or file missing; using placeholder.",
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
            _call_update_axle_status(truck_id, "FAILED")
            return
        axle_count = _parse_axle_count_from_stdout(stdout)
        if axle_count is None:
            axle_count = 0
            print("[axle_runner] Could not parse axle count from stdout; using 0", file=sys.stderr)
        processed_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if _call_axle_detection(truck_id, axle_count, processed_time):
            print(f"[axle_runner] Done truck_id={truck_id} axle_count={axle_count}")
        else:
            _call_update_axle_status(truck_id, "FAILED")
    except subprocess.TimeoutExpired:
        print(f"[axle_runner] Axle script timed out for truck_id={truck_id}", file=sys.stderr)
        _call_update_axle_status(truck_id, "FAILED")
    except Exception as e:
        print(f"[axle_runner] Error running axle detection: {e}", file=sys.stderr)
        _call_update_axle_status(truck_id, "FAILED")
