from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.models import CheckinPayload
from app.db import init_db, upsert_device, insert_checkin, get_devices_latest, get_device_detail
from app.health_rules import classify


# -------------------------
# MVP API key (replace later with env var)
# -------------------------
API_KEY = "dev-secret-key"

# schema.sql lives in project root
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"

app = FastAPI(title="Public PC Monitoring Dashboard API", version="0.1.0")

DEVICE_PAGE_PATH = Path(__file__).resolve().parent.parent / "static" / "device.html"

DASHBOARD_PATH = Path (__file__).resolve().parent.parent / "static" / "dashboard.html"


@app.on_event("startup")
def startup() -> None:
    # Initialize SQLite database and tables
    init_db(SCHEMA_PATH)


def require_api_key(x_api_key: Optional[str]) -> None:
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health() -> dict:
    return {"ok": True}

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
def dashboard():
    return FileResponse(DASHBOARD_PATH)

@app.get("/device")
def device_page():
    return FileResponse(DEVICE_PAGE_PATH)

@app.post("/api/checkin")
def post_checkin(payload: CheckinPayload, x_api_key: Optional[str] = Header(default=None)) -> dict:
    require_api_key(x_api_key)

    d = payload.model_dump()
    device_id = d["device_id"]
    ts = d["timestamp_utc"]
    m = d["metrics"]

    # Flatten payload into DB row that matches schema.sql columns
    row = {
        "device_id": device_id,
        "timestamp_utc": ts,
        "agent_version": d["agent_version"],

        # Availability
        "last_boot_utc": m["availability"]["last_boot_utc"],
        "uptime_seconds": m["availability"]["uptime_seconds"],

        # Stability
        "unexpected_shutdowns": m["stability"]["unexpected_shutdowns"],
        "app_crashes": m["stability"]["app_crashes"],
        "service_restarts": m["stability"]["service_restarts"],
        "hang_indicators": m["stability"].get("hang_indicators"),

        # Storage
        "disk_c_free_gb": m["storage"]["disk_c_free_gb"],
        "disk_c_free_pct": m["storage"]["disk_c_free_pct"],
        "disk_errors": m["storage"].get("disk_errors"),
        "profile_errors": m["storage"].get("profile_errors"),

        # Security
        "av_enabled": 1 if m["security"]["av_enabled"] else 0,
        "av_sig_age_days": m["security"]["av_sig_age_days"],
        "pending_reboot": 1 if m["security"]["pending_reboot"] else 0,
        "update_failures": m["security"].get("update_failures"),

        # Network
        "dns_ok": 1 if m["network"]["dns_ok"] else 0,
        "gateway_ok": 1 if m["network"]["gateway_ok"] else 0,
        "backend_reachable": None
        if m["network"].get("backend_reachable") is None
        else (1 if m["network"]["backend_reachable"] else 0),
        "network_resets": m["network"].get("network_resets"),

        # MyPC
        "mypc_client_running": None
        if m["mypc"].get("client_running") is None
        else (1 if m["mypc"]["client_running"] else 0),

        "mypc_auth_attempts": m["mypc"]["auth"]["attempts"],
        "mypc_auth_successes": m["mypc"]["auth"]["successes"],
        "mypc_auth_failures": m["mypc"]["auth"]["failures"],
        "mypc_auth_failures_by_reason_json": json.dumps(
            m["mypc"]["auth"]["failures_by_reason"], ensure_ascii=False
        ),

        "mypc_service_connect_failures": m["mypc"]["connectivity"]["service_connect_failures"],
        "mypc_time_to_service_ready_s": m["mypc"]["connectivity"].get("time_to_service_ready_s"),
        "mypc_last_error_category": m["mypc"]["connectivity"].get("last_error_category"),

        "mypc_avg_auth_ms": m["mypc"]["login_perf"].get("avg_auth_ms"),
        "mypc_p95_auth_ms": m["mypc"]["login_perf"].get("p95_auth_ms"),
        "mypc_slow_login_count": m["mypc"]["login_perf"].get("slow_login_count"),

        # Optional raw payload (NO PII!)
        "raw_json": json.dumps(d, ensure_ascii=False),
    }

    computed_status, reasons = classify(row)
    row["computed_status"] = computed_status
    row["computed_reasons_json"] = json.dumps(reasons, ensure_ascii=False)

    # Update devices table (first_seen_utc passed but only used on insert)
    upsert_device(
        device_id=device_id,
        location_tag=d.get("location_tag"),
        ip=d.get("ip_address"),
        first_seen_utc=ts,
        last_seen_utc=ts,
    )

    checkin_id = insert_checkin(row)

    return {
        "ok": True,
        "checkin_id": checkin_id,
        "computed_status": computed_status,
        "reasons": reasons,
    }


@app.get("/api/devices")
def list_devices(x_api_key: Optional[str] = Header(default=None)) -> dict:
    require_api_key(x_api_key)
    return {"devices": get_devices_latest()}


@app.get("/api/devices/{device_id}")
def device_detail(device_id: str, limit: int = 20, x_api_key: Optional[str] = Header(default=None)) -> dict:
    require_api_key(x_api_key)
    return get_device_detail(device_id, limit=limit)

