"""Asset producer: single task that emits an asset event."""

import datetime

try:
    from airflow.sdk import DAG, Asset
except ImportError:
    from airflow.models import DAG
    from airflow.sdk import Asset

from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"

DEMO_ASSET = Asset(name="demo_asset", uri="s3://mojdp-test-mwaa/demo/demo_asset")

with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args={"owner": OWNER},
    start_date=datetime.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["example", "asset"],
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
        arguments=["echo 'producing demo_asset'"],
        outlets=[DEMO_ASSET],
    )
