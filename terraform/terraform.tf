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
      version = "5.84.0"
    }
  }
  required_version = "~> 1.10"
}
