from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from analytical_platform.compute_profiles import get_compute_profile

class AnalyticalPlatformStandardOperator(KubernetesPodOperator):
    def __init__(self,
                 task_id: str,
                 compute_profile: str,
                 name: str,
                 image: str,
                 environment: str,
                 project: str,
                 workflow: str,
                 *args, **kwargs):

        compute_profile = get_compute_profile(compute_profile=compute_profile)

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
            cmds=["sleep", "60"],
            labels={
                "airflow.compute.analytical-platform.service.justice.gov.uk/environment": environment,
                "airflow.compute.analytical-platform.service.justice.gov.uk/project": project,
                "airflow.compute.analytical-platform.service.justice.gov.uk/workflow": workflow,
            },
            affinity=compute_profile["affinity"],
            annotations=compute_profile["annotations"],
            container_resources=compute_profile["container_resources"],
            security_context=compute_profile["security_context"],
            tolerations=compute_profile["tolerations"],
            *args, **kwargs
        )
