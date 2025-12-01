from datetime import datetime
from airflow import DAG
# REMOVED: import boto3, import json (no longer needed here)
from airflow.providers.cncf.kubernetes.secret import Secret
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

# --- CONFIGURATION ---
S3_SECRET_BUCKET = "alpha-contracts-etl"
S3_SECRET_KEY = "secrets/secrets.json"
AWS_REGION = "eu-west-2"
AWS_SECRET_ARN = (
    "arn:aws:secretsmanager:eu-west-2:593291632749:secret:"
    "/airflow/development/corp/contracts-etl-dev/airflow-dev-contracts-etl-7RywJy"
)

# Project Constants
REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"
IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"
DEFAULT_DB_ENV = "dev"
RETRIES = 0

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": "supratik.chowdhury@justice.gov.uk",
}

GLOBAL_SECRETS_LIST = [
    Secret("env", "CLIENT_ID", AWS_SECRET_ARN, "client_id"),
    Secret("env", "CLIENT_SECRET", AWS_SECRET_ARN, "client_secret"),
    Secret("env", "JAG_PRIVATE_KEY", AWS_SECRET_ARN, "jag_private_key"),
    Secret("env", "JAG_HOST_KEY", AWS_SECRET_ARN, "jag_host_key"),
]

with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description="Contracts ETL Pipeline",
    start_date=datetime(2022, 5, 20),
    catchup=False,
) as dag:

    # --- Task Helper ---
    def create_task(
        task_id,
        python_script_name,
        source_db_env="none", # Default to none for sync task
        prod_db_env=None,
        table_name_env=None,
        trigger_rule="all_success",
        secret_list=None,
        extra_env_vars=None, # Added support for extra env vars
    ):
        # Base environment variables
        env_vars = {
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "AWS_DEFAULT_REGION": "eu-west-1",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "GITHUB_TAG": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DEFAULT_DB_ENV,
            "PYTHON_SCRIPT_NAME": python_script_name,
            "SOURCE_DB_ENV": source_db_env,
            **({"PROD_DB_ENV": prod_db_env} if prod_db_env else {}),
            **({"TABLE_NAME_ENV": table_name_env} if table_name_env else {}),
        }

        # Merge extra env vars if provided (Critical for Sync Task)
        if extra_env_vars:
            env_vars.update(extra_env_vars)

        return AnalyticalPlatformStandardOperator(
            dag=dag,
            task_id=task_id,
            name=task_id,
            compute_profile="general-on-demand-1vcpu-4gb",
            image=IMAGE,
            environment=ENVIRONMENT,
            project=PROJECT,
            workflow=WORKFLOW,
            trigger_rule=trigger_rule,
            retries=RETRIES,
            secrets=secret_list or [],
            env_vars=env_vars,
        )

    tasks = {}
    JAG_SECRETS = GLOBAL_SECRETS_LIST

    # ----------------------------------------------------------------------
    # 1. The Sync Task (Moved to Standard Operator)
    # ----------------------------------------------------------------------
    sync_secrets_task = create_task(
        task_id="sync_secrets_to_sm",
        python_script_name="sync_secrets.py", # This script must exist in your image
        source_db_env="none",
        extra_env_vars={
            "S3_SECRET_BUCKET": S3_SECRET_BUCKET,
            "S3_SECRET_KEY": S3_SECRET_KEY,
            "AWS_SECRET_ARN": AWS_SECRET_ARN,
            "AWS_REGION": AWS_REGION
        }
    )

    # ----------------------------------------------------------------------
    # 2. Business Logic (Unchanged)
    # ----------------------------------------------------------------------
    SOURCE_DB_ENV = "jaggaer"
    tasks[f"extract_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"extract_{SOURCE_DB_ENV}",
        python_script_name=f"{SOURCE_DB_ENV}_to_land.py",
        source_db_env=SOURCE_DB_ENV,
        secret_list=JAG_SECRETS,
    )

    tasks["jaggaer_preprocess"] = create_task(
        task_id="jaggaer_preprocess",
        python_script_name="pre_process_jaggaer.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="preprod",
        secret_list=JAG_SECRETS,
    )

    tasks[f"lint_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"lint_{SOURCE_DB_ENV}",
        python_script_name="land_to_raw_hist.py",
        source_db_env=SOURCE_DB_ENV,
    )

    tasks[f"process_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"process_{SOURCE_DB_ENV}",
        python_script_name="raw_to_curated.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="preprod",
    )

    # --- Rio Flow ---
    SOURCE_DB_ENV = "rio"
    tasks[f"extract_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"extract_{SOURCE_DB_ENV}",
        python_script_name=f"{SOURCE_DB_ENV}_to_land.py",
        source_db_env=SOURCE_DB_ENV,
    )

    tasks[f"lint_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"lint_{SOURCE_DB_ENV}",
        python_script_name="land_to_raw_hist.py",
        source_db_env=SOURCE_DB_ENV,
    )

    tasks[f"process_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"process_{SOURCE_DB_ENV}",
        python_script_name="rio_raw_hist_to_curated.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="preprod",
    )

    # --- Tables ---
    tables = [
        ("claims", "jaggaer"),
        ("contracts", "jaggaer"),
        ("light_touch_scorecards", "jaggaer"),
        ("spend", "jaggaer"),
        ("rio", "rio"),
    ]

    for table_name, source_env in tables:
        current_secrets = JAG_SECRETS if source_env == "jaggaer" else None

        check_name = f"preprod_check_status_{table_name}"
        tasks[check_name] = create_task(
            task_id=check_name,
            python_script_name="get_preprod_check_status.py",
            source_db_env=source_env,
            table_name_env=table_name,
            prod_db_env="preprod",
            secret_list=current_secrets,
        )

        copy_name = f"copy_preprod_to_live_{table_name}"
        tasks[copy_name] = create_task(
            task_id=copy_name,
            python_script_name="copy_preprod_to_live.py",
            source_db_env=source_env,
            table_name_env=table_name,
            prod_db_env="live",
            secret_list=current_secrets,
        )

    # --- DB Creation ---
    tasks["create_ext_db"] = create_task("create_ext_db", "create_db.py", "ext", prod_db_env="live")
    tasks["create_preprod_db"] = create_task("create_preprod_db", "create_db.py", "all", prod_db_env="preprod", trigger_rule="all_done")
    tasks["create_live_db"] = create_task("create_live_db", "create_db.py", "all", prod_db_env="live", trigger_rule="all_done")

    tasks["create_jaggaer_db"] = create_task("create_jaggaer_db", "create_db.py", "jaggaer", prod_db_env="live")
    tasks["create_rio_db"] = create_task("create_rio_db", "create_db.py", "rio", prod_db_env="live")

    tasks["create_jaggaer_extracts"] = create_task("create_jaggaer_extracts", "create_extracts.py", "jaggaer")
    tasks["create_rio_extracts"] = create_task("create_rio_extracts", "create_extracts.py", "rio")

    tasks["preprod_checks"] = create_task(
        task_id="preprod_checks",
        python_script_name="run_preprod_checks.py",
        source_db_env="all",
        prod_db_env="preprod",
    )

    # ----------------------------------------------------------------------
    # 3. Dependencies
    # ----------------------------------------------------------------------
    sync_secrets_task >> tasks["extract_jaggaer"]
    sync_secrets_task >> tasks["extract_rio"]

    tasks["extract_jaggaer"] >> tasks["jaggaer_preprocess"]
    tasks["jaggaer_preprocess"] >> tasks["lint_jaggaer"]
    tasks["lint_jaggaer"] >> tasks["process_jaggaer"]

    tasks["extract_rio"] >> tasks["lint_rio"]
    tasks["lint_rio"] >> tasks["process_rio"]

    [tasks["process_jaggaer"], tasks["process_rio"]] >> tasks["create_preprod_db"]
    tasks["create_preprod_db"] >> tasks["preprod_checks"]

    tasks["preprod_checks"] >> [
        tasks[f"preprod_check_status_{t[0]}"] for t in tables
    ]

    for t in tables:
        tasks[f"preprod_check_status_{t[0]}"] >> tasks[f"copy_preprod_to_live_{t[0]}"]

    # Gather copies for Live DB creation
    copy_tasks = [tasks[f"copy_preprod_to_live_{t[0]}"] for t in tables]

    copy_tasks >> tasks["create_live_db"]

    # Specific DB Dependencies
    jaggaer_copies = [t for t in copy_tasks if "rio" not in t.task_id]
    rio_copies = [t for t in copy_tasks if "rio" in t.task_id]

    if jaggaer_copies:
        jaggaer_copies >> tasks["create_jaggaer_db"]
    if rio_copies:
        rio_copies >> tasks["create_rio_db"]

    tasks["create_ext_db"]
    tasks["create_jaggaer_db"] >> tasks["create_jaggaer_extracts"]
    tasks["create_rio_db"] >> tasks["create_rio_extracts"]