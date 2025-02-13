module "iam_role" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  count = length(local.iam_external_role) == 0 ? 1 : 0

  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.52.2"

  providers = {
    aws = aws.analytical-platform-data-production-eu-west-2
  }

  role_name = "airflow-${var.environment}-${var.project}-${var.workflow}"

  oidc_providers = {
    main = {
      provider_arn               = format("arn:aws:iam::593291632749:oidc-provider/%s", trimprefix(var.eks_oidc_url, "https://"))
      namespace_service_accounts = ["mwaa:${var.project}-${var.workflow}"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "generated" {
  count = length(local.iam_external_role) == 0 ? 1 : 0

  provider = aws.analytical-platform-data-production-eu-west-2

  role       = module.iam_role[0].iam_role_name
  policy_arn = module.iam_policy[0].arn
}

resource "aws_iam_role_policy_attachment" "athena_read" {
  count = length(local.iam_external_role) == 0 && local.iam_athena == "read" ? 1 : 0

  provider = aws.analytical-platform-data-production-eu-west-2

  role       = module.iam_role[0].iam_role_name
  policy_arn = "arn:aws:iam::593291632749:policy/airflow-service/athena-read"
}
