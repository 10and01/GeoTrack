.PHONY: up down ingest mine full-summary full-ingest full-spark full-load full-index test demo acceptance

up:
	docker compose up -d

down:
	docker compose down

ingest:
	python jobs/run_pipeline.py --data-root "Geolife Trajectories 1.3/Data" --max-trajectories 120 --max-points 60000

mine:
	python jobs/run_pipeline.py --data-root "Geolife Trajectories 1.3/Data" --max-trajectories 120 --max-points 60000 --mine-only

demo:
	python jobs/run_pipeline.py --data-root "Geolife Trajectories 1.3/Data" --max-trajectories 120 --max-points 60000

# Full data path: bounded-memory manifest, isolated from demo.json.
full-summary:
	python jobs/full_summary.py --data-root "Geolife Trajectories 1.3/Data" --output data/processed/full-manifest.json

full-ingest: full-summary
	python jobs/spark_full_pipeline.py --input "Geolife Trajectories 1.3/Data/*/Trajectory/*.plt" --output-root data/processed/full-curated --manifest data/processed/full-manifest.json

full-index:
	python jobs/full_serving_index.py --data-root "Geolife Trajectories 1.3/Data" --output data/processed/full-serving.sqlite --sample-points 200

# Run this in a Spark/HDFS client or Docker batch container.
full-spark:
	python jobs/spark_full_pipeline.py --input "Geolife Trajectories 1.3/Data/*/Trajectory/*.plt" --output-root data/processed/full-curated --manifest data/processed/full-manifest.json

full-load:
	python jobs/load_full_serving.py --input-root data/processed/full-curated --manifest-uri data/processed/full-manifest.json --dsn "$${DATABASE_URL:-postgresql://geotrack:geotrack@localhost:5432/geotrack}"

test:
	python -m unittest discover -s tests -v

acceptance:
	python -m unittest discover -s tests -v
	python jobs/check_serving_payload.py --input data/processed/demo.json
	python jobs/load_serving_tables.py --input data/processed/demo.json --dry-run
	docker compose config
	npm --prefix frontend run build
