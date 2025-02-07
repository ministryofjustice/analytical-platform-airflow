locals {
  iam_configuration   = try(var.configuration.iam, {})
  iam_external_role   = try(local.iam_configuration.external_role, "")
  iam_bedrock_enabled = try(local.iam_configuration.bedrock, false)
  iam_kms_keys        = try(local.iam_configuration.kms, [])
  iam_s3_read_only    = try(local.iam_configuration.s3_read_only, [])
  iam_s3_read_write   = try(local.iam_configuration.s3_read_write, [])

  secrets_configuration = try(var.configuration.secrets, [])
}
