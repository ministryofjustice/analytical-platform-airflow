from datetime import datetime, timedelta

try:
    from airflow.sdk import DAG, Asset
except ImportError:
    from airflow.datasets import Dataset as Asset
    from airflow.models import DAG
from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

BUCKET = "mojdp-test-mwaa"
PREFIX = "durability-test"
FILES = 12
ENV = {"BUCKET": BUCKET, "PREFIX": PREFIX}
DATA = Asset(f"s3://{BUCKET}/{PREFIX}/")
IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"


def pod(task_id, args, **kwargs):
    return DataPlatformStandardOperator(
        task_id=task_id,
        name=f"{PROJECT}.{WORKFLOW}-{task_id}",
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        arguments=args,
        **{"env_vars": ENV, **kwargs},
    )


dag_id = f"{PROJECT}.{WORKFLOW}"
with DAG(
    dag_id=dag_id,
    default_args={"owner": OWNER, "retries": 1, "execution_timeout": timedelta(minutes=30)},
    start_date=datetime(2025, 1, 1),
    schedule=[DATA],
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    tags=["durability-test"],
) as dag:
    validate = pod("validate", ["validate"])
    validate >> [pod(f"delete-{n:02d}", ["delete", str(n)]) for n in range(1, FILES + 1)]
globals()[dag_id] = dag
