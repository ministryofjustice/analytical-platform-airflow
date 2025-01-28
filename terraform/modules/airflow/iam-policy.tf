data "aws_iam_policy_document" "iam_policy" {
  count = length(local.iam_external_role) > 0 ? 0 : 1

  /* Default - KMS */
  statement {
    sid     = "DefaultKMS"
    effect  = "Allow"
    actions = ["kms:Decrypt"]
    resources = [
      data.aws_kms_key.secrets_manager_eu_west_2.arn,
      data.aws_kms_key.secrets_manager_eu_west_1.arn
    ]
  }

  /* Default - Secrets Manager */
  statement {
    sid     = "DefaultSecretsManager"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:eu-west-2:593291632749:secret:/airflow/${var.environment}/${var.project}/${var.workflow}/*",
      "arn:aws:secretsmanager:eu-west-1:593291632749:secret:/airflow/${var.environment}/${var.project}/${var.workflow}/*"
    ]
  }

  /* Bedrock */
  dynamic "statement" {
    for_each = local.iam_bedrock_enabled ? [1] : []
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
}

module "iam_policy" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  count = length(local.iam_external_role) > 0 ? 0 : 1

  source  = "terraform-aws-modules/iam/aws//modules/iam-policy"
  version = "5.52.2"

  providers = {
    aws = aws.analytical-platform-data-production-eu-west-2
  }

  name   = "airflow-${var.environment}-${var.project}-${var.workflow}"
  policy = data.aws_iam_policy_document.iam_policy[0].json
}
