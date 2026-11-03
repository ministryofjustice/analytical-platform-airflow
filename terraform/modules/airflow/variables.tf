variable "project" {
  type = string
}

variable "workflow" {
  type = string
}

variable "environment" {
  type = string
}

variable "configuration" {
  type = any
}

variable "eks_oidc_url" {
  type = string
}

variable "label_domain" {
  type        = string
  description = "Domain used for Kubernetes labels on the service account"
  default     = "compute.analytical-platform.service.justice.gov.uk"
}

variable "iam_environment" {
  type        = string
  description = "Short environment name used in IAM role and policy names (64 character limit). Defaults to environment."
  default     = null
}
