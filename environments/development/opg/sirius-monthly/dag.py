from datetime import datetime
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator


REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

start_date=datetime(2025, 6, 1)
total_workers = 10

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
    "DATABASE": "sirius_monthly",
    "PIPELINE_NAME": f"{WORKFLOW}",
    "DATABASE_VERSION": "dev",
    "GITHUB_TAG": f"{REPOSITORY_TAG}",
    "ATHENA_DB_PREFIX": "opg",
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
    env_vars=update_env_vars(base_env_vars, {"STEP": "land"})
)

tasks["raw_to_curated"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="raw_to_curated",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "curated"})
)

tasks[f"land_to_raw_init"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=f"land_to_raw_init",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "raw", "TOTAL_WORKERS": total_workers, "CLOSE": False})
)
tasks["to_land"] >> tasks[f"land_to_raw_init"]

tasks[f"land_to_raw_close"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=f"land_to_raw_close",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "raw", "TOTAL_WORKERS": total_workers, "CLOSE": True})
)

for batch in range (total_workers):
    tasks[f"land_to_raw_{batch}"] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=f"land_to_raw_{batch}",
        name=f"{PROJECT}.{WORKFLOW}",
        compute_profile=f"general-spot-16vcpu-64gb",
        image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
        environment=f"{ENVIRONMENT}",
        project=f"{PROJECT}",
        workflow=f"{WORKFLOW}",
        env_vars=update_env_vars(base_env_vars, {"STEP": "raw", "TOTAL_WORKERS": total_workers, "CLOSE": False, "CURRENT_WORKER": batch})
    )
    tasks[f"land_to_raw_init"] >> tasks[f"land_to_raw_{batch}"]
    tasks[f"land_to_raw_{batch}"] >> tasks[f"land_to_raw_close"]
    tasks[f"land_to_raw_close"] >> tasks[f"raw_to_curated"]


tasks["create_curated_database"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="create_curated_database",
    name=f"{PROJECT}.{WORKFLOW}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars=update_env_vars(base_env_vars, {"STEP": "curated_database"})
)
tasks["raw_to_curated"] >> tasks["create_curated_database"]
