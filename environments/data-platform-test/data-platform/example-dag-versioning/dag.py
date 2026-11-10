"""
DAG versioning example (v1): extract -> wait -> load
"""
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
DAG_VERSION_LABEL = "v1"


def pod(task_id, command):
    return DataPlatformStandardOperator(
        task_id=task_id,
        name=f"{PROJECT}.{WORKFLOW}-{task_id}",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=[command],
    )


with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args={"owner": OWNER},
    start_date=datetime.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["example", "versioning"],
    doc_md=f"DAG versioning demo, label {DAG_VERSION_LABEL}",
) as dag:
    extract = pod("extract", f"echo 'DAG {DAG_VERSION_LABEL}: extract'")
    wait = pod("wait", f"echo 'DAG {DAG_VERSION_LABEL}: waiting'; sleep 300")
    load = pod("load", f"echo 'DAG {DAG_VERSION_LABEL}: load'")

    extract >> wait >> load
