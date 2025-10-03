from datetime import datetime
from airflow.models import DAG
from airflow.providers.slack.notifications.slack import send_slack_notification
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.cncf.kubernetes.secret import Secret

# Configuration for testing
REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"
SLACK_CHANNEL = "analytical-platform-airflow-testing"  # Use test channel

DAG_EMAIL = [
    "william.orr@justice.gov.uk",
]

def slack_failure_callback(context):
    return send_slack_notification(
        channel=SLACK_CHANNEL,
        text=f":airflow: *Airflow {ENVIRONMENT.capitalize()}*\n"
             f":x: {PROJECT}.{WORKFLOW} has failed.\n"
             f"*Task*: {context['ti'].task_id}\n"
             f"*Logs*: {context['ti'].log_url}"
    )

def slack_success_callback(context):
    return send_slack_notification(
        channel=SLACK_CHANNEL,
        text=f":airflow: *Airflow {ENVIRONMENT.capitalize()}*\n"
             f":white_check_mark: {PROJECT}.{WORKFLOW} has succeeded.\n"
             f"*Task*: {context['ti'].task_id}\n"
             f"*Logs*: {context['ti'].log_url}"
    )

default_args = {
    "depends_on_past": False,
    "email_on_failure": True,
    "owner": f"{OWNER}",
    "email": DAG_EMAIL,
    "retries": 0,  # No retries for testing
}

# Test DAG with Slack notifications
dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    on_failure_callback=slack_failure_callback,
    on_success_callback=slack_success_callback,
    tags=["slack-notification-test"],
)

# Task that will succeed - tests success notification
success_task = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="test_success_notification",
    name=f"{PROJECT}.{WORKFLOW}.success",
    compute_profile="general-spot-1vcpu-4gb",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "TEST_TYPE": "success",
    },
)

# Task that will fail - tests failure notification
failure_task = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="test_failure_notification", 
    name=f"{PROJECT}.{WORKFLOW}.failure",
    compute_profile="general-spot-1vcpu-4gb",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "TEST_TYPE": "failure",
    },
)