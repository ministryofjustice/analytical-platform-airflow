from kubernetes.client import models as k8s_models

# Data Platform Karpenter node pools (airflow-cluster/src/helm/charts/karpenter-configuration)
# are labelled AND tainted with:
#   compute.data-platform.service.justice.gov.uk/node-pool=<pool>-<arch>
# Available pools: general-on-demand-{amd64,arm64}, general-spot-{amd64,arm64}
NODE_POOL_KEY = "compute.data-platform.service.justice.gov.uk/node-pool"
SUPPORTED_ARCHES = ("amd64", "arm64")
DEFAULT_ARCH = "amd64"

FLAVOURS = {
    "-1vcpu-4gb": ("1", "4Gi"),
    "-2vcpu-8gb": ("2", "8Gi"),
    "-4vcpu-16gb": ("4", "16Gi"),
    "-8vcpu-32gb": ("8", "32Gi"),
    "-16vcpu-64gb": ("16", "64Gi"),
    "-32vcpu-128gb": ("32", "128Gi"),
    "-64vcpu-256gb": ("64", "256Gi"),
    "-120vcpu-500gb": ("120", "500Gi"),
    "-128vcpu-512gb": ("128", "512Gi"),
}


def get_compute_profile(compute_profile="general-spot-1vcpu-4gb", arch=DEFAULT_ARCH):
    if arch not in SUPPORTED_ARCHES:
        raise ValueError(f"Unsupported arch '{arch}', expected one of {SUPPORTED_ARCHES}")

    if compute_profile.startswith("general-on-demand"):
        karpenter_node_pool = "general-on-demand"
    elif compute_profile.startswith("general-spot"):
        karpenter_node_pool = "general-spot"
    elif compute_profile.startswith(("gpu-on-demand", "gpu-spot")):
        raise ValueError(
            f"GPU compute profiles are not available on Data Platform: {compute_profile}"
        )
    else:
        raise ValueError(f"Unknown compute_profile: {compute_profile}")

    for suffix, (cpu, memory) in FLAVOURS.items():
        if compute_profile.endswith(suffix):
            break
    else:
        raise ValueError(f"Unknown compute_profile: {compute_profile}")

    node_pool = f"{karpenter_node_pool}-{arch}"

    affinity = k8s_models.V1Affinity(
        node_affinity=k8s_models.V1NodeAffinity(
            required_during_scheduling_ignored_during_execution=k8s_models.V1NodeSelector(
                node_selector_terms=[
                    k8s_models.V1NodeSelectorTerm(
                        match_expressions=[
                            k8s_models.V1NodeSelectorRequirement(
                                key=NODE_POOL_KEY,
                                operator="In",
                                values=[node_pool],
                            )
                        ]
                    )
                ]
            )
        )
    )

    tolerations = [
        k8s_models.V1Toleration(
            key=NODE_POOL_KEY,
            operator="Equal",
            value=node_pool,
            effect="NoSchedule",
        )
    ]

    container_resources = k8s_models.V1ResourceRequirements(
        requests={"cpu": cpu, "memory": memory},
        limits={"cpu": cpu, "memory": memory},
    )

    # Stops Karpenter voluntarily disrupting the node while a task runs
    # (spot interruptions can still happen).
    annotations = {"karpenter.sh/do-not-disrupt": "true"}

    # Pod-level: must be V1PodSecurityContext (privileged / capabilities /
    # allowPrivilegeEscalation are container-only fields).
    security_context = k8s_models.V1PodSecurityContext(
        run_as_non_root=True,
        seccomp_profile=k8s_models.V1SeccompProfile(type="RuntimeDefault"),
    )

    container_security_context = k8s_models.V1SecurityContext(
        allow_privilege_escalation=False,
        privileged=False,
        run_as_non_root=True,
        seccomp_profile=k8s_models.V1SeccompProfile(type="RuntimeDefault"),
        capabilities=k8s_models.V1Capabilities(drop=["ALL"]),
    )

    return {
        "affinity": affinity,
        "annotations": annotations,
        "tolerations": tolerations,
        "container_resources": container_resources,
        "container_security_context": container_security_context,
        "security_context": security_context,
    }
