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

  project       = format("%s", split("/", each.key)[0])
  workflow      = format("%s", split("/", each.key)[1])
  environment   = terraform.workspace
  configuration = yamldecode(file("../environments/${terraform.workspace}/${each.key}/workflow.yml"))
  eks_oidc_url  = jsondecode(data.aws_secretsmanager_secret_version.analytical_platform_compute_cluster_data.secret_string)["analytical-platform-compute-${terraform.workspace}-oidc-endpoint"]
}
