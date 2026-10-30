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

JOBS = 30
TASKS_PER_JOB = 10
SLEEP_SECONDS = 30

for j in range(1, JOBS + 1):
    dag_id = f"{PROJECT}.{WORKFLOW}-job-{j:02d}"
    with DAG(
        dag_id=dag_id,
        default_args={"depends_on_past": False, "owner": OWNER, "retries": 0},
        start_date=datetime(2025, 1, 1),
        schedule="* * * * *",
        catchup=False,
        max_active_runs=1,
        max_active_tasks=TASKS_PER_JOB,
        is_paused_upon_creation=True,
        tags=["stress-test"],
    ) as dag:
        for t in range(1, TASKS_PER_JOB + 1):
            DataPlatformStandardOperator(
                task_id=f"task-{t:02d}",
                name=f"{PROJECT}.{WORKFLOW}-job-{j:02d}-{t:02d}",
                compute_profile="general-spot-1vcpu-4gb",
                image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
                environment=ENVIRONMENT,
                project=PROJECT,
                workflow=WORKFLOW,
                cmds=["sleep", str(SLEEP_SECONDS)],
            )
    globals()[dag_id] = dag
