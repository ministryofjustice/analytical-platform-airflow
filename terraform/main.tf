module "airflow" {
  for_each = {
    for f in fileset(path.module, "../environments/**/configuration.yaml") :
    join("/", slice(split("/", dirname(f)), 2, 5)) => f
  }

  source = "./modules/airflow"

  name          = format("%s", split("/", each.key)[2])
  project       = format("%s", split("/", each.key)[1])
  environment   = format("%s", split("/", each.key)[0])
  configuration = yamldecode(file("../environments/${each.key}/configuration.yaml"))
}
