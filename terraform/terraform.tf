terraform {
  backend "s3" {
    bucket               = "mojap-common-production-tfstate"
    region               = "eu-west-2"
    encrypt              = true
    kms_key_id           = "arn:aws:kms:eu-west-2:509399598587:key/ffd33710-74c9-46e0-9025-4de4571a1cae"
    use_lockfile         = true
    workspace_key_prefix = "analytical-platform-airflow"
    key                  = "terraform.tfstate"
    assume_role = {
      role_arn = "arn:aws:iam::509399598587:role/analytical-platform-terraform"
    }
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.64.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "3.0.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "3.2.1"
    }
  }
  required_version = "~> 1.10"
}

provider "aws" {
  alias  = "analytical-platform-common-production"
  region = "eu-west-2"
}

provider "aws" {
  alias  = "analytical-platform-data-production-eu-west-1"
  region = "eu-west-1"
  assume_role {
    role_arn = "arn:aws:iam::${var.account_ids["analytical-platform-data-production"]}:role/analytical-platform-infrastructure-access"
  }
  default_tags {
    tags = merge(
      var.tags,
      {
        environment   = terraform.workspace
        is-production = terraform.workspace == "production" ? "true" : "false"
      }
    )
  }
}

provider "aws" {
  alias  = "analytical-platform-data-production-eu-west-2"
  region = "eu-west-2"
  assume_role {
    role_arn = "arn:aws:iam::${var.account_ids["analytical-platform-data-production"]}:role/analytical-platform-infrastructure-access"
  }
  default_tags {
    tags = merge(
      var.tags,
      {
        environment   = terraform.workspace
        is-production = terraform.workspace == "production" ? "true" : "false"
      }
    )
  }
}

provider "kubernetes" {
  host                   = local.eks_cluster_endpoint
  cluster_ca_certificate = local.eks_cluster_ca_certificate
  exec {
    api_version = "client.authentication.k8s.io/v1"
    command     = "bash"
    args        = ["scripts/eks-authentication.sh", local.eks_cluster_name]
  }
}

provider "helm" {
  kubernetes = {
    host                   = local.eks_cluster_endpoint
    cluster_ca_certificate = local.eks_cluster_ca_certificate
    exec = {
      api_version = "client.authentication.k8s.io/v1"
      command     = "bash"
      args        = ["scripts/eks-authentication.sh", local.eks_cluster_name]
    }
  }
}