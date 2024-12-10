def get_compute_profile(compute_profile="general-on-demand-2vcpu-8gb"):
    if compute_profile.startswith("general-on-demand"):
        karpenter_node_pool = "general-on-demand"
        gpu_enabled = False
    elif compute_profile.startswith("general-spot"):
        karpenter_node_pool = "general-spot"
        gpu_enabled = False
    elif compute_profile.startswith("gpu-on-demand"):
        karpenter_node_pool = "gpu-on-demand"
        gpu_enabled = True
    elif compute_profile.startswith("gpu-spot"):
        karpenter_node_pool = "gpu-spot"
        gpu_enabled = True
    else:
        raise ValueError(f"Unknown compute_profile: {compute_profile}")

    flavours = {
        "-1vcpu-4gb": {
            "requests_cpu": "1",
            "requests_memory": "4Gi",
            "limits_cpu": "1",
            "limits_memory": "4Gi"
        },
        "-2vcpu-8gb": {
            "requests_cpu": "2",
            "requests_memory": "8Gi",
            "limits_cpu": "2",
            "limits_memory": "8Gi"
        },
        "-4vcpu-16gb": {
            "requests_cpu": "4",
            "requests_memory": "16Gi",
            "limits_cpu": "4",
            "limits_memory": "16Gi"
        },
        "-8vcpu-32gb": {
            "requests_cpu": "8",
            "requests_memory": "32Gi",
            "limits_cpu": "8",
            "limits_memory": "32Gi"
        },
        "-16vcpu-64gb": {
            "requests_cpu": "16",
            "requests_memory": "64Gi",
            "limits_cpu": "16",
            "limits_memory": "64Gi"
        },
        "-32vcpu-128gb": {
            "requests_cpu": "32",
            "requests_memory": "128Gi",
            "limits_cpu": "32",
            "limits_memory": "128Gi"
        },
        "-64vcpu-256gb": {
            "requests_cpu": "64",
            "requests_memory": "256Gi",
            "limits_cpu": "64",
            "limits_memory": "256Gi"
        }
    }

    for flavour in flavours.keys():
        if compute_profile.endswith(flavour):
            profile = flavours[flavour]
            requests_cpu = profile["requests_cpu"]
            requests_memory = profile["requests_memory"]
            limits_cpu = profile["limits_cpu"]
            limits_memory = profile["limits_memory"]
            break
    else:
        raise ValueError(f"Unknown compute_profile: {compute_profile}")

    if gpu_enabled:
        container_resources = {
            "requests": {
                "cpu": requests_cpu,
                "memory": requests_memory
            },
            "limits": {
                "cpu": limits_cpu,
                "memory": limits_memory,
                "nvidia.com/gpu": "1"
            }
        }
    else:
        container_resources = {
            "requests": {
                "cpu": requests_cpu,
                "memory": requests_memory
            },
            "limits": {
                "cpu": limits_cpu,
                "memory": limits_memory
            }
        }

    return {
       "karpenter_node_pool": karpenter_node_pool,
       "container_resources": container_resources
    }
