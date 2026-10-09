locals {
  is_data_platform = startswith(terraform.workspace, "data-platform-")


  cluster_data_key_prefix = local.is_data_platform ? terraform.workspace : "analytical-platform-compute-${terraform.workspace}"

  # EKS cluster name used to get a token
  eks_cluster_name = local.is_data_platform ? "${terraform.workspace}-airflow" : "analytical-platform-compute-${terraform.workspace}"

  cluster_data = jsondecode(data.aws_secretsmanager_secret_version.analytical_platform_compute_cluster_data.secret_string)

  eks_cluster_endpoint       = local.cluster_data["${local.cluster_data_key_prefix}-api-endpoint"]
  eks_cluster_ca_certificate = base64decode(local.cluster_data["${local.cluster_data_key_prefix}-certificate"])
  eks_oidc_url               = local.cluster_data["${local.cluster_data_key_prefix}-oidc-endpoint"]

  # Domain used for Kubernetes labels (matches airflow/<package>/standard_operator.py)
  label_domain = local.is_data_platform ? "compute.data-platform.service.justice.gov.uk" : "compute.analytical-platform.service.justice.gov.uk"
}