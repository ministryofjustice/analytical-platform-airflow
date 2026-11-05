"""
HITL (human-in-the-loop) example with dynamic task mapping: a simulated
training task produces metric scores, a weak-metric check flags which ones
missed their threshold, and one Approve/Reject HITL prompt is created per
weak metric found (so the number and content of prompts is decided entirely
by the previous task's output).
"""
import datetime
import random

try:
    from airflow.sdk import DAG, task
except ImportError:
    from airflow.decorators import task
    from airflow.models import DAG

try:
    from airflow.sdk import TriggerRule
except ImportError:
    from airflow.utils.trigger_rule import TriggerRule

# HITL operators require Airflow 3.1+; this repo's CI test venv is pinned to
# an older Airflow, so skip building the DAG there rather than crash.
try:
    from airflow.providers.standard.operators.hitl import ApprovalOperator
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

# Weak if the score is below the threshold, except latency_ms which is weak if above it.
THRESHOLDS = {
    "accuracy": 0.90,
    "precision": 0.85,
    "recall": 0.75,
    "f1": 0.80,
    "latency_ms": 100,
}


def pod(task_id, message, **kwargs):
    # Base image has no entrypoint of its own, so just prove the task ran.
    return DataPlatformStandardOperator(
        task_id=task_id,
        name=f"{PROJECT}.{WORKFLOW}-{task_id}",
        compute_profile="general-spot-1vcpu-4gb",
        image=IMAGE,
        environment=ENVIRONMENT,
        project=PROJECT,
        workflow=WORKFLOW,
        cmds=["/bin/bash", "-c"],
        arguments=[f"echo '{message}'"],
        **kwargs,
    )


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

        @task
        def train_model():
            return {
                "accuracy": round(random.uniform(0.75, 0.95), 2),
                "precision": round(random.uniform(0.70, 0.95), 2),
                "recall": round(random.uniform(0.60, 0.90), 2),
                "f1": round(random.uniform(0.65, 0.92), 2),
                "latency_ms": random.randint(50, 150),
            }

        @task
        def identify_weak_metrics(scores):
            weak = [
                metric
                for metric in ("accuracy", "precision", "recall", "f1")
                if scores[metric] < THRESHOLDS[metric]
            ]
            if scores["latency_ms"] > THRESHOLDS["latency_ms"]:
                weak.append("latency_ms")
            return weak

        @task
        def build_subjects(weak_metrics):
            return [
                f"The model's '{metric}' score was weak. Approve retraining to address it?"
                for metric in weak_metrics
            ]

        scores = train_model()
        weak_metrics = identify_weak_metrics(scores)
        subjects = build_subjects(weak_metrics)

        approve_retrain = ApprovalOperator.partial(
            task_id="approve_retrain",
            body="Full training scores: {{ ti.xcom_pull(task_ids='train_model') }}",
            response_timeout=datetime.timedelta(minutes=30),
            map_index_template="{{ task.subject }}",
        ).expand(subject=subjects)

        promote_to_staging = pod(
            "promote_to_staging",
            "promoted to staging",
            trigger_rule=TriggerRule.NONE_FAILED,
        )

        approve_retrain >> promote_to_staging
    globals()[dag_id] = dag
