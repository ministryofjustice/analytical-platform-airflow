from datetime import datetime
# Import the base DAG class
from airflow import DAG
# Import the custom operator
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
# 🛠️ FIX 1: Import the required Secret class for Kubernetes secrets
from airflow.providers.cncf.kubernetes.secret import Secret


# --- Placeholders ---

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
# Define the AWS Secret ARN Constant
AWS_SECRET_ARN = "arn:aws:secretsmanager:eu-west-2:593291632749:secret:/airflow/development/corp/contracts-etl-dev/airflow-dev-contracts-etl-7RywJy"


# --- Default Args ---
default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": "supratik.chowdhury@justice.gov.uk",
}

# ----------------------------------------------------------------------
# 🔑 Global Secrets List (Defined BEFORE use)
# ----------------------------------------------------------------------
GLOBAL_SECRETS_LIST = [
    Secret(deploy_type="env", deploy_target="DB_USER", secret=AWS_SECRET_ARN, key="db_user"),
    Secret(deploy_type="env", deploy_target="DB_PASSWORD", secret=AWS_SECRET_ARN, key="db_password"),
    Secret(deploy_type="env", deploy_target="JAG_PRIVATE_KEY", secret=AWS_SECRET_ARN, key="jag_private_key"),
    Secret(deploy_type="env", deploy_target="JAG_HOST_KEY", secret=AWS_SECRET_ARN, key="jag_host_key"),
]


