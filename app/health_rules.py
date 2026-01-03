from __future__ import annotations

from typing import Dict, List, Tuple


def classify(checkin_row: Dict) -> Tuple[str, List[str]]:
    """
    Classify a check-in row into a health state and human-readable reasons.

    Returns:
      computed_status: 'green' | 'yellow' | 'red'
      reasons: list[str]
    """
    reasons: List[str] = []
    status = "green"

    # -------------------------
    # Storage rules
    # -------------------------
    disk_pct = float(checkin_row["disk_c_free_pct"])
    if disk_pct < 10:
        status = "red"
        reasons.append("Low disk space (<10%)")
    elif disk_pct < 20 and status != "red":
        status = "yellow"
        reasons.append("Disk space warning (<20%)")

    # Optional disk/profile error signals (if you populate them)
    disk_errors = checkin_row.get("disk_errors")
    if disk_errors is not None and int(disk_errors) > 0 and status != "red":
        status = "yellow"
        reasons.append("Disk errors detected")

    profile_errors = checkin_row.get("profile_errors")
    if profile_errors is not None and int(profile_errors) > 0 and status != "red":
        status = "yellow"
        reasons.append("Profile errors detected")

    # -------------------------
    # Security rules
    # -------------------------
    if not bool(checkin_row["av_enabled"]):
        status = "red"
        reasons.append("Antivirus disabled")

    sig_age = int(checkin_row["av_sig_age_days"])
    if sig_age > 7 and status != "red":
        status = "yellow"
        reasons.append("AV definitions out of date (>7 days)")

    if bool(checkin_row["pending_reboot"]) and status != "red":
        status = "yellow"
        reasons.append("Pending reboot")

    update_failures = checkin_row.get("update_failures")
    if update_failures is not None and int(update_failures) > 0 and status != "red":
        status = "yellow"
        reasons.append("Windows Update failures detected")

    # -------------------------
    # Network rules
    # -------------------------
    if not bool(checkin_row["dns_ok"]):
        status = "red"
        reasons.append("DNS check failed")

    if not bool(checkin_row["gateway_ok"]):
        status = "red"
        reasons.append("Gateway unreachable")

    backend_reachable = checkin_row.get("backend_reachable")
    if backend_reachable is not None and int(backend_reachable) == 0 and status != "red":
        status = "yellow"
        reasons.append("Auth backend not reachable")

    network_resets = checkin_row.get("network_resets")
    if network_resets is not None and int(network_resets) > 0 and status != "red":
        status = "yellow"
        reasons.append("Network adapter resets detected")

    # -------------------------
    # Stability rules
    # -------------------------
    if int(checkin_row["unexpected_shutdowns"]) > 0:
        status = "red"
        reasons.append("Unexpected shutdown detected")

    # Crash thresholds can be tuned later; keep reasonable defaults
    if int(checkin_row["app_crashes"]) >= 3 and status != "red":
        status = "yellow"
        reasons.append("High application crash count")

    if int(checkin_row["service_restarts"]) >= 3 and status != "red":
        status = "yellow"
        reasons.append("High service restart count")

    hang = checkin_row.get("hang_indicators")
    if hang is not None and int(hang) > 0 and status != "red":
        status = "yellow"
        reasons.append("Hang indicators detected")

    # -------------------------
    # MyPC rules (generic)
    # -------------------------
    if int(checkin_row["mypc_service_connect_failures"]) > 0 and status != "red":
        status = "yellow"
        reasons.append("MyPC service connectivity failures")

    attempts = int(checkin_row["mypc_auth_attempts"])
    failures = int(checkin_row["mypc_auth_failures"])
    if attempts >= 10:
        fail_rate = failures / max(attempts, 1)
        if fail_rate >= 0.5 and status != "red":
            status = "yellow"
            reasons.append("High MyPC auth failure rate (>=50%)")

    # Slow auth signal (if present)
    slow_count = checkin_row.get("mypc_slow_login_count")
    if slow_count is not None and int(slow_count) > 0 and status != "red":
        status = "yellow"
        reasons.append("Slow MyPC authentication events")

    return status, reasons

