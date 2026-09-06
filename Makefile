.PHONY: up down ingest mine full-summary full-ingest full-spark test demo acceptance

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

# Run this in a Spark/HDFS client or Docker batch container.
full-spark:
	python jobs/spark_distributed.py --input "Geolife Trajectories 1.3/Data/*/Trajectory/*.plt" --output data/processed/full-points --quality-output data/processed/full-quality

test:
	python -m unittest discover -s tests -v

acceptance:
	python -m unittest discover -s tests -v
	python jobs/check_serving_payload.py --input data/processed/demo.json
	python jobs/load_serving_tables.py --input data/processed/demo.json --dry-run
	docker compose config
	npm --prefix frontend run build

