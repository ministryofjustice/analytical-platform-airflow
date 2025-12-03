from datetime import datetime
from airflow import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.cncf.kubernetes.secret import (
    Secret,
)


# --- Placeholders ---

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

# --- Image ---
IMAGE = (f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}")

# --- Email ---
DAG_EMAIL = ["philip.neale@justice.gov.uk"]

# --- Default Args ---
default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": DAG_EMAIL,
    "retries": 5,  # From old defaults
}

# --- Default Params ---
default_params = {
    "retries": 0,  # Added based on example format
}

# --- Auth Secret ---
# The deploy_type must be set to 'env' to inject the secret as an environment variable
JAG_PRIVATE_SECRET = Secret(
    # The type of secret (e.g., 'env', 'volume')
    deploy_type='env', #
    # The environment variable name (e.g., 'SECRET_API_KEY')
    deploy_target='SECRET_JAG_PRIVATE_KEY',
    # The name of the Kubernetes Secret resource
    secret=f"{PROJECT}-{WORKFLOW}-JAG_CONTRACTS_KEY", # Use a specific secret name if known, or a placeholder
    # The key within the Secret resource to pull the value from
    key='jag_private_key', # Use a specific key name if known, or a placeholder
)
JAG_HOST_SECRET = Secret(
    # The type of secret (e.g., 'env', 'volume')
    deploy_type='env', #
    # The environment variable name (e.g., 'SECRET_API_KEY')
    deploy_target='SECRET_JAG_HOST_KEY',
    # The name of the Kubernetes Secret resource
    secret=f"{PROJECT}-{WORKFLOW}-HOST_KEY", # Use a specific secret name if known, or a placeholder
    # The key within the Secret resource to pull the value from
    key='jag_host_key', # Use a specific key name if known, or a placeholder
)
CLIENT_ID_SECRET = Secret(
    # The type of secret (e.g., 'env', 'volume')
    deploy_type='env', #
    # The environment variable name (e.g., 'SECRET_API_KEY')
    deploy_target='SECRET_CLIENT_ID_KEY',
    # The name of the Kubernetes Secret resource
    secret=f"{PROJECT}-{WORKFLOW}-CLIENT_ID_KEY", # Use a specific secret name if known, or a placeholder
    # The key within the Secret resource to pull the value from
    key='CLIENT_ID_SECRET', # Use a specific key name if known, or a placeholder
)
CLIENT_SECRET = Secret(
    # The type of secret (e.g., 'env', 'volume')
    deploy_type='env', #
    # The environment variable name (e.g., 'SECRET_API_KEY')
    deploy_target='SECRET_CLIENT_KEY',
    # The name of the Kubernetes Secret resource
    secret=f"{PROJECT}-{WORKFLOW}-CLIENT_KEY", # Use a specific secret name if known, or a placeholder
    # The key within the Secret resource to pull the value from
    key='CLIENT_SECRET', # Use a specific key name if known, or a placeholder
)


# A list of secrets to be applied to all tasks

SECRETS = [
    JAG_PRIVATE_SECRET,
    JAG_HOST_SECRET,
    CLIENT_ID_SECRET,
    CLIENT_SECRET
]

# --- DAG ---
dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description="Contracts data pipeline",
    start_date=datetime(2022, 5, 20),
    schedule_interval="40 04 * * *",
    params=default_params,
    catchup=False,
    max_active_tasks=1,
)

tasks = {}

PRODUCTION_ENV = "preprod"
DATABASE_VERSION = "dev"  # From old file, used in env_vars

# --- Task Definitions ---

# create jaggaer and rio tasks
dbs = [("jaggaer", "raw_to_curated.py"), ("rio", "rio_raw_hist_to_curated.py")]

