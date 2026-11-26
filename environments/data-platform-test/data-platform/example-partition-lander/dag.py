"""Lander: writes fake prison-capacity CSVs to S3 (manual, parameterised)."""

import datetime

try:
    from airflow.sdk import DAG
except ImportError:
    from airflow.models import DAG

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
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    params={
        "prison": "alpha",
        "day": "2026-11-12",
        "first_hour": 0,
        "last_hour": 23,
        "skip": "",
    },
    tags=["example", "asset", "partition"],
) as dag:
    DataPlatformStandardOperator(
        task_id="land",
        name=f"{PROJECT}.{WORKFLOW}-land",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=["pwd && ls && python3 lander.py"],
        env_vars={
            "BUCKET": "mojdp-test-mwaa",
            "PREFIX": "asset-partition-demo/landing",
            "PRISON": "{{ params.prison }}",
            "DAY": "{{ params.day }}",
            "FIRST_HOUR": "{{ params.first_hour }}",
            "LAST_HOUR": "{{ params.last_hour }}",
            "SKIP": "{{ params.skip }}",
        },
    )
