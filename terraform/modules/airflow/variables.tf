variable "name" {
  type = string
}

variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "configuration" {
  type = any
}

variable "kubernetes_namespace" {
  type    = string
  default = "jacobwoffenden-test"
}
