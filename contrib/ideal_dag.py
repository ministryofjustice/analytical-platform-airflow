from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from kubernetes.client import models as k8s_models

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

task = KubernetesPodOperator(
    dag=dag,
    task_id="analytical-platform-example",
    namespace="airflow",
    name="analytical-platform-example",
    image="ghcr.io/ministryofjustice/analytical-platform-airflow-python-base:1.1.0",
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
        "allowPrivilegeEscalation": False,
        "privileged": False,
    },
    service_account_name="analytical-platform-example",
    in_cluster=False,
    get_logs=True,
    startup_timeout_seconds=600,
    is_delete_operator_pod=True,
    # This doesn't work when running locally
    # cluster_context="analytical-platform-compute-development",
    # config_file="/usr/local/airflow/dags/.kube/config",
)

task.dry_run()
