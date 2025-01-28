terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [
        analytical-platform-data-production-eu-west-1,
        analytical-platform-data-production-eu-west-2
      ]
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  required_version = "~> 1.10"
}
