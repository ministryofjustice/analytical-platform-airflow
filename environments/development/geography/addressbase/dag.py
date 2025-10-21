from datetime import datetime
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

start_date=datetime(2025, 8, 5)
total_workers = 20

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "retries": 1,
    "retry_delay":150
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=start_date,
    schedule=None,
    catchup=False,
)

base_env_vars={
    "DATABASE": "addressbase",
    "PIPELINE_NAME": f"{WORKFLOW}",
    "DATABASE_VERSION": "dev",
    "GITHUB_TAG": f"{REPOSITORY_TAG}",
    "ATHENA_DB_PREFIX": "geog",
    "START_DATE": start_date.strftime("%Y-%m-%d"),
}

def update_env_vars(env_vars: dict[str, str], updates: dict[str, str]) -> dict[str, str]:
    return {**env_vars, **updates}

tasks = {}

tasks["to_land"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="to_land",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "to_land"}),
    secrets=[
        Secret(
            deploy_type="env",
            deploy_target="SECRET_OSDATAHUB_API_KEY",
            secret=f"{PROJECT}-{WORKFLOW}-osdatahub-api-key",
            key="osdatahub_api_key",
        )
    ],
)

tasks["raw_hist_to_curated"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="raw_hist_to_curated",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "raw_hist_to_curated"})
)

raw_tables = ["addressbasepremium"]


for table in raw_tables:

    tasks[f"land_to_raw_hist_init_{table}"] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=f"land_to_raw_hist_init_{table}",
        name=f"{PROJECT}.{WORKFLOW}",
        compute_profile="general-spot-1vcpu-4gb",
        image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
        environment=f"{ENVIRONMENT}",
        project=f"{PROJECT}",
        workflow=f"{WORKFLOW}",
        env_vars=update_env_vars(base_env_vars, {"STEP": "land_to_raw", "TOTAL_WORKERS": total_workers, "CLOSE": False, "TABLE": table})
    )
    tasks["to_land"] >> tasks[f"land_to_raw_hist_init_{table}"]

    tasks[f"land_to_raw_close_{table}"] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=f"land_to_raw_close_{table}",
        name=f"{PROJECT}.{WORKFLOW}",
        compute_profile="general-spot-1vcpu-4gb",
        image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
        environment=f"{ENVIRONMENT}",
        project=f"{PROJECT}",
        workflow=f"{WORKFLOW}",
        env_vars=update_env_vars(base_env_vars, {"STEP": "land_to_raw", "TOTAL_WORKERS": total_workers, "CLOSE": True, "TABLE": table})
    )

    for batch in range (total_workers):
        tasks[f"land_to_raw_{table}_{batch}"] = AnalyticalPlatformStandardOperator(
            dag=dag,
            task_id=f"land_to_raw_{table}_{batch}",
            name=f"{PROJECT}.{WORKFLOW}",
            compute_profile="general-spot-1vcpu-4gb",
            image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
            environment=f"{ENVIRONMENT}",
            project=f"{PROJECT}",
            workflow=f"{WORKFLOW}",
            env_vars=update_env_vars(base_env_vars, {"STEP": "land_to_raw", "TOTAL_WORKERS": total_workers, "CLOSE": False, "CURRENT_WORKER": batch, "TABLE": table})
        )
        tasks[f"land_to_raw_hist_init_{table}"] >> tasks[f"land_to_raw_{table}_{batch}"]
        tasks[f"land_to_raw_{table}_{batch}"] >> tasks[f"land_to_raw_close_{table}"]
        tasks[f"land_to_raw_close_{table}"] >> tasks[f"raw_hist_to_curated"]


tasks["create_curated_database"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="create_curated_database",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "create_curated_database"})
)
tasks["raw_hist_to_curated"] >> tasks["create_curated_database"]
