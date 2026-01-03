from __future__ import annotations

import random
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import requests

API_URL = "http://127.0.0.1:8000/api/checkin"
API_KEY = "dev-secret-key"  # must match app/main.py

FLEET_SIZE = 30
INTERVAL_SECONDS = 3  # how often each device reports (roughly)
LOCATION_TAGS = ["Adult Area", "Teen Area", "Children's", "Study Zone", "Reference"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def boot_time(uptime_seconds: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=uptime_seconds)).isoformat()


def make_device_ids(n: int) -> List[str]:
    # Example naming: PUBPC-01 .. PUBPC-30
    return [f"PUBPC-{i:02d}" for i in range(1, n + 1)]


def choose_bad_actors(device_ids: List[str]) -> Dict[str, str]:
    """
    Assign specific failure modes to a few devices so the dashboard has interesting data.
    Returns: device_id -> mode
    """
    modes = [
        "low_disk_red",
        "av_disabled_red",
        "dns_fail_red",
        "gateway_fail_red",
        "crashy_yellow",
        "mypc_connect_yellow",
        "mypc_auth_fail_yellow",
        "slow_auth_yellow",
    ]
    random.shuffle(device_ids)
    chosen = device_ids[: len(modes)]
    return {dev: mode for dev, mode in zip(chosen, modes)}


def base_metrics(device_id: str) -> Dict:
    uptime = random.randint(300, 7 * 24 * 3600)  # 5 min to 7 days
    disk_free_pct = random.uniform(25, 85)
    disk_free_gb = random.uniform(30, 250)

    av_enabled = True
    sig_age = random.randint(0, 3)
    pending_reboot = random.random() < 0.1

    dns_ok = True
    gateway_ok = True
    backend_reachable = True

    unexpected_shutdowns = 0
    app_crashes = random.randint(0, 1)
    service_restarts = random.randint(0, 1)

    # MyPC: mostly healthy baseline
    mypc_client_running = True
    attempts = random.randint(0, 8)
    failures = random.randint(0, min(2, attempts))
    successes = max(0, attempts - failures)

    failures_by_reason = {}
    if failures > 0:
        failures_by_reason["invalid_credentials"] = failures

    connect_failures = 0
    time_to_ready_s = None
    last_err_cat = None

    avg_auth_ms = None
    p95_auth_ms = None
    slow_login_count = None

    return {
        "device_id": device_id,
        "timestamp_utc": utc_now(),
        "agent_version": "sim-0.1.0",
        "ip_address": f"10.0.10.{random.randint(10, 240)}",
        "location_tag": random.choice(LOCATION_TAGS),
        "metrics": {
            "availability": {
                "last_boot_utc": boot_time(uptime),
                "uptime_seconds": uptime,
            },
            "stability": {
                "unexpected_shutdowns": unexpected_shutdowns,
                "app_crashes": app_crashes,
                "service_restarts": service_restarts,
                "hang_indicators": None,
            },
            "storage": {
                "disk_c_free_gb": round(disk_free_gb, 1),
                "disk_c_free_pct": round(disk_free_pct, 1),
                "disk_errors": None,
                "profile_errors": None,
            },
            "security": {
                "av_enabled": av_enabled,
                "av_sig_age_days": sig_age,
                "pending_reboot": pending_reboot,
                "update_failures": None,
            },
            "network": {
                "dns_ok": dns_ok,
                "gateway_ok": gateway_ok,
                "backend_reachable": backend_reachable,
                "network_resets": None,
            },
            "mypc": {
                "client_running": mypc_client_running,
                "auth": {
                    "attempts": attempts,
                    "successes": successes,
                    "failures": failures,
                    "failures_by_reason": failures_by_reason,
                },
                "connectivity": {
                    "service_connect_failures": connect_failures,
                    "time_to_service_ready_s": time_to_ready_s,
                    "last_error_category": last_err_cat,
                },
                "login_perf": {
                    "avg_auth_ms": avg_auth_ms,
                    "p95_auth_ms": p95_auth_ms,
                    "slow_login_count": slow_login_count,
                },
            },
        },
    }


