data "aws_iam_policy_document" "iam_policy" {
  count = length(local.iam_external_role) == 0 ? 1 : 0

  /* Glue */
  dynamic "statement" {
    for_each = local.iam_glue ? [1] : []
    content {
      sid       = "GluePassRole"
      effect    = "Allow"
      actions   = ["iam:PassRole"]
      resources = ["arn:aws:iam::${data.aws_caller_identity.analytical_platform_data_production.account_id}:role/airflow-${var.environment}-${var.project}-${var.workflow}"]
      condition {
        test     = "StringEquals"
        variable = "iam:PassedToService"
        values   = ["glue.amazonaws.com"]
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

  /* S3 - Deny */
  dynamic "statement" {
    for_each = length(local.iam_s3_deny) > 0 ? [1] : []
    content {
      sid    = "S3Deny"
      effect = "Deny"
      actions = [
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectVersion",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:RestoreObject"
      ]
      resources = [
        for item in local.iam_s3_deny : "arn:aws:s3:::${item}"
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
        "s3:CreateMultipartUpload",
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

  /* S3 - Write Only */
  dynamic "statement" {
    for_each = length(local.iam_s3_write_only) > 0 ? [1] : []
    content {
      sid    = "S3WriteOnly"
      effect = "Allow"
      actions = [
        "s3:CreateMultipartUpload",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:RestoreObject"
      ]
      resources = [
        for item in local.iam_s3_write_only : "arn:aws:s3:::${item}"
      ]
    }
  }

  /* Secrets Manager */
  statement {
    sid     = "SecretsManager"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:eu-west-2:${data.aws_caller_identity.analytical_platform_data_production.account_id}:secret:/airflow/${var.environment}/${var.project}/${var.workflow}/*",
      "arn:aws:secretsmanager:eu-west-1:${data.aws_caller_identity.analytical_platform_data_production.account_id}:secret:/airflow/${var.environment}/${var.project}/${var.workflow}/*"
    ]
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
