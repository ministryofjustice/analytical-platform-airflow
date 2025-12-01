import json
import logging
from datetime import datetime

# AWS SDK
import boto3

# Airflow
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.secret import Secret

# Custom Operator
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

# --- CONFIGURATION ---
# Static variables (Safe at top level)
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
IMAGE = (
    f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"
)
DEFAULT_DB_ENV = "dev"
RETRIES = 0


# --- 🐍 Python Sync Function ---
# This runs strictly on the worker, preventing Scheduler overload.
def sync_s3_to_secrets_manager():
    """Reads secrets.json from S3 and updates the Secrets Manager ARN."""
    logging.basicConfig(level=logging.INFO)

    # Initialize clients INSIDE the function (Task execution context)
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    sm_client = boto3.client("secretsmanager", region_name=AWS_REGION)

    # 1. Read S3 Content
    try:
        logging.info(f"Reading from Bucket: {S3_SECRET_BUCKET}, Key: {S3_SECRET_KEY}")
        response = s3_client.get_object(Bucket=S3_SECRET_BUCKET, Key=S3_SECRET_KEY)
        json_string = response["Body"].read().decode("utf-8")
        json.loads(json_string)  # Validate JSON structure
        logging.info("S3 content successfully read and validated.")
    except Exception as e:
        raise Exception(f"Failed to read or validate S3 secret: {e}")

    # 2. Update/Create Secret Manager Entry
    try:
        # Try updating first
        sm_client.update_secret(SecretId=AWS_SECRET_ARN, SecretString=json_string)
        logging.info(f"✅ Successfully updated secret at ARN: {AWS_SECRET_ARN}")
    except sm_client.exceptions.ResourceNotFoundException:
        # If it doesn't exist, create it
        sm_client.create_secret(Name=AWS_SECRET_ARN, SecretString=json_string)
        logging.info(f"✅ Successfully created new secret at ARN: {AWS_SECRET_ARN}")
    except Exception as e:
        raise Exception(f"Failed to sync to Secrets Manager: {e}")


# --- Default Args ---
default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": "supratik.chowdhury@justice.gov.uk",
}

# --- Global Secrets Definition ---
# This is safe at top level because Secret() is a declarative object,
# it does not make API calls during parsing.
GLOBAL_SECRETS_LIST = [
    Secret(
        deploy_type="env",
        deploy_target="CLIENT_ID",
        secret=AWS_SECRET_ARN,
        key="client_id",
    ),
    Secret(
        deploy_type="env",
        deploy_target="CLIENT_SECRET",
        secret=AWS_SECRET_ARN,
        key="client_secret",
    ),
    Secret(
        deploy_type="env",
        deploy_target="JAG_PRIVATE_KEY",
        secret=AWS_SECRET_ARN,
        key="jag_private_key",
    ),
    Secret(
        deploy_type="env",
        deploy_target="JAG_HOST_KEY",
        secret=AWS_SECRET_ARN,
        key="jag_host_key",
    ),
]

