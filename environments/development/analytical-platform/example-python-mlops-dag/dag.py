from datetime import datetime
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.slack.notifications.slack import send_slack_notification
from airflow.providers.cncf.kubernetes.secret import (
    Secret,
)

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "owner": f"{OWNER}",
}

default_params = {
    "EXAMPLE_PARAMATER": "banana",
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=datetime(2025, 6, 26),
    schedule=None,
    params=default_params,
)

task = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="main",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "EXAMPLE_VARIABLE_ONE": "apple",
    },
    secrets=[
        Secret(
            deploy_type="env",
            deploy_target="SECRET_API_KEY",
            secret=f"{PROJECT}-{WORKFLOW}-api-key",
            key="data"
        )
    ],
    on_success_callback=[
        send_slack_notification(
            text="The task {{ ti.task_id }} succeeded",
            channel="#analytical-platform-airflow-testing",
        )
    ],
)
