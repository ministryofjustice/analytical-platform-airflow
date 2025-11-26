from datetime import datetime, timedelta
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator


REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"
DATE = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

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
    "email": DAG_EMAIL,
}

default_params = {
    "retries": 0,
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=datetime(2025, 11, 19),
    params=default_params,
    schedule_interval="0 7 * * *",
    catchup=False,
    max_active_tasks=1,
)


def create_kubernetes_operator(task_id, run_function, dag, scrape_date=DATE):
    return AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=f"{PROJECT}.{WORKFLOW}.{task_id}",
        compute_profile="general-on-demand-1vcpu-4gb",
        image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
        environment=f"{ENVIRONMENT}",
        project=f"{PROJECT}",
        workflow=f"{WORKFLOW}",
        env_vars={
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "AWS_DEFAULT_REGION": "eu-west-1",
        },
        cmds=["bash", "-c"],
        arguments=[
            f"""uv run python_scripts/main.py --scrape_date {scrape_date} \
            --env prod --function {run_function}""",
        ],
    )


run_functions = [
    "scrape_and_write_raw_bookings_data",
    "scrape_and_write_raw_locations_data",
    "validate_bookings_data",
    "validate_locations_data",
    "read_and_write_cleaned_bookings",
    "read_and_write_cleaned_locations",
    "refresh_new_partition_bookings",
    "refresh_new_partition_locations",
]
tasks = {}
for func in run_functions:
    tasks[func] = create_kubernetes_operator(f"task_{func}", func, dag)

tasks["scrape_and_write_raw_bookings_data"] >> tasks["validate_bookings_data"]
tasks["validate_bookings_data"] >> tasks["read_and_write_cleaned_bookings"]
tasks["read_and_write_cleaned_bookings"] >> tasks["refresh_new_partition_bookings"]
tasks["scrape_and_write_raw_locations_data"] >> tasks["validate_locations_data"]
tasks["validate_locations_data"] >> tasks["read_and_write_cleaned_locations"]
tasks["read_and_write_cleaned_locations"] >> tasks["refresh_new_partition_locations"]
