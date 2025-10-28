import os
from datetime import datetime
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.slack.notifications.slack import send_slack_notification
from airflow.providers.cncf.kubernetes.secret import (
    Secret,
)

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

# Overall constants
ENV = "dev"
# This needs to be the same in the image docker files, where necessary
# (only required for ssh extraction)
USERID = 1008
DB_RUN_TS = datetime.now().strftime("%Y-%m-%d %H:%m:%S")
DB_VERSION = "v1"

# check_file task
CHECK_FILE_VERSION = "v1.2.13-dev"
CHECK_FILE_IMAGE = (
    f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/moj-analytical-services/"
    f"airflow-bold-rr-essex-police:{CHECK_FILE_VERSION}"
)

# load task
LOAD_IMAGE_VERSION = "v4.0.0"
LOAD_IMAGE = (
    f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/moj-analytical-services/"
    f"airflow-create-a-pipeline:{LOAD_IMAGE_VERSION}"
)

ROLE = f"airflow_{ENV}_bold_rr_essex_police_load"
SERVICE = "bold"

# Constants
LAND = "s3://mojap-land-dev/bold/essex-police/"
RAW_HIST = "s3://mojap-raw-hist-dev/bold/essex-police/"
BASE_LOC = "s3://alpha-bold-data-shares/bold-dev/"
BASE_DB_NAME = "bold_essex_police_data_dev"
PARTITION_COL = "mojap_file_land_timestamp"
TABLE = "essex_police_table"
SEPARATOR = "\t"

SECRET_GOV_NOTIFY_KEY = os.getenv("SECRET_GOV_NOTIFY_KEY_DEV")
EMAILS = "guy.wheeler@justice.gov.uk"

default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "owner": f"{OWNER}",
}



dag = DAG(
    dag_id="bold_rr_essex_police.load",
    default_args=default_args,
    start_date=datetime(2025, 6, 26),
    schedule=None)

tasks = {}

task_id_1 = "check-essex-police-file"

tasks[task_id_1] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id_1,
    name=task_id_1,
    compute_profile="general-spot-1vcpu-4gb",
    image=CHECK_FILE_IMAGE,
    environment=f"{ENV}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "LAND": LAND,
        "TABLE": TABLE,
        "EMAILS": EMAILS,
        "SEPARATOR": SEPARATOR,
        "PARAMETER_NAME": SECRET_GOV_NOTIFY_KEY,
        "PYTHON_SCRIPT_NAME": "police_data_check.py",
        "AWS_METADATA_SERVICE_TIMEOUT": "240",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "20",
        "AWS_DEFAULT_REGION": "eu-west-1",
    }
)

task_id_2 = "load-essex-police-bold-data"
tasks[task_id_2] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id_2,
    name=task_id_2,
    compute_profile="general-spot-1vcpu-4gb",
    image=LOAD_IMAGE,
    environment=f"{ENV}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "SERVICE": SERVICE,
        "IMAGE_TAG": DB_VERSION,
        "IMAGE_VERSION": LOAD_IMAGE_VERSION,
        "DB_RUN_TS": DB_RUN_TS,
        "DAG_RUN_ID": "{{ run_id }}",
        "DAG_INTERVAL_END": "{{ data_interval_end }}",
        "TABLE": TABLE,
        "LAND": LAND,
        "RAW_HIST": RAW_HIST,
        "BASE_LOC": BASE_LOC,
        "BASE_DB_NAME": BASE_DB_NAME,
        "PARTITION_COL": PARTITION_COL,
        "SEPARATOR": SEPARATOR,
        "AWS_METADATA_SERVICE_TIMEOUT": "240",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "20",
        "AWS_DEFAULT_REGION": "eu-west-1",
    }
)

tasks[task_id_1] >> tasks[task_id_2]
