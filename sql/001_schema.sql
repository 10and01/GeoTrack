-- GeoTrack serving schema. Execute inside PostgreSQL/PostGIS/MobilityDB.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS mobilitydb;

CREATE TABLE IF NOT EXISTS trajectory_points (
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

CREATE TABLE IF NOT EXISTS stay_points (
  stay_id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  trajectory_id TEXT NOT NULL REFERENCES trajectories(trajectory_id),
  start_ts TIMESTAMPTZ NOT NULL,
  end_ts TIMESTAMPTZ NOT NULL,
  duration_s DOUBLE PRECISION NOT NULL,
  center_geom geometry(Point, 4326) NOT NULL,
  radius_m DOUBLE PRECISION NOT NULL
);

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

CREATE TABLE IF NOT EXISTS pipeline_jobs (
  job_id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  error_message TEXT
);
