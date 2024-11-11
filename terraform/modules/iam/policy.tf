data "aws_iam_policy_document" "policy" {
  count = length(local.iam_configuration) > 0 ? 1 : 0

  /* Bedrock */
  dynamic "statement" {
    for_each = local.bedrock_enabled ? [1] : []
    content {
      sid    = "Bedrock"
      effect = "Allow"
      actions = [
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel",
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:CreateModelCustomizationJob",
        "bedrock:GetModelCustomizationJob",
        "bedrock:GetFoundationModelAvailability",
        "bedrock:ListModelCustomizationJobs",
        "bedrock:StopModelCustomizationJob",
        "bedrock:GetCustomModel",
        "bedrock:ListCustomModels",
        "bedrock:DeleteCustomModel",
        "bedrock:ListProvisionedModelThroughputs",
        "bedrock:ListTagsForResource",
        "bedrock:UntagResource",
        "bedrock:TagResource",
        "bedrock:CreateAgent",
        "bedrock:UpdateAgent",
        "bedrock:GetAgent",
        "bedrock:ListAgents",
        "bedrock:CreateActionGroup",
        "bedrock:UpdateActionGroup",
        "bedrock:GetActionGroup",
        "bedrock:ListActionGroups",
        "bedrock:CreateAgentDraftSnapshot",
        "bedrock:GetAgentVersion",
        "bedrock:ListAgentVersions",
        "bedrock:CreateAgentAlias",
        "bedrock:UpdateAgentAlias",
        "bedrock:GetAgentAlias",
        "bedrock:ListAgentAliases",
        "bedrock:InvokeAgent",
        "bedrock:PutFoundationModelEntitlement",
        "bedrock:GetModelInvocationLoggingConfiguration",
        "bedrock:PutModelInvocationLoggingConfiguration",
        "bedrock:CreateFoundationModelAgreement",
        "bedrock:DeleteFoundationModelAgreement",
        "bedrock:ListFoundationModelAgreementOffers",
        "bedrock:GetUseCaseForModelAccess"
      ]
      resources = ["*"]
      condition {
        test     = "StringEquals"
        variable = "aws:RequestedRegion"
        values = [
          "eu-central-1", // Frankfurt
          "eu-west-1",    // Ireland
          "eu-west-2",    // London
          "eu-west-3"     // Paris
        ]
      }
    }
  }
  /* KMS */
  dynamic "statement" {
    for_each = length(local.kms_keys) > 0 ? [1] : []
    content {
      sid    = "KMS"
      effect = "Allow"
      actions = [
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:Encrypt",
        "kms:DescribeKey",
        "kms:Decrypt"
      ]
      resources = [
        for item in local.kms_keys : "${item}"
      ]
    }
  }
  /* S3 Deny */
  dynamic "statement" {
    for_each = length(local.s3_deny) > 0 ? [1] : []
    content {
      sid    = "S3Deny"
      effect = "Deny"
      actions = [
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:RestoreObject"
      ]
      resources = [
        for item in local.s3_deny : "arn:aws:s3:::${item}"
      ]
    }
  }
  /* S3 Read Only */
  dynamic "statement" {
    for_each = length(local.s3_read_only) > 0 ? [1] : []
    content {
      sid    = "S3ReadOnly"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectVersion"
      ]
      resources = [
        for item in local.s3_read_only : "arn:aws:s3:::${item}"
      ]
    }
  }
  /* S3 Read Write */
  dynamic "statement" {
    for_each = length(local.s3_read_write) > 0 ? [1] : []
    content {
      sid    = "S3ReadWrite"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectVersion",
        "s3:GetObjectTagging",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:PutObjectTagging",
        "s3:RestoreObject"
      ]
      resources = [
        for item in local.s3_read_write : "arn:aws:s3:::${item}"
      ]
    }
  }
  # /* S3 Write Only */
  dynamic "statement" {
    for_each = length(local.s3_write_only) > 0 ? [1] : []
    content {
      sid    = "S3WriteOnly"
      effect = "Allow"
      actions = [
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:RestoreObject"
      ]
      resources = [
        for item in local.s3_write_only : "arn:aws:s3:::${item}"
      ]
    }
  }
}

module "policy" {
  count = length(local.iam_configuration) > 0 ? 1 : 0

  source  = "terraform-aws-modules/iam/aws//modules/iam-policy"
  version = "5.48.0"

  name   = var.name
  path   = "/airflow/${var.environment}/${var.project}/"
  policy = data.aws_iam_policy_document.policy[0].json
}