for db in dbs:
    DATABASE_NAME = db[0]

    task_id = f"extract_{DATABASE_NAME}"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        compute_profile="general-on-demand-1vcpu-4gb",  # Added default
        image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": f"{DATABASE_NAME}_to_land.py",
            "AIRFLOW__CORE__LOGGING_LEVEL": "DEBUG",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
        },
    )

    task_id = f"lint_{DATABASE_NAME}"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": "land_to_raw_hist.py",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
        },

    )

    task_id = f"process_{DATABASE_NAME}"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": db[1],
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
            "PROD_DB_ENV": "preprod",
        },

    )

    task_id = f"create_{DATABASE_NAME}_db"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        trigger_rule="all_done",
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": "create_db.py",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
            "PROD_DB_ENV": "live",
        },

    )

    task_id = f"create_{DATABASE_NAME}_extracts"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": "create_app_extracts.py",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
            "PROD_DB_ENV": "live",
        },

    )

# these are tables we run extracts from and can get preprod
# check results for each independently
tables = [
    ("claims", "jaggaer"),
    ("contracts", "jaggaer"),
    ("light_touch_scorecards", "jaggaer"),
    ("spend", "jaggaer"),
    ("rio", "rio"),
    ("risk_category", "rio"),
]

for table in tables:
    DATABASE_NAME = table[1]

    task_id = f"preprod_check_staus_{table[0]}"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        retries=1,  # Note: Preserved task-specific retry from old file
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": "get_preprod_check_status.py",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "TABLE_NAME_ENV": table[0],
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
            "PROD_DB_ENV": "preprod",
        },

    )

    task_id = f"copy_preprod_to_live_{table[0]}"
    tasks[task_id] = AnalyticalPlatformStandardOperator(
        dag=dag,
        task_id=task_id,
        name=task_id,
        compute_profile="general-on-demand-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        secrets=SECRETS,
        env_vars={
            "PYTHON_SCRIPT_NAME": "copy_preprod_to_live.py",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "IMAGE_VERSION": REPOSITORY_TAG,
            "DEFAULT_DB_ENV": DATABASE_VERSION,
            "SOURCE_DB_ENV": DATABASE_NAME,
            "TABLE_NAME_ENV": table[0],
            "AWS_DEFAULT_REGION": "eu-west-1",
            "GITHUB_TAG": REPOSITORY_TAG,
            "PROD_DB_ENV": "live",
        },

    )

# change env var for different db
DATABASE_NAME = "ext"

# create db for external tables
task_id = "create_ext_db"
tasks[task_id] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id,
    name=task_id,
    compute_profile="general-on-demand-1vcpu-4gb",
    image=IMAGE,
    environment=ENVIRONMENT,
    project=PROJECT,
    workflow=WORKFLOW,
    secrets=SECRETS,
    env_vars={
        "PYTHON_SCRIPT_NAME": "create_db.py",
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "IMAGE_VERSION": REPOSITORY_TAG,
        "DEFAULT_DB_ENV": DATABASE_VERSION,
        "SOURCE_DB_ENV": DATABASE_NAME,
        "AWS_DEFAULT_REGION": "eu-west-1",
        "GITHUB_TAG": REPOSITORY_TAG,
        "PROD_DB_ENV": "live",
    },

)

# create overall database with all data
DATABASE_NAME = "all"

task_id = "create_preprod_db"
tasks[task_id] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id,
    name=task_id,
    trigger_rule="all_done",
    compute_profile="general-on-demand-1vcpu-4gb",
    image=IMAGE,
    environment=ENVIRONMENT,
    project=PROJECT,
    workflow=WORKFLOW,
    secrets=SECRETS,
    env_vars={
        "PYTHON_SCRIPT_NAME": "create_db.py",
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "IMAGE_VERSION": REPOSITORY_TAG,
        "DEFAULT_DB_ENV": DATABASE_VERSION,
        "SOURCE_DB_ENV": DATABASE_NAME,
        "AWS_DEFAULT_REGION": "eu-west-1",
        "GITHUB_TAG": REPOSITORY_TAG,
        "PROD_DB_ENV": "preprod",
    },

)

