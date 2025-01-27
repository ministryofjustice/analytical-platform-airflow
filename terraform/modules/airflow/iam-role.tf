module "iam_role" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.52.2"

  role_name = "airflow-${var.environment}-${var.project}-${var.workflow}"
  role_policy_arns = {
    policy = module.iam_policy.arn
  }

  oidc_providers = {
    main = {
      provider_arn               = format("arn:aws:iam::593291632749:oidc-provider/%s", local.oidc_provider)
      namespace_service_accounts = ["mwaa:${var.project}-${var.workflow}"]
    }
  }
}
