resource "aws_iam_openid_connect_provider" "data_platform" {
  count = local.is_data_platform ? 1 : 0

  provider = aws.analytical-platform-data-production-eu-west-2

  url            = local.eks_oidc_url
  client_id_list = ["sts.amazonaws.com"]
}