resource "google_artifact_registry_repository" "images" {
  repository_id = "openstars-frontend"
  location      = var.region
  format        = "DOCKER"
  description   = "Docker images for frontend and backend services"
}
