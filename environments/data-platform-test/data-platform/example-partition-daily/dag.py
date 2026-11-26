"""Daily: runs on each hourly summary and rolls the hours up into a day for the prison."""

import datetime

try:
    from airflow.sdk import (
        DAG,
        Asset,
        IdentityMapper,
        PartitionedAssetTimetable,
        ProductMapper,
        StartOfDayMapper,
    )

    BASE_URI = "s3://mojdp-test-mwaa/asset-partition-demo"
    HOURLY_SUMMARY = Asset(name="prison_hourly_summary", uri=f"{BASE_URI}/summaries/hourly")

    ASSET_SCHEDULE = PartitionedAssetTimetable(
        assets=HOURLY_SUMMARY,
        default_partition_mapper=ProductMapper(
            IdentityMapper(),
            StartOfDayMapper(input_format="%Y-%m-%dT%H"),
        ),
    )
except ImportError:
    from airflow.models import DAG

    ASSET_SCHEDULE = None

from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "moj-analytical-services/airflow-3-feature-test-hitl"
REPOSITORY_TAG = "0.0.5"
PROJECT = "data-platform"
WORKFLOW = "example-partition-daily"
ENVIRONMENT = "data-platform-test"
OWNER = "analytical-platform@justice.gov.uk"

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
            "PARTITION_KEY": "{{ dag_run.partition_key }}",
        },
    )
