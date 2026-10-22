from datetime import datetime

from airflow.sdk import DAG, Variable
from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

try:
    DAG_COUNT = int(Variable.get("example_stress_test_parse_dag_count", default=0))
except Exception:
    DAG_COUNT = 0
TASKS_PER_DAG = 5

for d in range(1, DAG_COUNT + 1):
    dag_id = f"{PROJECT}.{WORKFLOW}-{d:04d}"
    with DAG(
        dag_id=dag_id,
        default_args={"depends_on_past": False, "owner": OWNER, "retries": 0},
        start_date=datetime(2025, 1, 1),
        schedule=None,
        catchup=False,
        is_paused_upon_creation=True,
        tags=["stress-test"],
    ) as dag:
        for t in range(1, TASKS_PER_DAG + 1):
            DataPlatformStandardOperator(
                task_id=f"task-{t}",
                name=f"{PROJECT}.{WORKFLOW}-{d:04d}-{t}",
                compute_profile="general-spot-1vcpu-4gb",
                image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
                environment=ENVIRONMENT,
                project=PROJECT,
                workflow=WORKFLOW,
                cmds=["sleep", "1"],
            )
    globals()[dag_id] = dag
