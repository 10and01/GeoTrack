.PHONY: up down ingest mine test demo

up:
	docker compose up -d

down:
	docker compose down

ingest:
	python jobs/run_pipeline.py --data-root "Geolife Trajectories 1.3/Data" --max-trajectories 120 --max-points 60000

mine:
	python jobs/run_pipeline.py --data-root "Geolife Trajectories 1.3/Data" --max-trajectories 120 --max-points 60000 --mine-only

test:
	python -m unittest discover -s tests -v

demo:
	python jobs/run_pipeline.py --data-root "Geolife Trajectories 1.3/Data" --max-trajectories 120 --max-points 60000

