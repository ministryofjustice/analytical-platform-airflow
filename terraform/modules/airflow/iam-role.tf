# /* THIS IS FOR TESTING - IT NEEDS TO BE IRSA IN REALITY */
module "iam_role" {
  count = local.create && length(local.iam_configuration) > 0 ? 1 : 0

  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role"
  version = "5.48.0"

  create_role       = true
  role_name         = "airflow-${var.project}-${var.name}"
  role_requires_mfa = false

  trusted_role_services = ["ec2.amazonaws.com"]

  custom_role_policy_arns = [module.iam_policy[0].arn]
}