# --- DAG Definition ---
with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description="Contracts ETL Pipeline",
    start_date=datetime(2022, 5, 20),
    catchup=False,
) as dag:

    # ----------------------------------------------------------------------
    # 1. The Sync Task
    # ----------------------------------------------------------------------
    sync_secrets_task = PythonOperator(
        task_id="sync_secrets_to_sm",
        python_callable=sync_s3_to_secrets_manager,
    )

    # --- Task Helper ---
    def create_task(
        task_id,
        python_script_name,
        source_db_env,
        prod_db_env=None,
        table_name_env=None,
        trigger_rule="all_success",
        secret_list=None,
    ):
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
            env_vars={
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
            },
        )

    tasks = {}
    JAG_SECRETS = GLOBAL_SECRETS_LIST

    # ----------------------------------------------------------------------
    # 2. Define Business Logic Tasks
    # ----------------------------------------------------------------------

    # --- Jaggaer Flow ---
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

    # --- Specific Table Checks/Copies ---
    tables = [
        ("claims", "jaggaer"),
        ("contracts", "jaggaer"),
        ("light_touch_scorecards", "jaggaer"),
        ("spend", "jaggaer"),
        ("rio", "rio"),
    ]

    for table_name, source_env in tables:
        current_secrets = JAG_SECRETS if source_env == "jaggaer" else None

        # Check Status
        check_name = f"preprod_check_status_{table_name}"
        tasks[check_name] = create_task(
            task_id=check_name,
            python_script_name="get_preprod_check_status.py",
            source_db_env=source_env,
            table_name_env=table_name,
            prod_db_env="preprod",
            secret_list=current_secrets,
        )

        # Copy to Live
        copy_name = f"copy_preprod_to_live_{table_name}"
        tasks[copy_name] = create_task(
            task_id=copy_name,
            python_script_name="copy_preprod_to_live.py",
            source_db_env=source_env,
            table_name_env=table_name,
            prod_db_env="live",
            secret_list=current_secrets,
        )

    # --- DB Creation Tasks ---
    tasks["create_ext_db"] = create_task(
        "create_ext_db", "create_db.py", "ext", prod_db_env="live"
    )
    tasks["create_preprod_db"] = create_task(
        "create_preprod_db",
        "create_db.py",
        "all",
        prod_db_env="preprod",
        trigger_rule="all_done",
    )
    tasks["create_live_db"] = create_task(
        "create_live_db",
        "create_db.py",
        "all",
        prod_db_env="live",
        trigger_rule="all_done",
    )

    # Added these definitions to fix KeyError in dependencies
    tasks["create_jaggaer_db"] = create_task(
        "create_jaggaer_db", "create_db.py", "jaggaer", prod_db_env="live"
    )
    tasks["create_rio_db"] = create_task(
        "create_rio_db", "create_db.py", "rio", prod_db_env="live"
    )

    tasks["create_jaggaer_extracts"] = create_task(
        "create_jaggaer_extracts", "create_extracts.py", "jaggaer"
    )
    tasks["create_rio_extracts"] = create_task(
        "create_rio_extracts", "create_extracts.py", "rio"
    )

    # --- Preprod Checks ---
    tasks["preprod_checks"] = create_task(
        task_id="preprod_checks",
        python_script_name="run_preprod_checks.py",
        source_db_env="all",
        prod_db_env="preprod",
    )

    # ----------------------------------------------------------------------
    # 3. Task Dependencies
    # ----------------------------------------------------------------------

    # *** CRITICAL: The sync task must run before any extraction ***
    sync_secrets_task >> tasks["extract_jaggaer"]
    sync_secrets_task >> tasks["extract_rio"]

    # Jaggaer Pipeline
    tasks["extract_jaggaer"] >> tasks["jaggaer_preprocess"]
    tasks["jaggaer_preprocess"] >> tasks["lint_jaggaer"]
    tasks["lint_jaggaer"] >> tasks["process_jaggaer"]

    # Rio Pipeline
    tasks["extract_rio"] >> tasks["lint_rio"]
    tasks["lint_rio"] >> tasks["process_rio"]

    # DB Creation & Checks
    [tasks["process_jaggaer"], tasks["process_rio"]] >> tasks["create_preprod_db"]
    tasks["create_preprod_db"] >> tasks["preprod_checks"]

    # Preprod Checks -> Status Checks
    tasks["preprod_checks"] >> [
        tasks["preprod_check_status_claims"],
        tasks["preprod_check_status_contracts"],
        tasks["preprod_check_status_light_touch_scorecards"],
        tasks["preprod_check_status_spend"],
        tasks["preprod_check_status_rio"],
    ]

    # Status Checks -> Copy to Live
    tasks["preprod_check_status_claims"] >> tasks["copy_preprod_to_live_claims"]
    tasks["preprod_check_status_contracts"] >> tasks["copy_preprod_to_live_contracts"]
    (
        tasks["preprod_check_status_light_touch_scorecards"]
        >> tasks["copy_preprod_to_live_light_touch_scorecards"]
    )
    tasks["preprod_check_status_spend"] >> tasks["copy_preprod_to_live_spend"]
    tasks["preprod_check_status_rio"] >> tasks["copy_preprod_to_live_rio"]

    # Copy to Live -> Create DBs
    [
        tasks["copy_preprod_to_live_claims"],
        tasks["copy_preprod_to_live_contracts"],
        tasks["copy_preprod_to_live_light_touch_scorecards"],
        tasks["copy_preprod_to_live_spend"],
    ] >> tasks["create_jaggaer_db"]

    tasks["copy_preprod_to_live_rio"] >> tasks["create_rio_db"]

    # Sync all copy tasks to Final Live DB creation
    [
        tasks["copy_preprod_to_live_claims"],
        tasks["copy_preprod_to_live_contracts"],
        tasks["copy_preprod_to_live_light_touch_scorecards"],
        tasks["copy_preprod_to_live_spend"],
        tasks["copy_preprod_to_live_rio"],
    ] >> tasks["create_live_db"]

    # Independent task
    tasks["create_ext_db"]

    # Final Extracts
    tasks["create_jaggaer_db"] >> tasks["create_jaggaer_extracts"]
    tasks["create_rio_db"] >> tasks["create_rio_extracts"]
