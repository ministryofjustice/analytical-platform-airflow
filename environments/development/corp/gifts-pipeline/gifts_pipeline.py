from datetime import datetime
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

# DECLARE ENV VARIABLES
GITHUB_TAG = 'v3.0.4'
PIPELINE = 'airflow-gifts-pipeline'
IMAGE = f"189157455002.dkr.ecr.eu-west-1.amazonaws.com/{PIPELINE}:{GITHUB_TAG}"
IAM_ROLE = "airflow_prod_gifts"
SNAPSHOT_DATE = datetime.now().strftime("%Y-%m-%d")
EXPORT_SCRIPT = 'export_extracts.py'
NAMESPACE = 'airflow'

task_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": "glenn-christmas",  # your GitHub username
    "email": ["glenn.christmas@justice.gov.uk"],
}

dag = DAG(
    "gifts.gifts_pipeline",
    default_args=task_args,
    description="Gifts reporting app pipeline",
    start_date=datetime(2020, 12, 1),
    schedule_interval='00 16 * * *',
    catchup=False
)

tasks = {}

task_id = "export"
tasks[task_id] = KubernetesPodOperator(
    dag=dag,
    namespace=NAMESPACE,
    image=IMAGE,
    env_vars={
        "PYTHON_SCRIPT_NAME": EXPORT_SCRIPT,
        "AWS_METADATA_SERVICE_TIMEOUT": "60",
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5"
    },
    labels={"app": dag.dag_id},
    name=task_id,
    in_cluster=False,
    task_id=task_id,
    get_logs=True,
    annotations={"iam.amazonaws.com/role": IAM_ROLE},
    security_context={
        "runAsNonRoot": True,
        "allowPrivilegeEscalation": False,
        "runAsUser": 1337,
        "privileged": False,
    },
    is_delete_operator_pod=True,
    cluster_context="aws",
    config_file="/usr/local/airflow/dags/.kube/config"
)

tasks['export']
