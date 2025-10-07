from datetime import datetime
from airflow.models import DAG
from airflow.providers.slack.notifications.slack import SlackNotifier
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator
from airflow.providers.cncf.kubernetes.secret import Secret

# Configuration for testing
REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"
SLACK_CHANNEL = "dmet-corp-notifications"

DAG_EMAIL = [
    "william.orr@justice.gov.uk",
]

# Define Slack notifiers
slack_notifier_success = SlackNotifier(
    slack_conn_id="slack_api_default",
    text=":airflow: *Airflow {{ var.value.environment | capitalize }}*\n"
         ":white_check_mark: {{ dag.dag_id }} has succeeded.\n"
         "*Task*: {{ ti.task_id }}\n"
         "*Logs*: {{ ti.log_url }}",
    channel=SLACK_CHANNEL,
)

slack_notifier_failure = SlackNotifier(
    slack_conn_id="slack_api_default",
    text=":airflow: *Airflow {{ var.value.environment | capitalize }}*\n"
         ":x: {{ dag.dag_id }} has failed.\n"
         "*Task*: {{ ti.task_id }}\n"
         "*Logs*: {{ ti.log_url }}",
    channel=SLACK_CHANNEL,
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
    tags=["slack-notification-test"],
)

# Task that will succeed - tests success notification
success_task = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="test_success_notification",
    name=f"{PROJECT}.{WORKFLOW}.success",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    compute_profile="general-spot-1vcpu-4gb",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "TEST_TYPE": "success",
    },
    on_failure_callback=[slack_notifier_failure],
    on_success_callback=[slack_notifier_success],
)

# Task that will fail - tests failure notification
failure_task = AnalyticalPlatformStandardOperator(
    dag=dag,
    task_id="test_failure_notification",
    name=f"{PROJECT}.{WORKFLOW}.failure",
    image=f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}",
    compute_profile="general-spot-1vcpu-4gb",
    environment=f"{ENVIRONMENT}",
    project=f"{PROJECT}",
    workflow=f"{WORKFLOW}",
    env_vars={
        "TEST_TYPE": "failure",
    },
    on_failure_callback=[slack_notifier_failure],
    on_success_callback=[slack_notifier_success],
)
