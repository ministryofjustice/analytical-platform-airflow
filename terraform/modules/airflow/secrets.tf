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

resource "kubernetes_manifest" "external_secret" {
  for_each = toset(local.secrets_configuration)

  manifest = {
    "apiVersion" = "external-secrets.io/v1beta1"
    "kind"       = "ExternalSecret"
    "metadata" = {
      "namespace" = "mwaa"
      "name"      = "${var.project}-${var.workflow}-${each.key}"
    }
    "spec" = {
      "refreshInterval" = "5m"
      "secretStoreRef" = {
        "kind" = "SecretStore"
        "name" = "analytical-platform-data-production"
      }
      "target" = {
        "name"           = "${var.project}-${var.workflow}-${each.key}"
        "deletionPolicy" = "Delete"
      }
      "data" = [
        {
          "remoteRef" = {
            "key" = module.secrets_manager[each.key].secret_id
          }
          "secretKey" = "data"
        }
      ]
    }
  }
}
