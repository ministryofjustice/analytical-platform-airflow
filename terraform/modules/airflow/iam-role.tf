module "iam_role" {
  #checkov:skip=CKV_TF_1:Module registry does not support commit hashes for versions
  #checkov:skip=CKV_TF_2:Module registry does not support tags for versions

  count = local.create && length(local.iam_configuration) > 0 ? 1 : 0

  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.52.2"

  role_name = "airflow-${var.environment}-${var.project}-${var.workflow}"
  role_policy_arns = {
    policy = module.iam_policy[0].arn
  }

  oidc_providers = {
    main = {
      provider_arn               = format("arn:aws:iam::593291632749:oidc-provider/%s", trimprefix(var.eks_oidc_url, "https://"))
      namespace_service_accounts = ["mwaa:${var.project}-${var.workflow}"]
    }
  }
}
