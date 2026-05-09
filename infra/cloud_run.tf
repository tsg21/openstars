locals {
  image_registry = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

resource "google_cloud_run_v2_service" "backend" {
  name                 = "backend"
  location             = var.region
  invoker_iam_disabled = true

  template {
    service_account                  = "${var.project_number}-compute@developer.gserviceaccount.com"
    timeout                          = "10s"
    max_instance_request_concurrency = 4

    containers {
      image = "${local.image_registry}/backend:latest"

      env {
        name  = "STORAGE_BACKEND"
        value = "gcs"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = "openstars-games"
      }
      env {
        name  = "LOG_FORMAT"
        value = "json"
      }

      resources {
        cpu_idle          = true
        startup_cpu_boost = true
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      startup_probe {
        failure_threshold = 1
        period_seconds    = 240
        timeout_seconds   = 240
        tcp_socket {
          port = 8080
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 20
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version, scaling]
  }
}

resource "google_cloud_run_v2_service" "frontend" {
  name                 = "openstars-frontend"
  location             = var.region
  invoker_iam_disabled = true

  template {
    service_account                  = google_service_account.github_actions.email
    timeout                          = "10s"
    max_instance_request_concurrency = 4

    containers {
      image = "${local.image_registry}/frontend:latest"

      env {
        name  = "BACKEND_URL"
        value = "https://backend-${var.project_number}.${var.region}.run.app"
      }

      resources {
        cpu_idle          = true
        startup_cpu_boost = true
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      startup_probe {
        failure_threshold = 1
        period_seconds    = 240
        timeout_seconds   = 240
        tcp_socket {
          port = 8080
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version, scaling]
  }
}
