locals {
  iam_configuration   = try(var.configuration.iam, {})
  iam_external_role   = try(local.iam_configuration.external_role, null)
  iam_bedrock_enabled = try(local.iam_configuration.bedrock, false)

  secrets_configuration = try(var.configuration.secrets, [])
}
