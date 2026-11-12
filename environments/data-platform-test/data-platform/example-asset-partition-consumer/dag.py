"""Partitioned asset consumer: runs once per partition of demo_partitioned."""

import datetime

try:
    from airflow.sdk import DAG, Asset, PartitionedAssetTimetable, StartOfHourMapper

    ASSET_SCHEDULE = PartitionedAssetTimetable(
        assets=Asset(name="demo_partitioned", uri="s3://demo/demo_partitioned"),
        default_partition_mapper=StartOfHourMapper(),
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
        task_id="consume",
        name=f"{PROJECT}.{WORKFLOW}-consume",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=["echo 'consuming demo_partitioned'"],
    )
