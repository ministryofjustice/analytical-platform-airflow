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

  /* Athena - Read Only */
  dynamic "statement" {
    for_each = local.iam_athena == "read" ? [1] : []
    content {
      sid    = "AthenaReadOnlyS3BucketActions"
      effect = "Allow"
      actions = [
        "s3:GetBucketLocation",
        "s3:ListAllMyBuckets"
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = local.iam_athena == "read" ? [1] : []
    content {
      sid     = "AthenaReadOnlyS3ListBuckets"
      effect  = "Allow"
      actions = ["s3:ListBucket"]
      resources = [
        "arn:aws:s3:::moj-analytics-lookup-tables",
        "arn:aws:s3:::mojap-athena-query-dump"
      ]
    }
  }

  dynamic "statement" {
    for_each = local.iam_athena == "read" ? [1] : []
    content {
      sid       = "AthenaReadOnlyS3GetObjects"
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = ["arn:aws:s3:::moj-analytics-lookup-tables/*"]
    }
  }

  dynamic "statement" {
    for_each = local.iam_athena == "read" ? [1] : []
    content {
      sid    = "AthenaReadOnlyS3GetPutObjects"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:PutObject"
      ]
      resources = ["arn:aws:s3:::aws-athena-query-results-*"]
    }
  }

  dynamic "statement" {
    for_each = local.iam_athena == "read" ? [1] : []
    content {
      sid    = "AthenaReadOnlyS3DeleteGetPutObjects"
      effect = "Allow"
      actions = [
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:PutObject"
      ]
      resources = ["arn:aws:s3:::mojap-athena-query-dump/$${aws:userid}/*"]
    }
  }

  dynamic "statement" {
    for_each = local.iam_athena == "read" ? [1] : []
    content {
      sid    = "AthenaReadOnlyAthenaGlueRead"
      effect = "Allow"
      actions = [
        "athena:BatchGetNamedQuery",
        "athena:BatchGetQueryExecution",
        "athena:CancelQueryExecution",
        "athena:GetCatalogs",
        "athena:GetExecutionEngine",
        "athena:GetExecutionEngines",
        "athena:GetNamedQuery",
        "athena:GetNamespace",
        "athena:GetNamespaces",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:GetQueryResultsStream",
        "athena:GetTable",
        "athena:GetTableMetadata",
        "athena:GetTables",
        "athena:GetWorkGroup",
        "athena:ListNamedQueries",
        "athena:ListQueryExecutions",
        "athena:ListWorkGroups",
        "athena:RunQuery",
        "athena:StartQueryExecution",
        "athena:StopQueryExecution",
        "glue:BatchGetPartition",
        "glue:GetCatalogImportStatus",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:GetTable",
        "glue:GetTableVersions",
        "glue:GetTables",
        "glue:GetUserDefinedFunction",
        "glue:GetUserDefinedFunctions"
      ]
      resources = ["*"]
    }
  }

  /* Bedrock */
  dynamic "statement" {
    for_each = local.iam_bedrock_enabled ? [1] : []
    content {
      sid    = "Bedrock"
      effect = "Allow"
      actions = [
        "bedrock:CreateActionGroup",
        "bedrock:CreateAgent",
        "bedrock:CreateAgentAlias",
        "bedrock:CreateAgentDraftSnapshot",
        "bedrock:CreateFoundationModelAgreement",
        "bedrock:CreateModelCustomizationJob",
        "bedrock:DeleteCustomModel",
        "bedrock:DeleteFoundationModelAgreement",
        "bedrock:GetActionGroup",
        "bedrock:GetAgent",
        "bedrock:GetAgentAlias",
        "bedrock:GetAgentVersion",
        "bedrock:GetCustomModel",
        "bedrock:GetFoundationModel",
        "bedrock:GetFoundationModelAvailability",
        "bedrock:GetModelCustomizationJob",
        "bedrock:GetModelInvocationLoggingConfiguration",
        "bedrock:GetUseCaseForModelAccess",
        "bedrock:InvokeAgent",
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListActionGroups",
        "bedrock:ListAgentAliases",
        "bedrock:ListAgents",
        "bedrock:ListAgentVersions",
        "bedrock:ListCustomModels",
        "bedrock:ListFoundationModelAgreementOffers",
        "bedrock:ListFoundationModels",
        "bedrock:ListModelCustomizationJobs",
        "bedrock:ListProvisionedModelThroughputs",
        "bedrock:ListTagsForResource",
        "bedrock:PutFoundationModelEntitlement",
        "bedrock:PutModelInvocationLoggingConfiguration",
        "bedrock:StopModelCustomizationJob",
        "bedrock:TagResource",
        "bedrock:UntagResource",
        "bedrock:UpdateActionGroup",
        "bedrock:UpdateAgent",
        "bedrock:UpdateAgentAlias"
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
    for_each = length(local.iam_kms_keys) > 0 ? [1] : []
    content {
      sid    = "KMS"
      effect = "Allow"
      actions = [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:Encrypt",
        "kms:GenerateDataKey*",
        "kms:ReEncrypt*",
      ]
      resources = [
        for item in local.iam_kms_keys : item
      ]
    }
  }

  /* S3 - Read Only */
  dynamic "statement" {
    for_each = length(local.iam_s3_read_only) > 0 ? [1] : []
    content {
      sid    = "S3ReadOnly"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectVersion"
      ]
      resources = [
        for item in local.iam_s3_read_only : "arn:aws:s3:::${item}"
      ]
    }
  }

  /* S3 Read Write */
  dynamic "statement" {
    for_each = length(local.iam_s3_read_write) > 0 ? [1] : []
    content {
      sid    = "S3ReadWrite"
      effect = "Allow"
      actions = [
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectTagging",
        "s3:GetObjectVersion",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:PutObjectTagging",
        "s3:RestoreObject"
      ]
      resources = [
        for item in local.iam_s3_read_write : "arn:aws:s3:::${item}"
      ]
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
