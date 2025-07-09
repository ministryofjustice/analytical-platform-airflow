from typing import Optional

from airflow.providers.cncf.kubernetes.operators.pod import (
    KubernetesPodOperator,
)
from airflow.providers.cncf.kubernetes.utils.xcom_sidecar import (
    PodDefaults,
)
from analytical_platform.compute_profiles import get_compute_profile
from kubernetes.client import models as k8s_models

def override_xcom_sidecar_defaults():
    """Override the default sidecar container for XCom in KubernetesPodOperator"""
    PodDefaults.SIDECAR_CONTAINER.image = "ghcr.io/ministryofjustice/analytical-platform-airflow-xcom-sidecar:1.0.0-rc2@sha256:1e0adde6f97c66b64bbb213f43d83e0c54e45dcf5422c23628e3a157dc7172ad"
    PodDefaults.SIDECAR_CONTAINER.security_context = k8s_models.V1SecurityContext(
        allow_privilege_escalation=False,
        privileged=False,
        run_as_non_root=True,
        seccomp_profile=k8s_models.V1SeccompProfile(type="RuntimeDefault"),
        capabilities=k8s_models.V1Capabilities(drop=["ALL"]),
    )

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
        hmcts_sdp_networking: Optional[bool] = False,
        env_vars: Optional[dict] = None,
        *args,
        **kwargs,
    ):
        # Override the default sidecar container for XCom
        override_xcom_sidecar_defaults()

        # Declare any settings that can be updated later
        annotations = {}

        # Compute Profile
        compute_profile = get_compute_profile(compute_profile=compute_profile)
        annotations.update(compute_profile["annotations"])

        # HMCTS SDP Networking
        if not hmcts_sdp_networking:
            hmcts_sdp_networking_host_aliases = None
        else:
            # Annotations
            hmcts_sdp_networking_annotations = {
                # Ingress and Egress is capped at 175M so workloads
                # don't saturate the network link between MoJ and HMCTS
                "kubernetes.io/ingress-bandwidth": "175M",
                "kubernetes.io/egress-bandwidth": "175M"
            }

            annotations.update(hmcts_sdp_networking_annotations)

            # Host Aliases
            hmcts_sdp_networking_host_aliases = [
                {
                    "ip": "10.168.4.13",
                    "hostnames": ["mipersistentithc.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.4.5",
                    "hostnames": ["miexportithc.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.3.8",
                    "hostnames": ["mipersistentstg.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.3.7",
                    "hostnames": ["miexportstg.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.5.13",
                    "hostnames": ["mipersistentprod.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.5.8",
                    "hostnames": ["miexportprod.blob.core.windows.net"]
                },
                {
                    "ip": "10.225.251.100",
                    "hostnames": ["baisbaumojapnle.blob.core.windows.net"]
                },
                {
                    "ip": "10.224.251.100",
                    "hostnames": ["baisbaumojapprod.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.5.4",
                    "hostnames": ["miadhoclandingprod.blob.core.windows.net"]
                },
                {
                    "ip": "10.168.1.14",
                    "hostnames": ["mi-synapse-dev.sql.azuresynapse.net"]
                },
                {
                    "ip": "10.168.1.15",
                    "hostnames": ["mi-synapse-dev.dev.azuresynapse.net"]
                },
                {
                    "ip": "10.168.1.16",
                    "hostnames": ["mi-synapse-dev-ondemand.sql.azuresynapse.net"]
                },
                {
                    "ip": "10.168.5.16",
                    "hostnames": ["mi-synapse-prod.sql.azuresynapse.net"]
                },
                {
                    "ip": "10.168.5.17",
                    "hostnames": ["mi-synapse-prod-ondemand.sql.azuresynapse.net"]
                },
                {
                    "ip": "10.168.5.18",
                    "hostnames": ["mi-synapse-prod.dev.azuresynapse.net"]
                }
            ]

        # Environment Variables
        if env_vars is None:
            env_vars = {}

        std_envs = {
            "AWS_DEFAULT_REGION": "eu-west-1",
            "AWS_ATHENA_QUERY_EXTRACT_REGION": "eu-west-1",
            "AWS_DEFAULT_EXTRACT_REGION": "eu-west-1",
            "AWS_METADATA_SERVICE_TIMEOUT": "60",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS": "5",
            "AIRFLOW_ENVIRONMENT": environment.upper(),
            "AIRFLOW_RUN_ID": "{{ run_id }}",
            "AIRFLOW_TIMESTAMP": "{{ ts }}",
            "AIRFLOW_TIMESTAMP_NO_DASH": "{{ ts_nodash }}",
            "AIRFLOW_TIMESTAMP_NO_DASH_WITH_TZ": "{{ ts_nodash_with_tz }}",
        }

        # merge dicts into env_vars
        env_vars = std_envs | env_vars

        # Convert all values to strings
        env_vars = {k: str(v) for k, v in env_vars.items()}


        super().__init__(
            # Airflow Configuration
            task_id=task_id,
            # Cluster configuration
            config_file="/usr/local/airflow/dags/.kube/config",
            namespace="mwaa",
            in_cluster=False,
            get_logs=True,
            startup_timeout_seconds=600,
            is_delete_operator_pod=True,
            log_pod_spec_on_failure=True,
            # Pod Configuration
            name=name,
            service_account_name=f"{project}-{workflow}",
            image=image,
            image_pull_policy="Always",
            annotations=annotations,
            labels={
                "airflow.compute.analytical-platform.service.justice.gov.uk/environment": environment,
                "airflow.compute.analytical-platform.service.justice.gov.uk/project": project,
                "airflow.compute.analytical-platform.service.justice.gov.uk/workflow": workflow,
            },
            env_vars=env_vars,
            host_aliases=hmcts_sdp_networking_host_aliases,
            affinity=compute_profile["affinity"],
            container_resources=compute_profile["container_resources"],
            container_security_context=compute_profile["container_security_context"],
            security_context=compute_profile["security_context"],
            tolerations=compute_profile["tolerations"],
            *args,
            **kwargs,
        )
