from datetime import datetime

try:
    from airflow.sdk import DAG, Asset
except ImportError:  # CI validation runs Airflow 2
    from airflow.datasets import Dataset as Asset
    from airflow.models import DAG
from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

API_ASSET = Asset("s3://test-dummy/api-asset")

dag_id = f"{PROJECT}.{WORKFLOW}"
with DAG(
    dag_id=dag_id,
    default_args={"depends_on_past": False, "owner": OWNER, "retries": 0},
    start_date=datetime(2025, 1, 1),
    schedule=[API_ASSET],
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["stress-test"],
) as dag:
    DataPlatformStandardOperator(
        task_id="noop",
        name=f"{PROJECT}.{WORKFLOW}",
        compute_profile="general-spot-1vcpu-4gb",
        image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["sleep", "1"],
    )
globals()[dag_id] = dag
