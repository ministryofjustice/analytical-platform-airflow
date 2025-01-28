resource "kubernetes_service_account" "this" {
  metadata {
    namespace = "mwaa"
    name      = "${var.project}-${var.workflow}"
    labels = {
      "airflow.compute.analytical-platform.service.justice.gov.uk/environment" = var.environment
      "airflow.compute.analytical-platform.service.justice.gov.uk/project"     = var.project
    }
    annotations = {
      "eks.amazonaws.com/role-arn" = module.iam_role.iam_role_arn
    }
  }
}