def apply_mode(payload: Dict, mode: str) -> Dict:
    m = payload["metrics"]

    if mode == "low_disk_red":
        m["storage"]["disk_c_free_pct"] = 6.5
        m["storage"]["disk_c_free_gb"] = 3.2

    elif mode == "av_disabled_red":
        m["security"]["av_enabled"] = False

    elif mode == "dns_fail_red":
        m["network"]["dns_ok"] = False

    elif mode == "gateway_fail_red":
        m["network"]["gateway_ok"] = False

    elif mode == "crashy_yellow":
        m["stability"]["app_crashes"] = 4
        m["stability"]["service_restarts"] = 3

    elif mode == "mypc_connect_yellow":
        m["mypc"]["connectivity"]["service_connect_failures"] = random.randint(1, 3)
        m["mypc"]["connectivity"]["last_error_category"] = "service_unreachable"
        # sometimes backend not reachable too
        m["network"]["backend_reachable"] = False

    elif mode == "mypc_auth_fail_yellow":
        attempts = random.randint(12, 30)
        failures = random.randint(int(attempts * 0.5), int(attempts * 0.9))
        successes = attempts - failures
        m["mypc"]["auth"]["attempts"] = attempts
        m["mypc"]["auth"]["failures"] = failures
        m["mypc"]["auth"]["successes"] = successes
        m["mypc"]["auth"]["failures_by_reason"] = {
            "timeout": random.randint(0, failures),
            "backend_unreachable": random.randint(0, failures),
            "invalid_credentials": random.randint(0, failures),
        }

    elif mode == "slow_auth_yellow":
        attempts = random.randint(8, 20)
        failures = random.randint(0, 3)
        successes = attempts - failures
        m["mypc"]["auth"]["attempts"] = attempts
        m["mypc"]["auth"]["failures"] = failures
        m["mypc"]["auth"]["successes"] = successes
        m["mypc"]["login_perf"]["avg_auth_ms"] = round(random.uniform(1200, 4500), 1)
        m["mypc"]["login_perf"]["p95_auth_ms"] = round(random.uniform(6000, 15000), 1)
        m["mypc"]["login_perf"]["slow_login_count"] = random.randint(1, 5)

    return payload


def post_checkin(payload: Dict) -> None:
    headers = {"X-API-Key": API_KEY}
    r = requests.post(API_URL, json=payload, headers=headers, timeout=5)
    if r.status_code != 200:
        print(f"[{payload['device_id']}] ERROR {r.status_code}: {r.text}")
    else:
        out = r.json()
        print(f"[{payload['device_id']}] {out.get('computed_status')} {out.get('reasons')}")


def main() -> None:
    device_ids = make_device_ids(FLEET_SIZE)
    bad_map = choose_bad_actors(device_ids)

    print("Simulator starting...")
    print(f"API_URL: {API_URL}")
    print(f"Fleet size: {FLEET_SIZE}")
    print("Bad actors:")
    for dev, mode in bad_map.items():
        print(f"  - {dev}: {mode}")

    while True:
        # each loop sends one check-in per device (with small jitter)
        for dev in device_ids:
            payload = base_metrics(dev)
            if dev in bad_map:
                payload = apply_mode(payload, bad_map[dev])

            # slight variability each cycle
            if random.random() < 0.05:
                payload["metrics"]["security"]["pending_reboot"] = True
            if random.random() < 0.05:
                payload["metrics"]["storage"]["disk_c_free_pct"] = round(
                    max(1.0, payload["metrics"]["storage"]["disk_c_free_pct"] - random.uniform(1, 5)), 1
                )

            post_checkin(payload)
            time.sleep(random.uniform(0.05, 0.20))

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

