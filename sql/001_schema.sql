-- GeoTrack serving schema. Execute inside PostgreSQL/PostGIS/MobilityDB.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS mobilitydb;

-- Versioned serving batches. A batch is only exposed after validation by
-- updating the one-row current_run pointer in the same transaction.
CREATE TABLE IF NOT EXISTS batch_runs (
  run_id TEXT PRIMARY KEY,
  dataset TEXT NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('staging', 'validated', 'published', 'failed')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  manifest_uri TEXT,
  counts JSONB NOT NULL DEFAULT '{}'::jsonb,
  quality JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_batch_runs_status_time
  ON batch_runs (status, started_at DESC);

CREATE TABLE IF NOT EXISTS current_run (
  singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
  run_id TEXT REFERENCES batch_runs(run_id),
  published_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS users (
  run_id TEXT NOT NULL REFERENCES batch_runs(run_id),
  user_id TEXT NOT NULL,
  trajectory_count INTEGER NOT NULL,
  point_count BIGINT NOT NULL,
  distance_m DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (run_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_users_run_distance ON users (run_id, distance_m DESC);

CREATE TABLE IF NOT EXISTS trajectory_points (
  run_id TEXT NOT NULL DEFAULT 'legacy',
  user_id TEXT NOT NULL,
  trajectory_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  ts TIMESTAMPTZ NOT NULL,
  latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  altitude_m DOUBLE PRECISION,
  geom geometry(Point, 4326) GENERATED ALWAYS AS (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
  ) STORED,
  PRIMARY KEY (trajectory_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_points_user_ts ON trajectory_points (user_id, ts);
CREATE INDEX IF NOT EXISTS idx_points_geom ON trajectory_points USING GIST (geom);

CREATE TABLE IF NOT EXISTS trajectories (
  run_id TEXT NOT NULL DEFAULT 'legacy',
  trajectory_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  start_ts TIMESTAMPTZ NOT NULL,
  end_ts TIMESTAMPTZ NOT NULL,
  point_count INTEGER NOT NULL,
  distance_m DOUBLE PRECISION NOT NULL,
  duration_s DOUBLE PRECISION NOT NULL,
  geom geometry(LineString, 4326),
  temporal_geom tgeompoint,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trajectories_user_time ON trajectories (user_id, start_ts, end_ts);
CREATE INDEX IF NOT EXISTS idx_trajectories_geom ON trajectories USING GIST (geom);

-- Upgrade databases created by the original demo schema.  PostgreSQL's
-- ``ADD COLUMN IF NOT EXISTS`` keeps this file safe to run repeatedly.
ALTER TABLE trajectory_points ADD COLUMN IF NOT EXISTS run_id TEXT;
UPDATE trajectory_points SET run_id = 'legacy' WHERE run_id IS NULL;
ALTER TABLE trajectory_points ALTER COLUMN run_id SET DEFAULT 'legacy';
ALTER TABLE trajectory_points ALTER COLUMN run_id SET NOT NULL;
ALTER TABLE trajectories ADD COLUMN IF NOT EXISTS run_id TEXT;
UPDATE trajectories SET run_id = 'legacy' WHERE run_id IS NULL;
ALTER TABLE trajectories ALTER COLUMN run_id SET DEFAULT 'legacy';
ALTER TABLE trajectories ALTER COLUMN run_id SET NOT NULL;
ALTER TABLE trajectory_points DROP CONSTRAINT IF EXISTS trajectory_points_pkey;
ALTER TABLE trajectory_points ADD CONSTRAINT trajectory_points_pkey PRIMARY KEY (run_id, trajectory_id, seq);
ALTER TABLE stay_points DROP CONSTRAINT IF EXISTS stay_points_trajectory_id_start_ts_end_ts_key;
CREATE INDEX IF NOT EXISTS idx_points_run_user_ts ON trajectory_points (run_id, user_id, ts);
CREATE INDEX IF NOT EXISTS idx_trajectories_run_user_time
  ON trajectories (run_id, user_id, start_ts, end_ts);

CREATE TABLE IF NOT EXISTS stay_points (
  stay_id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL DEFAULT 'legacy',
  user_id TEXT NOT NULL,
  trajectory_id TEXT NOT NULL REFERENCES trajectories(trajectory_id),
  start_ts TIMESTAMPTZ NOT NULL,
  end_ts TIMESTAMPTZ NOT NULL,
  duration_s DOUBLE PRECISION NOT NULL,
  center_geom geometry(Point, 4326) NOT NULL,
  radius_m DOUBLE PRECISION NOT NULL
);

ALTER TABLE stay_points ADD COLUMN IF NOT EXISTS run_id TEXT;
UPDATE stay_points SET run_id = 'legacy' WHERE run_id IS NULL;
ALTER TABLE stay_points ALTER COLUMN run_id SET DEFAULT 'legacy';
ALTER TABLE stay_points ALTER COLUMN run_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stays_run_time ON stay_points (run_id, start_ts, end_ts);

CREATE INDEX IF NOT EXISTS idx_stays_geom ON stay_points USING GIST (center_geom);
CREATE INDEX IF NOT EXISTS idx_stays_time ON stay_points (start_ts, end_ts);
CREATE UNIQUE INDEX IF NOT EXISTS uq_stays_trajectory_window ON stay_points (trajectory_id, start_ts, end_ts);

CREATE TABLE IF NOT EXISTS hotspots (
  hotspot_id TEXT PRIMARY KEY,
  center_geom geometry(Point, 4326) NOT NULL,
  geometry geometry(Geometry, 4326) NOT NULL,
  visit_count INTEGER NOT NULL,
  unique_users INTEGER NOT NULL,
  avg_dwell_s DOUBLE PRECISION NOT NULL,
  peak_hour SMALLINT NOT NULL CHECK (peak_hour BETWEEN 0 AND 23),
  weekday_ratio DOUBLE PRECISION NOT NULL,
  algorithm TEXT NOT NULL,
  run_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_hotspots_geom ON hotspots USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_hotspots_run_users ON hotspots (run_id, unique_users DESC, visit_count DESC);

CREATE TABLE IF NOT EXISTS temporal_patterns (
  pattern_id TEXT PRIMARY KEY,
  cluster_id INTEGER NOT NULL,
  label TEXT NOT NULL,
  user_count INTEGER NOT NULL,
  avg_trip_count DOUBLE PRECISION NOT NULL,
  avg_distance_m DOUBLE PRECISION NOT NULL,
  avg_duration_s DOUBLE PRECISION NOT NULL,
  hourly_profile JSONB NOT NULL,
  weekday_ratio DOUBLE PRECISION NOT NULL,
  run_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_temporal_patterns_run_cluster
  ON temporal_patterns (run_id, cluster_id);

CREATE TABLE IF NOT EXISTS pipeline_jobs (
  job_id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  error_message TEXT
);
