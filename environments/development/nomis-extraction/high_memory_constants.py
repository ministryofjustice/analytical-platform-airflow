# Config to use high memory nodes
tolerations = [
    {
        "key": "high-memory",
        "operator": "Equal",
        "value": "true",
        "effect": "NoSchedule",
    }
]
affinity = {
    "nodeAffinity": {
        "requiredDuringSchedulingIgnoredDuringExecution": {
            "nodeSelectorTerms": [
                {
                    "matchExpressions": [
                        {
                            "key": "high-memory",
                            "operator": "In",
                            "values": [
                                "true",
                            ]
                        }
                    ]
                }
            ]
        }
    }
}
