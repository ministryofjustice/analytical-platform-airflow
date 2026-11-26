"""Hourly: runs when receptions, releases and empty_cells all exist for a prison and hour."""

import datetime

try:
    from airflow.sdk import (
        DAG,
        Asset,
        IdentityMapper,
        PartitionedAssetTimetable,
        ProductMapper,
        StartOfHourMapper,
    )

    BASE_URI = "s3://mojdp-test-mwaa/asset-partition-demo"
    RECEPTIONS = Asset(name="prison_receptions", uri=f"{BASE_URI}/landing/receptions")
    RELEASES = Asset(name="prison_releases", uri=f"{BASE_URI}/landing/releases")
    EMPTY_CELLS = Asset(name="prison_empty_cells", uri=f"{BASE_URI}/landing/empty_cells")
    HOURLY_SUMMARY = Asset(name="prison_hourly_summary", uri=f"{BASE_URI}/summaries/hourly")

    ASSET_SCHEDULE = PartitionedAssetTimetable(
        assets=RECEPTIONS & RELEASES & EMPTY_CELLS,
        default_partition_mapper=ProductMapper(IdentityMapper(), StartOfHourMapper()),
    )
    ASSET_OUTLETS = [HOURLY_SUMMARY]
except ImportError:
    from airflow.models import DAG

    ASSET_SCHEDULE = None
    ASSET_OUTLETS = []

from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"

with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args={"owner": OWNER},
    start_date=datetime.datetime(2025, 1, 1),
    schedule=ASSET_SCHEDULE,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["example", "asset", "partition"],
) as dag:
    DataPlatformStandardOperator(
        task_id="summarise_hour",
        name=f"{PROJECT}.{WORKFLOW}-summarise-hour",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=["echo partition_key=$PARTITION_KEY && python3 hourly.py"],
        outlets=ASSET_OUTLETS,
        env_vars={
            "BUCKET": "mojdp-test-mwaa",
            "BASE": "asset-partition-demo",
            "PARTITION_KEY": "{{ dag_run.partition_key }}",
        },
    )
