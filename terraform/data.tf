data "aws_secretsmanager_secret_version" "cluster_data" {
  provider = aws.analytical-platform-common-production

  secret_id = local.cluster_data_secret_id
}
