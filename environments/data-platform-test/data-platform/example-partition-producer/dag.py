"""Producer: scans the landing prefix and emits one partitioned asset event per new or changed file."""

import datetime
import json
import re

try:
    from airflow.sdk import DAG, Asset, PartitionedAtRuntime, Variable, task

    FEEDS = ("receptions", "releases", "empty_cells")
    ASSETS = {
        feed: Asset(
            name=f"prison_{feed}",
            uri=f"s3://mojdp-test-mwaa/asset-partition-demo/landing/{feed}",
        )
        for feed in FEEDS
    }
    ASSET_SCHEDULE = PartitionedAtRuntime()
except ImportError:
    from airflow.decorators import task
    from airflow.models import DAG, Variable

    FEEDS = ()
    ASSETS = {}
    ASSET_SCHEDULE = None

PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
OWNER = "PLACEHOLDER_OWNER"

BUCKET = "mojdp-test-mwaa"
LANDING = "asset-partition-demo/landing/"
SEEN_VARIABLE = "asset_partition_demo_seen"
KEY_RE = re.compile(
    r"landing/(?P<feed>[a-z_]+)/prison=(?P<prison>[^/]+)/dt=(?P<day>[\d-]+)/hour=(?P<hour>\d{2})/data\.csv$"
)

with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args={"owner": OWNER},
    start_date=datetime.datetime(2025, 1, 1),
    schedule=ASSET_SCHEDULE,
    catchup=False,
    is_paused_upon_creation=False,
    params={"prison": "", "day": "", "reset_seen": False},
    tags=["example", "asset", "partition"],
) as dag:

    @task(outlets=list(ASSETS.values()))
    def scan(*, params=None, outlet_events=None):
        import boto3

        seen = {} if params.get("reset_seen") else Variable.get(SEEN_VARIABLE, default={}, deserialize_json=True)
        emitted = []

        paginator = boto3.client("s3").get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BUCKET, Prefix=LANDING):
            for obj in page.get("Contents", []):
                key, etag = obj["Key"], obj["ETag"]
                match = KEY_RE.search(key)
                if not match or match["feed"] not in ASSETS:
                    continue
                if params.get("prison") and match["prison"] != params["prison"]:
                    continue
                if params.get("day") and match["day"] != params["day"]:
                    continue
                if seen.get(key) == etag:
                    continue
                partition_key = f"{match['prison']}|{match['day']}T{match['hour']}:00:00"
                outlet_events[ASSETS[match["feed"]]].add_partitions(partition_key)
                seen[key] = etag
                emitted.append((match["feed"], partition_key))

        Variable.set(SEEN_VARIABLE, seen, serialize_json=True)
        print(f"emitted {len(emitted)} partition events")
        for feed, partition_key in emitted:
            print(f"  {feed}: {partition_key}")

    scan()
