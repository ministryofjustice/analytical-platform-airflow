terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
      configuration_aliases = [
        aws.analytical-platform-data-production-eu-west-1,
        aws.analytical-platform-data-production-eu-west-2
      ]
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  required_version = "~> 1.10"
}
