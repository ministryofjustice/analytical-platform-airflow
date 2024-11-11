module "iam" {
  for_each = {
    for f in fileset(path.module, "../configuration/environments/**/configuration.yaml") :
    join("/", slice(split("/", dirname(f)), 3, 6)) => f
  }

  source = "./modules/iam"

  name          = format("%s", split("/", each.key)[2])
  project       = format("%s", split("/", each.key)[1])
  environment   = format("%s", split("/", each.key)[0])
  configuration = yamldecode(file("../configuration/environments/${each.key}/configuration.yaml"))
}
