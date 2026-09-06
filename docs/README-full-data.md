# Full-data quick reference

Run `python jobs/full_summary.py --data-root "Geolife Trajectories 1.3/Data" --output data/processed/full-manifest.json` for the local bounded-memory scan. The manifest records the real full-data counts while `demo.json` remains a bounded presentation subset. Use `scripts/full_data.ps1 -Mode spark` or `jobs/spark_distributed.py` only when Spark/HDFS is available.
