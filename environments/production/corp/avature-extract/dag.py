from datetime import datetime, timedelta
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
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
    "email_on_failure": True,
    "owner": f"{OWNER}",
}

default_params = {
    "retries": 0,
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=timedelta(seconds=62),
    schedule=False,
    params=default_params,
    catchup=False,
    max_active_tasks=1,
    is_paused_on_creation=True
)

task = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="main",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-on-demand-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "action": "scrape-store-plain-json-latest",
        "WR_WORKGROUP": "airflow-prod-workgroup-corp",
    },
    secrets=[
        Secret(
            deploy_type="env",
            deploy_target="SECRET_SERVICE_ACCOUNT_TOKEN",
            secret=f"{PROJECT}-{WORKFLOW}-service-account-token",
            key="data"
        )
    ]
)
