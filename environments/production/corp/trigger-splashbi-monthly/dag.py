from datetime import datetime, timedelta
from pendulum import datetime, duration
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

DAG_EMAIL = [
    "Supratik.Chowdhury@justice.gov.uk",
    "William.Orr@justice.gov.uk",
    "Mohammed.Ahad1@justice.gov.uk"
]

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": DAG_EMAIL,
    "retries": 2,
    "retry_delay": duration(hours=24)
}


dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=datetime(2025, 10, 1),
    schedule_interval="0 7 1 * *", 
    catchup=False,
    max_active_runs=1
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
        "REPORT_APP": "splashbi",
        "REPORT_RUNTIME_ENV": "prod",
        "REPORT_RUN_MODE": "trigger",
        "REPORT_NAME": "po_sscl_details",

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



