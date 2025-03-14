data "aws_caller_identity" "analytical_platform_data_production" {
  provider = aws.analytical-platform-data-production-eu-west-2
}

data "aws_kms_key" "secrets_manager_eu_west_2" {
  provider = aws.analytical-platform-data-production-eu-west-2

  key_id = "alias/secretsmanager/airflow"
}

data "aws_kms_key" "secrets_manager_eu_west_1" {
  provider = aws.analytical-platform-data-production-eu-west-1

  key_id = "alias/secretsmanager/airflow"
}
