data "aws_secretsmanager_secret_version" "analytical_platform_compute_cluster_data" {
  provider = aws.analytical-platform-common-production

  secret_id = "analytical-platform-compute/cluster-data"
}
