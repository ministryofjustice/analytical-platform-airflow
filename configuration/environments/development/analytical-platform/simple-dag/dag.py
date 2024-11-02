from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

default_args = {
    'owner': 'analytical-platform@justice.gov.uk',
}

task = KubernetesPodOperator(
    affinity={'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{'matchExpressions': [{'key': 'compute.analytical-platform.service.justice.gov.uk/karpenter-node-pool', 'operator': 'In', 'values': ['general-on-demand']}]}]}}},
    container_resources={'claims': None,
 'limits': {'cpu': '2', 'memory': '8Gi'},
 'requests': {'cpu': '2', 'memory': '8Gi'}},
    tolerations=[{'key': 'compute.analytical-platform.service.justice.gov.uk/karpenter-node-pool', 'operator': 'Equal', 'value': 'general-on-demand', 'effect': 'NoSchedule'}],
    security_context={'runAsNonRoot': True, 'runAsUser': 1000, 'allowPrivilegeEscalation': False, 'privileged': False}
)
