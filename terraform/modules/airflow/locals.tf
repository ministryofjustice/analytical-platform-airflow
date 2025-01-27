locals {
  oidc_provider = local.oidc_providers[var.environment]
  oidc_providers = {
    development = "oidc.eks.eu-west-2.amazonaws.com/id/1972AFFBD0701A0D1FD291E34F7D1287"
    test        = "oidc.eks.eu-west-2.amazonaws.com/id/9FAFCA50C4DA68A8E75FD21EA53A4F2B"
    production  = "oidc.eks.eu-west-2.amazonaws.com/id/801920EDEF91E3CAB03E04C03A2DE2BB"
  }
}
