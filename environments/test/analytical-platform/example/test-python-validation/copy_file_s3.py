from datetime import datetime
from airflow.models import DAG

from imports.analytical_platform_compute_profiles import get_compute_profile
from mojap_airflow_tools.operators import BasicKubernetesPodOperator


username = "jhypke"
# As defined in the image repo
IMAGE_TAG = "v0.0.1"
REPO_NAME = f"airflow-{username}-python"
USER_ID = 1337

# ROLE = re.sub(r"[\W]+", "", f"airflow_dev_{username}_example")
ROLE = f"airflow_dev_{username}_python"
SERVICE_ACCOUNT_NAME = ROLE.replace("_", "-")

compute_profile = get_compute_profile(compute_profile="general-on-demand-2vcpu-8gb")

# For tips/advice on the default args see the use_dummy_operator.py example
default_args = {
    # Normally you want to set this to False.
    "depends_on_past": False,
    "email_on_failure": False,
    # Name of DAG owner as it will appear on Airflow UI
    "owner": f"{username}",
}

dag = DAG(
    # Name of the dag (how it will appear on the Airflow UI)
    # We use the naming convention: <folder_name>.<filename>
    dag_id=f"{username}.copy_file_s3",
    default_args=default_args,
    description="A basic Kubernetes DAG",
    # Requires a start_date as a datetime object. This will be when the
    # DAG will start running from. DO NOT use datetime.now().
    start_date=datetime(2022, 1, 1),
    # How often should I run the dag. If set to None your dag
    # will only run when manually triggered.
    schedule_interval=None,
)

# Environmental variables for passing to the docker container
env_vars = {
    "RUN": "write",
    "TEXT": "Hello world",
    "OUTPATH": f"s3://alpha-everyone/airflow-example/{username}/test.txt",
    "AWS_METADATA_SERVICE_TIMEOUT": "60",
    "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5"
}

task_id = "task-1"
task = BasicKubernetesPodOperator(
    dag=dag,
    run_as_user=USER_ID,
    repo_name=REPO_NAME,
    release=IMAGE_TAG,
    role=ROLE,
    task_id=task_id,
    env_vars=env_vars,
    service_account_name=SERVICE_ACCOUNT_NAME,
    environment="dev",
    # COMPUTE PROFILE SECTION
    annotations=compute_profile["annotations"],
    tolerations=compute_profile["tolerations"],
    affinity=compute_profile["affinity"],
    container_resources=compute_profile["container_resources"]
)

task
