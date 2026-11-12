"""Partitioned asset producer: emits a partitioned asset event every 10 minutes."""

import datetime

try:
    from airflow.sdk import DAG, Asset, CronPartitionTimetable

    ASSET_OUTLETS = [Asset(name="demo_partitioned", uri="s3://demo/demo_partitioned")]
    PRODUCER_SCHEDULE = CronPartitionTimetable("*/10 * * * *", timezone="UTC")
except ImportError:
    from airflow.models import DAG

    ASSET_OUTLETS = []
    PRODUCER_SCHEDULE = None

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
    schedule=PRODUCER_SCHEDULE,
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    tags=["example", "asset", "partition"],
) as dag:
    DataPlatformStandardOperator(
        task_id="produce",
        name=f"{PROJECT}.{WORKFLOW}-produce",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=["echo 'producing demo_partitioned'"],
        outlets=ASSET_OUTLETS,
    )
