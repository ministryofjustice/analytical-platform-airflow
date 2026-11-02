"""
HITL (human-in-the-loop) example, based on:
https://airflow.apache.org/docs/apache-airflow/stable/tutorial/hitl.html
"""
import datetime

try:
    from airflow.sdk import DAG
except ImportError:
    from airflow.models import DAG

try:
    from airflow.sdk.bases.notifier import BaseNotifier
except ImportError:
    from airflow.notifications.basenotifier import BaseNotifier

# HITL operators require Airflow 3.1+; this repo's CI test venv is pinned to
# an older Airflow, so skip building the DAG there rather than crash.
try:
    from airflow.sdk import Param
    from airflow.providers.standard.operators.hitl import (
        ApprovalOperator,
        HITLBranchOperator,
        HITLEntryOperator,
        HITLOperator,
    )
    HITL_AVAILABLE = True
except ImportError:
    HITL_AVAILABLE = False

from data_platform.standard_operator import DataPlatformStandardOperator

REPOSITORY_NAME = "PLACEHOLDER_REPOSITORY_NAME"
REPOSITORY_TAG = "PLACEHOLDER_REPOSITORY_TAG"
PROJECT = "PLACEHOLDER_PROJECT"
WORKFLOW = "PLACEHOLDER_WORKFLOW"
ENVIRONMENT = "PLACEHOLDER_ENVIRONMENT"
OWNER = "PLACEHOLDER_OWNER"

IMAGE = f"509399598587.dkr.ecr.eu-west-2.amazonaws.com/{REPOSITORY_NAME}:{REPOSITORY_TAG}"


def pod(task_id, branch):
    # Base image has no entrypoint of its own, so just prove the chosen branch ran.
    return DataPlatformStandardOperator(
        task_id=task_id,
        name=f"{PROJECT}.{WORKFLOW}-{task_id}",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=[f"echo 'Human chose: {branch}'"],
    )


class LocalLogNotifier(BaseNotifier):
    """Logs HITL request/response events; no external connection required."""

    template_fields = ("message",)

    def __init__(self, message: str) -> None:
        self.message = message

    def notify(self, context) -> None:
        url = HITLOperator.generate_link_to_ui_from_context(context=context)
        self.log.info(self.message)
        self.log.info("Url to respond %s", url)


hitl_request_callback = LocalLogNotifier(
    message="""
[HITL]
Subject: {{ task.subject }}
Body: {{ task.body }}
Options: {{ task.options }}
Is Multiple Option: {{ task.multiple }}
Default Options: {{ task.defaults }}
Params: {{ task.params }}
"""
)
hitl_success_callback = LocalLogNotifier(
    message="{% set task_id = task.task_id -%}{{ ti.xcom_pull(task_ids=task_id) }}"
)
hitl_failure_callback = LocalLogNotifier(message="Request to response to '{{ task.subject }}' failed")

dag_id = f"{PROJECT}.{WORKFLOW}"
if not HITL_AVAILABLE:
    print(f"HITL operators unavailable in this Airflow version; skipping build of {dag_id}")
else:
    with DAG(
    dag_id=dag_id,
    default_args={"owner": OWNER},
    start_date=datetime.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["example", "HITL"],
) as dag:
    wait_for_input = HITLEntryOperator(
        task_id="wait_for_input",
        subject="Please provide required information: ",
        params={"information": Param("", type="string")},
        notifiers=[hitl_request_callback],
        on_success_callback=hitl_success_callback,
        on_failure_callback=hitl_failure_callback,
    )
    wait_for_option = HITLOperator(
        task_id="wait_for_option",
        subject="Please choose one option to proceed: ",
        options=["option 1", "option 2", "option 3"],
        notifiers=[hitl_request_callback],
        on_success_callback=hitl_success_callback,
        on_failure_callback=hitl_failure_callback,
    )
    wait_for_multiple_options = HITLOperator(
        task_id="wait_for_multiple_options",
        subject="Please choose option to proceed: ",
        options=["option 4", "option 5", "option 6"],
        multiple=True,
        notifiers=[hitl_request_callback],
        on_success_callback=hitl_success_callback,
        on_failure_callback=hitl_failure_callback,
    )
    wait_for_default_option = HITLOperator(
        task_id="wait_for_default_option",
        subject="Please choose option to proceed: ",
        options=["option 7", "option 8", "option 9"],
        defaults=["option 7"],
        response_timeout=datetime.timedelta(seconds=1),
        notifiers=[hitl_request_callback],
        on_success_callback=hitl_success_callback,
        on_failure_callback=hitl_failure_callback,
    )
    valid_input_and_options = ApprovalOperator(
        task_id="valid_input_and_options",
        subject="Are the following input and options valid?",
        body="""
        Input: {{ ti.xcom_pull(task_ids='wait_for_input')["params_input"]["information"] }}
        Option: {{ ti.xcom_pull(task_ids='wait_for_option')["chosen_options"] }}
        Multiple Options: {{ ti.xcom_pull(task_ids='wait_for_multiple_options')["chosen_options"] }}
        Timeout Option: {{ ti.xcom_pull(task_ids='wait_for_default_option')["chosen_options"] }}
        """,
        defaults="Reject",
        response_timeout=datetime.timedelta(minutes=5),
        notifiers=[hitl_request_callback],
        on_success_callback=hitl_success_callback,
        on_failure_callback=hitl_failure_callback,
    )
    choose_a_branch_to_run = HITLBranchOperator(
        task_id="choose_a_branch_to_run",
        subject="You're now allowed to proceed. Please choose one task to run: ",
        options=["task_1", "task_2", "task_3"],
        notifiers=[hitl_request_callback],
        on_success_callback=hitl_success_callback,
        on_failure_callback=hitl_failure_callback,
    )

    task_1 = pod("task_1", "task_1")
    task_2 = pod("task_2", "task_2")
    task_3 = pod("task_3", "task_3")

    (
        [wait_for_input, wait_for_option, wait_for_default_option, wait_for_multiple_options]
        >> valid_input_and_options
        >> choose_a_branch_to_run
        >> [task_1, task_2, task_3]
    )
globals()[dag_id] = dag
