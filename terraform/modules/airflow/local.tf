locals {
  iam_configuration = try(var.configuration.iam, {})

  create          = try(local.iam_configuration.create, true)
  bedrock_enabled = try(local.iam_configuration.bedrock, false)
  external_role   = try(local.iam_configuration.external_role, null)
}
