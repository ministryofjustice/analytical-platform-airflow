module "airflow" {
  for_each = {
    for f in fileset(path.module, "../environments/${terraform.workspace}/**/workflow.yml") :
    join("/", slice(split("/", dirname(f)), 3, 6)) => f
  }

  source = "./modules/airflow"

  project       = format("%s", split("/", each.key)[1])
  workflow      = format("%s", split("/", each.key)[2])
  environment   = format("%s", split("/", each.key)[0])
  configuration = yamldecode(file("../environments/${each.key}/workflow.yml"))
}
