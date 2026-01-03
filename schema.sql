PRAGMA foreign_keys = ON;

-- =========================
-- Devices table
-- One row per public PC
-- =========================
CREATE TABLE IF NOT EXISTS devices (
  device_id TEXT PRIMARY KEY,
  location_tag TEXT,
  last_ip TEXT,
  first_seen_utc TEXT,
  last_seen_utc TEXT
);

-- =========================
-- Check-ins table
-- Time-series health data
-- =========================
CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL,
  timestamp_utc TEXT NOT NULL,
  agent_version TEXT NOT NULL,

  -- Availability
  last_boot_utc TEXT NOT NULL,
  uptime_seconds INTEGER NOT NULL,

  -- Stability
  unexpected_shutdowns INTEGER NOT NULL,
  app_crashes INTEGER NOT NULL,
  service_restarts INTEGER NOT NULL,
  hang_indicators INTEGER,

  -- Storage
  disk_c_free_gb REAL NOT NULL,
  disk_c_free_pct REAL NOT NULL,
  disk_errors INTEGER,
  profile_errors INTEGER,

  -- Security
  av_enabled INTEGER NOT NULL,
  av_sig_age_days INTEGER NOT NULL,
  pending_reboot INTEGER NOT NULL,
  update_failures INTEGER,

  -- Network
  dns_ok INTEGER NOT NULL,
  gateway_ok INTEGER NOT NULL,
  backend_reachable INTEGER,
  network_resets INTEGER,

  -- MyPC client status
  mypc_client_running INTEGER,

  -- MyPC authentication metrics
  mypc_auth_attempts INTEGER NOT NULL,
  mypc_auth_successes INTEGER NOT NULL,
  mypc_auth_failures INTEGER NOT NULL,
  mypc_auth_failures_by_reason_json TEXT NOT NULL,

  -- MyPC connectivity metrics
  mypc_service_connect_failures INTEGER NOT NULL,
  mypc_time_to_service_ready_s REAL,
  mypc_last_error_category TEXT,

  -- MyPC login performance
  mypc_avg_auth_ms REAL,
  mypc_p95_auth_ms REAL,
  mypc_slow_login_count INTEGER,

  -- Server-computed health
  computed_status TEXT,
  computed_reasons_json TEXT,

  -- Optional raw payload (NO PII)
  raw_json TEXT,

  FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- =========================
-- Indexes for performance
-- =========================
CREATE INDEX IF NOT EXISTS idx_checkins_device_time
  ON checkins(device_id, timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_checkins_time
  ON checkins(timestamp_utc);

