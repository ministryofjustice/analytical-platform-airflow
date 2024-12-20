locals {
  iam_configuration = try(var.configuration.iam, {})

  create          = try(local.iam_configuration.create, true)
  bedrock_enabled = try(local.iam_configuration.bedrock, false)
  kms_keys        = try(local.iam_configuration.kms, [])
  s3_deny         = try(local.iam_configuration.s3.deny, [])
  s3_read_only    = try(local.iam_configuration.s3.read_only, [])
  s3_read_write   = try(local.iam_configuration.s3.read_write, [])
  s3_write_only   = try(local.iam_configuration.s3.write_only, [])
  external_role   = try(local.iam_configuration.external_role, null)
}
