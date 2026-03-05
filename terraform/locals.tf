locals {
  cluster_environment = terraform.workspace == "internal-development" ? "development" : terraform.workspace
}
