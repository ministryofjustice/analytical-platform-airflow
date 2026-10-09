resource "kubernetes_service_account_v1" "this" {
  metadata {
    namespace = "mwaa"
    name      = "${var.project}-${var.workflow}"
    labels = {
      "airflow.${var.label_domain}/environment" = var.environment
      "airflow.${var.label_domain}/project"     = var.project
      "airflow.${var.label_domain}/workflow"    = var.workflow
    }
    annotations = {
      "eks.amazonaws.com/role-arn" = try(module.iam_role[0].iam_role_arn, local.iam_external_role)
    }
  }
}