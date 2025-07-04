module "secrets_manager" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  for_each = toset(local.secrets_configuration)

  source  = "terraform-aws-modules/secrets-manager/aws"
  version = "1.3.1"

  providers = {
    aws = aws.analytical-platform-data-production-eu-west-2
  }

  name       = "/airflow/${var.environment}/${var.project}/${var.workflow}/${each.key}"
  kms_key_id = data.aws_kms_key.secrets_manager_eu_west_2.arn

  replica = {
    eu-west-1 = {
      region     = "eu-west-1"
      kms_key_id = data.aws_kms_key.secrets_manager_eu_west_1.arn
    }
  }


  create_policy = true
  policy_statements = {
    user_access = {
      sid = "UserAccess"
      actions = [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
      ]
      resources = ["*"]
      principals = [{
        type        = "AWS"
        identifiers = ["*"]
      }]
      conditions = [{
        test     = "StringEquals"
        variable = "aws:userName"
        values   = [for maintainer in var.configuration.maintainers : lower(maintainer)]
      }]
    }
  }

  secret_string         = "CHANGEME"
  ignore_secret_changes = true
}

resource "helm_release" "external_secret" {
  for_each = toset(local.secrets_configuration)

  name      = "${var.project}-${var.workflow}-${each.key}"
  chart     = "${path.module}/src/helm/charts/external-secret"
  namespace = "mwaa"

  set {
    name  = "secretName"
    value = "${var.project}-${var.workflow}-${each.key}"
  }

  set {
    name  = "targetName"
    value = "${var.project}-${var.workflow}-${each.key}"
  }

  set {
    name  = "remoteRefKey"
    value = module.secrets_manager[each.key].secret_id
  }
}
