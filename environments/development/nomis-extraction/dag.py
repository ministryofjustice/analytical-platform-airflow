from datetime import datetime

from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from imports.nomis_constants import PK_EXCEPTIONS, PK_EXTRACTIONS, email, owner, tags
from imports.high_memory_constants import tolerations, affinity

IMAGE_VERSION = "v3.10.21"
REPO = "airflow-nomis-ap"
BUILD_IMAGE = f"{REPO}:{IMAGE_VERSION}"
IMAGE = f"189157455002.dkr.ecr.eu-west-1.amazonaws.com/{BUILD_IMAGE}"
ROLE = "airflow_prod_nomis_extraction"

DELTA_FETCH_SIZE = "100000"
RM_FETCH_SIZE = "300000"

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
    dag_id="nomis.nomis_extraction",
    default_args=task_args,
    description="Extract data from the NOMIS T62 Database",
    start_date=datetime(2022, 6, 12),
    schedule_interval="00 01 * * *",
    catchup=False,
    tags=tags,
)

tasks = dict()

# Trigger for downstream pipeline
dep_dag_id = "nomis.nomis_transform"

tasks[f"trigger_for_{dep_dag_id}"] = TriggerDagRunOperator(
    task_id=f"trigger_{dep_dag_id}", trigger_dag_id=f"{dep_dag_id}"
)

task_id = "nomis-delta-extract"
tasks[task_id] = KubernetesPodOperator(
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
        "ENV": "PRODUCTION",
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

task_id = "nomis-delta-extract-check"
tasks[task_id] = KubernetesPodOperator(
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
        "ENV": "PRODUCTION",
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
    >> tasks[f"trigger_for_{dep_dag_id}"]
)

# Deletes
for i, L in PK_EXTRACTIONS.items():
    if i in PK_EXCEPTIONS and datetime.now().day not in PK_EXCEPTIONS[i]:
        continue
    tables_string = ",".join(L)
    task_id = f"nomis-pk-deletes-extract-{i}"
    tasks[task_id] = KubernetesPodOperator(
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
            "ENV": "PRODUCTION",
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

    task_id = f"nomis-pk-deletes-extract-check-{i}"
    tasks[task_id] = KubernetesPodOperator(
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
            "ENV": "PRODUCTION",
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
        >> tasks[f"trigger_for_{dep_dag_id}"]
    )
