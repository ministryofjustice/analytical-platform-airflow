module "airflow" {
  for_each = {
    for f in fileset(path.module, "../environments/${terraform.workspace}/**/workflow.yml") :
    join("/", slice(split("/", dirname(f)), 3, 5)) => f
  }

  source = "./modules/airflow"

  providers = {
    aws.analytical-platform-data-production-eu-west-1 = aws.analytical-platform-data-production-eu-west-1
    aws.analytical-platform-data-production-eu-west-2 = aws.analytical-platform-data-production-eu-west-2
  }

  project       = replace(format("%s", split("/", each.key)[0]), "electronic-monitoring-data-store", "emds")
  workflow      = format("%s", split("/", each.key)[1])
  environment   = terraform.workspace
  configuration = yamldecode(file("../environments/${terraform.workspace}/${each.key}/workflow.yml"))
  eks_oidc_url  = local.eks_oidc_url
  label_domain  = local.label_domain
}
