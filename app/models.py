from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field


# -------------------------
# Availability & uptime
# -------------------------
class Availability(BaseModel):
    last_boot_utc: str
    uptime_seconds: int = Field(ge=0)


# -------------------------
# System stability
# -------------------------
class Stability(BaseModel):
    unexpected_shutdowns: int = Field(ge=0)
    app_crashes: int = Field(ge=0)
    service_restarts: int = Field(ge=0)
    hang_indicators: Optional[int] = Field(default=None, ge=0)


# -------------------------
# Storage & profile health
# -------------------------
class Storage(BaseModel):
    disk_c_free_gb: float = Field(ge=0)
    disk_c_free_pct: float = Field(ge=0, le=100)
    disk_errors: Optional[int] = Field(default=None, ge=0)
    profile_errors: Optional[int] = Field(default=None, ge=0)


# -------------------------
# Security & updates
# -------------------------
class Security(BaseModel):
    av_enabled: bool
    av_sig_age_days: int = Field(ge=0)
    pending_reboot: bool
    update_failures: Optional[int] = Field(default=None, ge=0)


# -------------------------
# Network health
# -------------------------
class Network(BaseModel):
    dns_ok: bool
    gateway_ok: bool
    backend_reachable: Optional[bool] = None
    network_resets: Optional[int] = Field(default=None, ge=0)


# -------------------------
# MyPC authentication
# -------------------------
class MyPCAuth(BaseModel):
    attempts: int = Field(ge=0)
    successes: int = Field(ge=0)
    failures: int = Field(ge=0)
    failures_by_reason: Dict[str, int] = Field(default_factory=dict)


# -------------------------
# MyPC connectivity
# -------------------------
class MyPCConnectivity(BaseModel):
    service_connect_failures: int = Field(ge=0)
    time_to_service_ready_s: Optional[float] = Field(default=None, ge=0)
    last_error_category: Optional[str] = None


# -------------------------
# MyPC login performance
# -------------------------
class MyPCLoginPerf(BaseModel):
    avg_auth_ms: Optional[float] = Field(default=None, ge=0)
    p95_auth_ms: Optional[float] = Field(default=None, ge=0)
    slow_login_count: Optional[int] = Field(default=None, ge=0)


# -------------------------
# MyPC block
# -------------------------
class MyPC(BaseModel):
    client_running: Optional[bool] = None
    auth: MyPCAuth
    connectivity: MyPCConnectivity
    login_perf: MyPCLoginPerf


# -------------------------
# Metrics root
# -------------------------
class Metrics(BaseModel):
    availability: Availability
    stability: Stability
    storage: Storage
    security: Security
    network: Network
    mypc: MyPC


# -------------------------
# Check-in payload
# -------------------------
class CheckinPayload(BaseModel):
    device_id: str
    timestamp_utc: str
    agent_version: str
    ip_address: Optional[str] = None
    location_tag: Optional[str] = None
    metrics: Metrics

