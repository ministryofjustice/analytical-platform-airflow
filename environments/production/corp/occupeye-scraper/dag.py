from datetime import datetime, timedelta
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

DAG_EMAIL = [
    "Supratik.Chowdhury@justice.gov.uk",
    "Laurence.Droy@justice.gov.uk",
    "Shanmugapriya.Basker@justice.gov.uk",
    "William.Orr@justice.gov.uk",
]

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": DAG_EMAIL
}

default_params = {
    "retries": 3,
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=datetime(2025, 9, 1),
    schedule_interval=timedelta(days=1),
    params=default_params,
    catchup=False,
    max_active_tasks=1
)

surveys_to_s3 = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="main",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-on-demand-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "AWS_DEFAULT_REGION": "eu-west-1",
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "WR_WORKGROUP": "airflow-prod-workgroup-corp",
    },
    cmds=["bash", "-c"],
    arguments=[
        "python3 main.py "
        "--scrape_type=daily "
        "--scrape_datetime='{{ts}}' "
        "--next_execution_date='{{next_execution_date}}'"
    ]
)
