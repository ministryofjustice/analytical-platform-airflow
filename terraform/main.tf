module "airflow" {
  for_each = {
    for f in fileset(path.module, "../environments/${terraform.workspace}/**/workflow.yml") :
    join("/", slice(split("/", dirname(f)), 2, 4)) => f
  }

  source = "./modules/airflow"

  project       = format("%s", split("/", each.key)[0])
  workflow      = format("%s", split("/", each.key)[1])
  environment   = terraform.workspace
  configuration = yamldecode(file("../environments/${terraform.workspace}/${each.key}/workflow.yml"))
}
