
from datetime import datetime
from airflow.models import DAG
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.slack.notifications.slack import send_slack_notification
from airflow.providers.cncf.kubernetes.secret import (
    Secret,
)
from nomis_constants import PK_EXCEPTIONS, PK_EXTRACTIONS, email, owner, tags
from high_memory_constants import tolerations, affinity

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

task_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "owner": owner,
    "email": email,
    "retries": 2,
    "retry_delay": 300,
}

dag = DAG(
    dag_id="new_nomis_extraction",
    default_args=task_args,
    description="Extract data from the NOMIS T62 Database",
    start_date=datetime(2025, 11, 01),
    schedule_interval="00 01 * * *",
    catchup=False,
    tags=tags,
)

tasks = {}

tasks["initalise-dag"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    namespace="airflow",
    image=IMAGE,
    env_vars={
        "PYTHON_SCRIPT_NAME": "initialise_dag.py",
        "NOMIS_T62_FETCH_SIZE": DELTA_FETCH_SIZE,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "BUILD_IMAGE": BUILD_IMAGE,
        "DAG_ID": dag.dag_id,
#        "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
        "DAG_RUN_UTC_UNIXTIME": str(int(datetime.utcnow().timestamp())),
    },
    startup_timeout_seconds=600,
    pool="nomis_tasks",
    labels={"app": dag.dag_id},
    name=task_id,
    task_id=task_id,
    get_logs=True,
    in_cluster=False,
    security_context={
        "runAsNonRoot": True,
        "allowPrivilegeEscalation": False,
        "runAsUser": 1337,
        "privileged": False,
    },
    is_delete_operator_pod=True,
    cluster_context="analytical-platform-compute-production",
    service_account_name=ROLE.replace("_", "-"),
    config_file="/usr/local/airflow/dags/.kube/config",
    tolerations=tolerations,
    affinity=affinity,
)


tasks["nomis-delta-extract"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    namespace="airflow",
    image=IMAGE,
    env_vars={
        "PYTHON_SCRIPT_NAME": "nomis_delta_extract.py",
        "NOMIS_T62_FETCH_SIZE": DELTA_FETCH_SIZE,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "BUILD_IMAGE": BUILD_IMAGE,
        "DAG_ID": dag.dag_id,
 #       "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
    },
    startup_timeout_seconds=600,
    pool="nomis_tasks",
    labels={"app": dag.dag_id},
    name=task_id,
    task_id=task_id,
    get_logs=True,
    in_cluster=False,
    security_context={
        "runAsNonRoot": True,
        "allowPrivilegeEscalation": False,
        "runAsUser": 1337,
        "privileged": False,
    },
    is_delete_operator_pod=True,
    cluster_context="analytical-platform-compute-production",
    service_account_name=ROLE.replace("_", "-"),
    config_file="/usr/local/airflow/dags/.kube/config",
    tolerations=tolerations,
    affinity=affinity,
)

tasks["nomis-delta-extract-check"] = AnalyticalPlatformStandardOperator(
    dag=dag,
    namespace="airflow",
    image=IMAGE,
    env_vars={
        "PYTHON_SCRIPT_NAME": "test_extraction_outputs_and_move_to_raw.py",
        "NOMIS_T62_FETCH_SIZE": DELTA_FETCH_SIZE,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        "BUILD_IMAGE": BUILD_IMAGE,
        "DAG_ID": dag.dag_id,
  #      "ENV": "PRODUCTION",
        "ENV": "DEVELOPMENT",
    },
    startup_timeout_seconds=300,
    pool="nomis_tasks",
    labels={"app": dag.dag_id},
    name=task_id,
    task_id=task_id,
    get_logs=True,
    in_cluster=False,
    security_context={
        "runAsNonRoot": True,
        "allowPrivilegeEscalation": False,
        "runAsUser": 1337,
        "privileged": False,
    },
    is_delete_operator_pod=True,
    cluster_context="analytical-platform-compute-production",
    service_account_name=ROLE.replace("_", "-"),
    config_file="/usr/local/airflow/dags/.kube/config",
)

# Set dependencies
(
    tasks["nomis-delta-extract"]
    >> tasks["nomis-delta-extract-check"]
    >> tasks["initialise_dag"]
)

# Deletes
for i, L in PK_EXTRACTIONS.items():
    if i in PK_EXCEPTIONS and datetime.now().day not in PK_EXCEPTIONS[i]:
        continue
    tables_string = ",".join(L)
    tasks[f"nomis-pk-deletes-extracts-{i}"] = AnalyticalPlatformStandardOperator(
        dag=dag,
        namespace="airflow",
        image=IMAGE,
        env_vars={
            "PK_EXTRACT_TABLES": tables_string,
            "PYTHON_SCRIPT_NAME": "nomis_deletes_extract.py",
            "NOMIS_T62_FETCH_SIZE": RM_FETCH_SIZE,
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "BUILD_IMAGE": BUILD_IMAGE,
            "DAG_ID": dag.dag_id,
   #         "ENV": "PRODUCTION",
            "ENV": "DEVELOPMENT",
        },
        startup_timeout_seconds=300,
        pool="nomis_tasks",
        labels={"app": dag.dag_id},
        name=task_id,
        task_id=task_id,
        get_logs=True,
        in_cluster=False,
        security_context={
            "runAsNonRoot": True,
            "allowPrivilegeEscalation": False,
            "runAsUser": 1337,
            "privileged": False,
        },
        is_delete_operator_pod=True,
        cluster_context="analytical-platform-compute-production",
        service_account_name=ROLE.replace("_", "-"),
        config_file="/usr/local/airflow/dags/.kube/config",
    )

    tasks[f"nomis-pk-deletes-extract-check-{i}"] = AnalyticalPlatformStandardOperator(
        dag=dag,
        namespace="airflow",
        image=IMAGE,
        env_vars={
            "PK_EXTRACT_TABLES": tables_string,
            "PYTHON_SCRIPT_NAME": "test_deletes_extraction_outputs_and_move_to_raw.py",
            "NOMIS_T62_FETCH_SIZE": RM_FETCH_SIZE,
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "BUILD_IMAGE": BUILD_IMAGE,
            "DAG_ID": dag.dag_id,
    #        "ENV": "PRODUCTION",
            "ENV": "DEVELOPMENT",
        },
        startup_timeout_seconds=300,
        pool="nomis_tasks",
        labels={"app": dag.dag_id},
        name=task_id,
        task_id=task_id,
        get_logs=True,
        in_cluster=False,
        security_context={
            "runAsNonRoot": True,
            "allowPrivilegeEscalation": False,
            "runAsUser": 1337,
            "privileged": False,
        },
        is_delete_operator_pod=True,
        cluster_context="analytical-platform-compute-production",
        service_account_name=ROLE.replace("_", "-"),
        config_file="/usr/local/airflow/dags/.kube/config",
    )

    (
        tasks[f"nomis-pk-deletes-extract-{i}"]
        >> tasks[f"nomis-pk-deletes-extract-check-{i}"]
        >> tasks["initialise_dag"]

    )
