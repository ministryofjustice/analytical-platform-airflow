from datetime import datetime

from airflow.models import DAG
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

REPOSITORY_NAME="PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG="PLACEHOLDER_REPOSITORY_TAG"
PROJECT="PLACEHOLDER_PROJECT"
WORKFLOW="PLACEHOLDER_WORKFLOW"
ENVIRONMENT="PLACEHOLDER_ENVIRONMENT"
OWNER="PLACEHOLDER_OWNER"

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": [
        "dugald.hepburn@justice.gov.uk"
    ],
}


dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description="Preprocesses CJSM Email Logs",
    start_date=datetime(2022, 3, 1),
    schedule_interval="0 20 8-28 * *",
    catchup=False,
)

# Function to decide the next step based on XCom output
def decide_next_step(**kwargs):
    # Extract task instance (ti) from kwargs
    ti = kwargs["ti"]

    # Pull the value from XCom using the specified key and task ID
    next_step = ti.xcom_pull(
        task_ids=kwargs["xcom_push_id"]
    )

    print(f"next_step value: {next_step}")
    # Determine the next task based on the retrieved XCom value
    if next_step == kwargs["proceed_output"]:
        return kwargs["next_task_id"]  # Proceed to the next task
    else:
        return kwargs["skip_task_id"]  # Skip to the exit task


# Expected value from the first script to proceed picked up by xcom
proceed_process_value = {"result": "run pre-processing scripts"}
# Task ID of the first script
deciding_task_id = "process-decider"
# Task id for branching logic
branching_task_id = "branching"
# Task ID to run if condition matches
first_process_task_id = "clean-logs"
# Task ID to run if condition does not match
skip_process_task_id = "exit-process"
# Name of follow-up task to ensure the DAG concludes
follow_up_task_id = "follow-up"

# scripts
processcheck_script_name = "processing_step_check.R"
first_process_script_name = "run_all.R"

# Task: Decide if processing is needed
decider = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=deciding_task_id,
    name=f"{PROJECT}.{WORKFLOW}.{deciding_task_id}",
    compute_profile="general-spot-1vcpu-4gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "AWS_DEFAULT_REGION": "eu-west-1",
        "RSCRIPTNAME": processcheck_script_name,
    },
    do_xcom_push=True,
)

# Task: Branching based on decision
branch = BranchPythonOperator(
    task_id=branching_task_id,
    python_callable=decide_next_step,
    op_kwargs={
        "xcom_push_id": deciding_task_id,
        "next_task_id": first_process_task_id,
        "skip_task_id": skip_process_task_id,
        "proceed_output": proceed_process_value,
    },
    dag=dag,
)

# Task: Clean logs
clean_logs = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id=first_process_task_id,
    name=f"{PROJECT}.{WORKFLOW}.{first_process_task_id}",
    compute_profile="general-on-demand-4vcpu-16gb",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "AWS_DEFAULT_REGION": "eu-west-1",
        "RSCRIPTNAME": first_process_script_name,
    },
)

# Task: Dummy task if skipping process
skip_process = EmptyOperator(
    task_id=skip_process_task_id,
    dag=dag,
)

# Task: Final task after either path
follow_up = EmptyOperator(
    task_id=follow_up_task_id,
    trigger_rule="none_failed_or_skipped",
    dag=dag,
)

# DAG structure
decider >> branch >> [clean_logs, skip_process] >> follow_up
