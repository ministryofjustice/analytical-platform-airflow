locals {
  iam_configuration   = try(var.configuration.iam, {})
  iam_external_role   = try(local.iam_configuration.external_role, "")
  iam_athena          = try(local.iam_configuration.athena, "")
  iam_bedrock_enabled = try(local.iam_configuration.bedrock, false)
  iam_glue            = try(local.iam_configuration.glue, false)
  iam_kms_keys        = try(local.iam_configuration.kms, [])
  iam_s3_deny         = try(local.iam_configuration.s3_deny, [])
  iam_s3_read_only    = try(local.iam_configuration.s3_read_only, [])
  iam_s3_read_write   = try(local.iam_configuration.s3_read_write, [])
  iam_s3_write_only   = try(local.iam_configuration.s3_write_only, [])

  secrets_configuration = try(var.configuration.secrets, [])
}
