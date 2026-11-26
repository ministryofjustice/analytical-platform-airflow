"""Daily roll-up: runs when all 24 hourly summaries for a day exist."""

import datetime

try:
    from airflow.sdk import (
        DAG,
        Asset,
        DayWindow,
        PartitionedAssetTimetable,
        RollupMapper,
        StartOfHourMapper,
        WaitForAll,
    )

    HOURLY_SUMMARY = Asset(
        name="prison_hourly_summary",
        uri="s3://mojdp-test-mwaa/asset-partition-demo/summaries/hourly",
    )
    ASSET_SCHEDULE = PartitionedAssetTimetable(
        assets=HOURLY_SUMMARY,
        default_partition_mapper=RollupMapper(
            upstream_mapper=StartOfHourMapper(input_format="%Y-%m-%dT%H"),
            window=DayWindow(),
            wait_policy=WaitForAll(),
        ),
    )
except ImportError:
    from airflow.models import DAG

    ASSET_SCHEDULE = None

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
        task_id="summarise_day",
        name=f"{PROJECT}.{WORKFLOW}-summarise-day",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=["echo partition_key=$PARTITION_KEY && python3 daily.py"],
        env_vars={
            "BUCKET": "mojdp-test-mwaa",
            "BASE": "asset-partition-demo",
            "PRISON": "alpha",
            "PARTITION_KEY": "{{ dag_run.partition_key }}",
        },
    )
