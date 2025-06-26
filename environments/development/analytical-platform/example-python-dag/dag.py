from datetime import datetime
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

REPOSITORY_NAME="moj-analytical-services/analytical-platform-airflow-python-example"
REPOSITORY_TAG="2.10.0"
PROJECT="analytical-platform"
WORKFLOW="example-python-dag"
ENVIRONMENT="development"

default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "owner": "jacob.woffenden@justice.gov.uk",
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=datetime(2025, 6, 26),
    schedule=None,
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
    hmcts_sdp_networking=False
)
