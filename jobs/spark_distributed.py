"""Distributed GeoLife ingestion job for the HDFS + Spark layer.

The regular ``run_pipeline.py`` keeps the demo runnable without PySpark. This
entry point is used in Docker or a real Spark cluster and writes cleaned point
records as partitioned Parquet. The input may be a local glob or an HDFS URI,
for example ``hdfs:///geotrack/raw/Data/*/Trajectory/*.plt``.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath


def _parse_file(item: tuple[str, str]):
    path, content = item
    parts = PurePosixPath(path.split("?", 1)[0]).parts
    try:
        trajectory_name = PurePosixPath(path).stem
        trajectory_index = next(index for index, part in enumerate(parts) if part == "Trajectory")
        user_id = parts[trajectory_index - 1]
    except (StopIteration, IndexError):
        user_id = "unknown"
        trajectory_name = PurePosixPath(path).stem
    trajectory_id = f"{user_id}_{trajectory_name}"
    reader = csv.reader(io.StringIO(content))
    for _ in range(6):
        next(reader, None)
    previous = None
    seq = 0
    for row in reader:
        if len(row) < 7:
            continue
        try:
            latitude = float(row[0])
            longitude = float(row[1])
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                continue
            timestamp = datetime.strptime(f"{row[5]} {row[6]}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            altitude_ft = float(row[3])
            altitude_m = None if altitude_ft <= -777 else round(altitude_ft * 0.3048, 2)
        except (TypeError, ValueError):
            continue
        point_key = (timestamp, latitude, longitude)
        if point_key == previous:
            continue
        previous = point_key
        yield {
            "user_id": user_id,
            "trajectory_id": trajectory_id,
            "seq": seq,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "latitude": latitude,
            "longitude": longitude,
            "altitude_m": altitude_m,
        }
        seq += 1


def main() -> None:
    parser = argparse.ArgumentParser(description="GeoTrack Spark PLT to Parquet ingestion")
    parser.add_argument("--input", required=True, help="Local or HDFS PLT glob")
    parser.add_argument("--output", required=True, help="Parquet output directory")
    parser.add_argument("--quality-output", default=None, help="Optional JSON quality report path")
    parser.add_argument("--partitions", type=int, default=8)
    args = parser.parse_args()
    try:
        from pyspark.sql import SparkSession, functions as F, types as T
    except ImportError as error:  # pragma: no cover - exercised in Spark image
        raise SystemExit("PySpark is required for distributed ingestion; use jobs/run_pipeline.py for local demo mode") from error

    spark = SparkSession.builder.appName("GeoTrack-PLT-Ingest").getOrCreate()
    schema = T.StructType(
        [
            T.StructField("user_id", T.StringType(), False),
            T.StructField("trajectory_id", T.StringType(), False),
            T.StructField("seq", T.IntegerType(), False),
            T.StructField("timestamp", T.StringType(), False),
            T.StructField("latitude", T.DoubleType(), False),
            T.StructField("longitude", T.DoubleType(), False),
            T.StructField("altitude_m", T.DoubleType(), True),
        ]
    )
    records = spark.sparkContext.wholeTextFiles(args.input, minPartitions=max(1, args.partitions)).flatMap(_parse_file)
    points = spark.createDataFrame(records, schema=schema).withColumn("timestamp", F.to_timestamp("timestamp"))
    points = points.repartition("user_id").sortWithinPartitions("trajectory_id", "timestamp", "seq")
    points.write.mode("overwrite").partitionBy("user_id").parquet(args.output)

    quality = {
        "valid_points": points.count(),
        "trajectory_count": points.select("trajectory_id").distinct().count(),
        "user_count": points.select("user_id").distinct().count(),
        "output": args.output,
    }
    if args.quality_output:
        spark.sparkContext.parallelize([json.dumps(quality, ensure_ascii=False)]).coalesce(1).saveAsTextFile(args.quality_output)
    print(json.dumps(quality, ensure_ascii=False))
    spark.stop()


if __name__ == "__main__":
    main()
