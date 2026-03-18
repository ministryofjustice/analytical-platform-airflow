from datetime import datetime

from airflow.models import DAG
from airflow.utils.trigger_rule import TriggerRule
from analytical_platform.standard_operator import AnalyticalPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "owner": f"{OWNER}",
}

dag = DAG(
    dag_id=f"{PROJECT}.{WORKFLOW}",
    default_args=default_args,
    description="Online scorecard notifications pipeline",
    start_date=datetime(2025, 6, 26),
    schedule="0 9 * * *",
    catchup=False,
)

COMMON_ENV_VARS = {
    "AWS_METADATA_SERVICE_TIMEOUT": "60",
    "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
}

IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"


def make_task(task_id, python_script_name, extra_env_vars=None, trigger_rule=None):
    env_vars = {
        "PYTHON_SCRIPT_NAME": python_script_name,
        **COMMON_ENV_VARS,
    }
    if extra_env_vars:
        env_vars.update(extra_env_vars)

    kwargs = {
        "dag": dag,
        "task_id": task_id,
        "name": f"{PROJECT}.{WORKFLOW}.{task_id}",
        "compute_profile": "general-spot-1vcpu-4gb",
        "image": IMAGE,
        "environment": f"{ENVIRONMENT}",
        "project": f"{PROJECT}",
        "workflow": f"{WORKFLOW}",
        "env_vars": env_vars,
    }

    if trigger_rule:
        kwargs["trigger_rule"] = trigger_rule

    return AnalyticalPlatformStandardOperator(**kwargs)


dates = make_task(
    task_id="dates",
    python_script_name="date_check.py",
)

condition_commission = make_task(
    task_id="condition_commission",
    python_script_name="notification_check.py",
    extra_env_vars={"TEMPLATE_NAME": "commission"},
)

condition_reminder = make_task(
    task_id="condition_reminder",
    python_script_name="notification_check.py",
    extra_env_vars={"TEMPLATE_NAME": "reminder"},
)

condition_deadline = make_task(
    task_id="condition_deadline",
    python_script_name="notification_check.py",
    extra_env_vars={"TEMPLATE_NAME": "deadline"},
)

condition_follow1 = make_task(
    task_id="condition_follow1",
    python_script_name="notification_check.py",
    extra_env_vars={"TEMPLATE_NAME": "follow1"},
)

condition_follow2 = make_task(
    task_id="condition_follow2",
    python_script_name="notification_check.py",
    extra_env_vars={"TEMPLATE_NAME": "follow2"},
)

notify = make_task(
    task_id="notify",
    python_script_name="send_emails.py",
    trigger_rule=TriggerRule.ALL_DONE,
)

ptg_notify = make_task(
    task_id="ptg_notify",
    python_script_name="send_ptg.py",
    trigger_rule=TriggerRule.ALL_DONE,
)

dates >> [
    condition_commission,
    condition_reminder,
    condition_deadline,
    condition_follow1,
    condition_follow2,
]

[
    condition_commission,
    condition_reminder,
    condition_deadline,
    condition_follow1,
    condition_follow2,
] >> notify

notify >> ptg_notify