from typing import Optional

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from analytical_platform.compute_profiles import get_compute_profile


class AnalyticalPlatformStandardOperator(KubernetesPodOperator):
    def __init__(
        self,
        task_id: str,
        compute_profile: str,
        name: str,
        image: str,
        environment: str,
        project: str,
        workflow: str,
        env_vars: Optional[dict] = None,
        *args,
        **kwargs,
    ):

        compute_profile = get_compute_profile(compute_profile=compute_profile)

        if env_vars is None:
            env_vars = {}

        std_envs = {
            "AWS_DEFAULT_REGION": "eu-west-1",
            "AWS_ATHENA_QUERY_EXTRACT_REGION": "eu-west-1",
            "AWS_DEFAULT_EXTRACT_REGION": "eu-west-1",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
        }

        for k, v in std_envs.items():
            if k not in env_vars:
                env_vars[k] = v

        super().__init__(
            # Airflow Configuration
            task_id=task_id,
            # Cluster configuration
            config_file="/usr/local/airflow/dags/.kube/config",
            namespace="airflow",
            in_cluster=False,
            get_logs=True,
            startup_timeout_seconds=600,
            is_delete_operator_pod=True,
            # Pod Configuration
            name=name,
            image=image,
            image_pull_policy="Always",
            labels={
                "airflow.compute.analytical-platform.service.justice.gov.uk/environment": environment,
                "airflow.compute.analytical-platform.service.justice.gov.uk/project": project,
                "airflow.compute.analytical-platform.service.justice.gov.uk/workflow": workflow,
            },
            env_vars=env_vars,
            affinity=compute_profile["affinity"],
            annotations=compute_profile["annotations"],
            container_resources=compute_profile["container_resources"],
            security_context=compute_profile["security_context"],
            tolerations=compute_profile["tolerations"],
            *args,
            **kwargs
        )
