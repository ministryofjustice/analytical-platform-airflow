from datetime import datetime

try:
    from airflow.sdk import DAG
except ImportError:  # CI validation runs Airflow 2
    from airflow.models import DAG
from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

BURSTS = [10, 50, 70, 90, 120]
SLEEP_SECONDS = 600

for pods in BURSTS:
    dag_id = f"{PROJECT}.{WORKFLOW}-{pods}-pods"
    with DAG(
        dag_id=dag_id,
        default_args={"depends_on_past": False, "owner": OWNER, "retries": 0},
        start_date=datetime(2025, 1, 1),
        schedule=None,
        catchup=False,
        max_active_runs=1,
        max_active_tasks=pods,
        is_paused_upon_creation=False,
        tags=["stress-test"],
    ) as dag:
        for t in range(1, pods + 1):
            DataPlatformStandardOperator(
                task_id=f"pod-{t:03d}",
                name=f"{PROJECT}.{WORKFLOW}-{pods}-pods-{t:03d}",
                compute_profile="general-spot-1vcpu-4gb",
                image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
                environment=ENVIRONMENT,
                project=PROJECT,
                workflow=WORKFLOW,
                cmds=["sleep", str(SLEEP_SECONDS)],
            )
    globals()[dag_id] = dag
