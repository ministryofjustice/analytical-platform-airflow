module "secrets_manager" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  for_each = toset(local.secrets_configuration)

  source  = "terraform-aws-modules/secrets-manager/aws"
  version = "1.3.1"

  name = "/airflow/${var.environment}/${var.project}/${var.workflow}/${each.key}"

  secret_string         = "CHANGEME"
  ignore_secret_changes = true
}