task_id = "create_live_db"
tasks[task_id] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id,
    name=task_id,
    trigger_rule="all_done",
    compute_profile="general-on-demand-1vcpu-4gb",
    image=IMAGE,
    environment=ENVIRONMENT,
    project=PROJECT,
    workflow=WORKFLOW,
    secrets=SECRETS,
    env_vars={
        "PYTHON_SCRIPT_NAME": "create_db.py",
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "IMAGE_VERSION": REPOSITORY_TAG,
        "DEFAULT_DB_ENV": DATABASE_VERSION,
        "SOURCE_DB_ENV": DATABASE_NAME,
        "AWS_DEFAULT_REGION": "eu-west-1",
        "GITHUB_TAG": REPOSITORY_TAG,
        "PROD_DB_ENV": "live",
    },

)

task_id = "preprod_checks"
tasks[task_id] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id,
    name=task_id,
    retries=0,  # Note: Preserved task-specific retry from old file
    compute_profile="general-on-demand-1vcpu-4gb",
    image=IMAGE,
    environment=ENVIRONMENT,
    project=PROJECT,
    workflow=WORKFLOW,
    secrets=SECRETS,
    env_vars={
        "PYTHON_SCRIPT_NAME": "run_preprod_checks.py",
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "IMAGE_VERSION": REPOSITORY_TAG,
        "DEFAULT_DB_ENV": DATABASE_VERSION,
        "SOURCE_DB_ENV": DATABASE_NAME,
        "AWS_DEFAULT_REGION": "eu-west-1",
        "GITHUB_TAG": REPOSITORY_TAG,
        "PROD_DB_ENV": "preprod",
    },

)

task_id = "jaggaer_preprocess"
tasks[task_id] = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=task_id,
    name=task_id,
    retries=0,  # Note: Preserved task-specific retry from old file
    compute_profile="general-on-demand-1vcpu-4gb",
    image=IMAGE,
    environment=ENVIRONMENT,
    project=PROJECT,
    workflow=WORKFLOW,
    secrets=SECRETS,
    env_vars={
        "PYTHON_SCRIPT_NAME": "pre_process_jaggaer.py",
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "IMAGE_VERSION": REPOSITORY_TAG,
        "DEFAULT_DB_ENV": DATABASE_VERSION,
        "SOURCE_DB_ENV": "jaggaer",
        "AWS_DEFAULT_REGION": "eu-west-1",
        "GITHUB_TAG": REPOSITORY_TAG,
        "PROD_DB_ENV": "preprod",
    },

)

# --- Task Dependencies ---
# This is copied directly from your old file, as all task_ids match.

tasks["extract_jaggaer"] >> tasks["jaggaer_preprocess"]
tasks["jaggaer_preprocess"] >> tasks["lint_jaggaer"]
tasks["lint_jaggaer"] >> tasks["process_jaggaer"]

tasks["extract_rio"] >> tasks["lint_rio"]
tasks["lint_rio"] >> tasks["process_rio"]

[tasks["process_jaggaer"], tasks["process_rio"]] >> tasks["create_preprod_db"]
tasks["create_preprod_db"] >> tasks["preprod_checks"]
tasks["preprod_checks"] >> [
    tasks["preprod_check_staus_claims"],
    tasks["preprod_check_staus_contracts"],
    tasks["preprod_check_staus_light_touch_scorecards"],
    tasks["preprod_check_staus_spend"],
    tasks["preprod_check_staus_rio"],
]

tasks["preprod_check_staus_claims"] >> tasks["copy_preprod_to_live_claims"]
tasks["preprod_check_staus_contracts"] >> tasks["copy_preprod_to_live_contracts"]
(
    tasks["preprod_check_staus_light_touch_scorecards"]
    >> tasks["copy_preprod_to_live_light_touch_scorecards"]
)
tasks["preprod_check_staus_spend"] >> tasks["copy_preprod_to_live_spend"]
tasks["preprod_check_staus_rio"] >> tasks["copy_preprod_to_live_rio"]

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

tasks["create_rio_db"] >> tasks["create_rio_extracts"]
