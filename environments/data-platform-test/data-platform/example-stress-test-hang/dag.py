from datetime import datetime, timedelta

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

DAGS = 10
TASKS_PER_RUN = 50
MAX_RUNS_PER_DAG = 20
SLEEP_SECONDS = 60

for d in range(1, DAGS + 1):
    dag_id = f"{PROJECT}.{WORKFLOW}-{d:02d}"
    with DAG(
        dag_id=dag_id,
        default_args={"depends_on_past": False, "owner": OWNER, "retries": 0},
        start_date=datetime(2025, 1, 1),
        schedule="* * * * *",
        catchup=False,
        max_active_runs=MAX_RUNS_PER_DAG,
        max_active_tasks=70,
        dagrun_timeout=timedelta(minutes=90),
        is_paused_upon_creation=True,
        tags=["stress-test"],
    ) as dag:
        for t in range(1, TASKS_PER_RUN + 1):
            DataPlatformStandardOperator(
                task_id=f"pod-{t:03d}",
                name=f"{PROJECT}.{WORKFLOW}-{d:02d}-{t:03d}",
                compute_profile="general-spot-1vcpu-4gb",
                image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
                environment=ENVIRONMENT,
                project=PROJECT,
                workflow=WORKFLOW,
                cmds=["sleep", str(SLEEP_SECONDS)],
            )
    globals()[dag_id] = dag
