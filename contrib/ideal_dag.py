from datetime import datetime

from airflow import DAG, AirflowException
from airflow.decorators import task
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import \
    KubernetesPodOperator
from kubernetes.client import models as k8s_models

# TODO - Review eval() function, should be bool() instead, but bool("False") returns True - go figure...
maintenance_window_active = eval(
    Variable.get("MAINTENANCE_WINDOW_ACTIVE", default_var="False")
)

default_args = {
    "owner": "analytical-platform@justice.gov.uk",
    "depends_on_past": False,
    "email_on_failure": True,
    "start_date": datetime(2020, 1, 1),
}

dag = DAG(
    dag_id="analytical-platform.example",
    max_active_tasks=1,
    schedule_interval=None,
    default_args=default_args,
)


@task(
    task_id="maintenance_window_check",
    default_args={"owner": "analytical-platform@justice.gov.uk"},
)
def maintenance_window_check():
    print(maintenance_window_active)
    if maintenance_window_active:
        raise AirflowException(
            "There is an active maintenance window. Please try again later."
        )
    else:
        pass


maintenance_check = maintenance_window_check()

task = KubernetesPodOperator(
    dag=dag,
    task_id="analytical-platform-example",
    namespace="airflow",
    name="analytical-platform-example",
    image="ghcr.io/ministryofjustice/analytical-platform-airflow-python-base:1.1.0",
    cmds=["sleep", "60"],  # EXPERIMENTAL
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    labels={
        "airflow.compute.analytical-platform.service.justice.gov.uk/environment": "development",
        "airflow.compute.analytical-platform.service.justice.gov.uk/project": "analytical-platform",
    },
    affinity={
        "nodeAffinity": {
            "requiredDuringSchedulingIgnoredDuringExecution": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "compute.analytical-platform.service.justice.gov.uk/karpenter-node-pool",
                                "operator": "In",
                                "values": ["general-spot"],
                            }
                        ]
                    }
                ]
            }
        }
    },
    tolerations=[
        {
            "key": "compute.analytical-platform.service.justice.gov.uk/karpenter-node-pool",
            "operator": "Equal",
            "value": "general-spot",
            "effect": "NoSchedule",
        }
    ],
    container_resources=k8s_models.V1ResourceRequirements(
        requests={"cpu": 2, "memory": "8Gi"}, limits={"cpu": 2, "memory": "8Gi"}
    ),
    security_context={
        "runAsNonRoot": True,
        "runAsUser": 1000,
        # "allowPrivilegeEscalation": False,
        "privileged": False,
    },
    # service_account_name="analytical-platform-example",
    in_cluster=False,
    get_logs=True,
    startup_timeout_seconds=600,
    is_delete_operator_pod=True,
    # This doesn't work when running locally
    config_file="/usr/local/airflow/dags/.kube/config",
)

task << maintenance_check