# --- DAG Context Manager ---
# The DAG definition is often wrapped around the tasks, or defined globally.
# We define it here so the `dag` object is available for `create_task`.
with DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description="Contracts ETL Pipeline",
    start_date=datetime(2022, 5, 20),
    catchup=False,
) as dag: # The DAG object is created and assigned to the variable `dag`


    # --- Task Definitions (Helper Function) ---
    def create_task(
        task_id,
        python_script_name,
        source_db_env,
        prod_db_env=None,
        table_name_env=None,
        trigger_rule=None,
        secret_list=None,
    ):
        """Creates an AnalyticalPlatformStandardOperator task."""
        # 🛠️ FIX 2: `dag=dag` is now safe because `dag` is defined by the `with` statement
        return AnalyticalPlatformStandardOperator(
            dag=dag, 
            task_id=task_id,
            name=task_id,
            compute_profile="general-on-demand-1vcpu-4gb",
            image=IMAGE,
            environment=ENVIRONMENT,
            project=PROJECT,
            workflow=WORKFLOW,
            trigger_rule=trigger_rule or "all_success",
            retries=RETRIES,
            secrets=secret_list or [], # Use the passed secrets list
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


    # 🛠️ FIX 3: Initialize the dictionary BEFORE creating tasks
    tasks = {} 
    JAG_SECRETS = GLOBAL_SECRETS_LIST # Shorthand for tasks needing Jaggaer creds


    # --- Jaggaer Extract Tasks (APPLY SECRETS) ----
    SOURCE_DB_ENV = "jaggaer"
    tasks[f"extract_{SOURCE_DB_ENV}"] = create_task(
        task_id=f"extract_{SOURCE_DB_ENV}",
        python_script_name=f"{SOURCE_DB_ENV}_to_land.py",
        source_db_env=SOURCE_DB_ENV,
        secret_list=JAG_SECRETS, # Inject secrets
    )

    tasks["jaggaer_preprocess"] = create_task(
        task_id="jaggaer_preprocess",
        python_script_name="pre_process_jaggaer.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="preprod",
        secret_list=JAG_SECRETS, # Inject secrets
    )
    
    # ... (rest of your tasks follow, using the pattern: secret_list=JAG_SECRETS where needed) ...
    
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
    
    # --- Rio Extract Tasks ----
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
    
    # ... (omitting remaining task creation for brevity, assuming similar pattern) ...

    # --- Table Tasks ----

    tables = [
        ("claims", "jaggaer"),
        ("contracts", "jaggaer"),
        ("light_touch_scorecards", "jaggaer"),
        ("spend", "jaggaer"),
        ("rio", "rio"),
    ]

    for table in tables:
        SOURCE_DB_ENV = table[1]
        TABLE_NAME_ENV = table[0]
        
        # Conditionally set secrets based on source
        current_secrets = JAG_SECRETS if SOURCE_DB_ENV == "jaggaer" else None

        name = f"preprod_check_status_{table[0]}"
        tasks[name] = create_task(
            task_id=name,
            python_script_name="get_preprod_check_status.py",
            source_db_env=SOURCE_DB_ENV,
            table_name_env=TABLE_NAME_ENV,
            prod_db_env="preprod",
            secret_list=current_secrets, # Inject secrets only for Jaggaer tables
        )

        name = f"copy_preprod_to_live_{table[0]}"
        tasks[name] = create_task(
            task_id=name,
            python_script_name="copy_preprod_to_live.py",
            source_db_env=SOURCE_DB_ENV,
            table_name_env=TABLE_NAME_ENV,
            prod_db_env="live",
            secret_list=current_secrets, # Inject secrets only for Jaggaer tables
        )
        
    # ... (remaining task definitions and dependencies) ...

    # Ext Database task
    tasks["create_ext_db"] = create_task(
        task_id="create_ext_db",
        python_script_name="create_db.py",
        source_db_env="ext",
        prod_db_env="live",
    )
    
    # Overall Database tasks
    SOURCE_DB_ENV = "all"

    tasks["create_preprod_db"] = create_task(
        task_id="create_preprod_db",
        python_script_name="create_db.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="preprod",
        trigger_rule="all_done",
    )

    tasks["create_live_db"] = create_task(
        task_id="create_live_db",
        python_script_name="create_db.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="live",
        trigger_rule="all_done",
    )

    tasks["preprod_checks"] = create_task(
        task_id="preprod_checks",
        python_script_name="run_preprod_checks.py",
        source_db_env=SOURCE_DB_ENV,
        prod_db_env="preprod",
    )


    # Task Dependencies --- (Unchanged)
    tasks["extract_jaggaer"] >> tasks["jaggaer_preprocess"]
    tasks["jaggaer_preprocess"] >> tasks["lint_jaggaer"]
    tasks["lint_jaggaer"] >> tasks["process_jaggaer"]

    tasks["extract_rio"] >> tasks["lint_rio"]
    tasks["lint_rio"] >> tasks["process_rio"]

    [tasks["process_jaggaer"], tasks["process_rio"]] >> tasks["create_preprod_db"]
    tasks["create_preprod_db"] >> tasks["preprod_checks"]
    tasks["preprod_checks"] >> [
        tasks["preprod_check_status_claims"],
        tasks["preprod_check_status_contracts"],
        tasks["preprod_check_status_light_touch_scorecards"],
        tasks["preprod_check_status_spend"],
        tasks["preprod_check_status_rio"],
    ]

    tasks["preprod_check_status_claims"] >> tasks["copy_preprod_to_live_claims"]
    tasks["preprod_check_status_contracts"] >> tasks["copy_preprod_to_live_contracts"]
    (
        tasks["preprod_check_status_light_touch_scorecards"]
        >> tasks["copy_preprod_to_live_light_touch_scorecards"]
    )
    tasks["preprod_check_status_spend"] >> tasks["copy_preprod_to_live_spend"]
    tasks["preprod_check_status_rio"] >> tasks["copy_preprod_to_live_rio"]

    [
        tasks["copy_preprod_to_live_claims"],
        tasks["copy_preprod_to_live_contracts"],
        tasks["copy_preprod_to_live_light_touch_scorecards"],
        tasks["copy_preprod_to_live_spend"],
    ] >> tasks["create_jaggaer_db"]

    tasks["copy_preprod_to_live_rio"] >> tasks["create_rio_db"]

    [
        tasks["copy_preprod_to_live_claims"],
        tasks["copy_preprod_to_live_contracts"],
        tasks["copy_preprod_to_live_light_touch_scorecards"],
        tasks["copy_preprod_to_live_spend"],
        tasks["copy_preprod_to_live_rio"],
    ] >> tasks["create_live_db"]


    tasks["create_ext_db"]

    tasks["create_jaggaer_db"] >> [tasks["create_jaggaer_extracts"]]

    tasks["create_rio_db"] >> tasks["create_rio_extracts"]git 