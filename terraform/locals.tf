locals {
  # Workspaces are named after folders in environments/. Anything starting with
  # data-platform- runs on the Data Platform cluster; everything else runs on
  # Analytical Platform Compute. Both are reached the same way: endpoint,
  # certificate and OIDC URL come from the cluster-data secret, and
  # scripts/eks-authentication.sh authenticates as the current role.
  is_data_platform = startswith(terraform.workspace, "data-platform-")

  eks_cluster_name = local.is_data_platform ? "${terraform.workspace}-airflow" : "analytical-platform-compute-${terraform.workspace}"

  cluster_data = jsondecode(data.aws_secretsmanager_secret_version.analytical_platform_compute_cluster_data.secret_string)

  eks_cluster_endpoint       = local.cluster_data["${local.eks_cluster_name}-api-endpoint"]
  eks_cluster_ca_certificate = base64decode(local.cluster_data["${local.eks_cluster_name}-certificate"])
  eks_oidc_url               = local.cluster_data["${local.eks_cluster_name}-oidc-endpoint"]

  # Domain used for Kubernetes labels (matches airflow/<package>/standard_operator.py)
  label_domain = local.is_data_platform ? "compute.data-platform.service.justice.gov.uk" : "compute.analytical-platform.service.justice.gov.uk"
}