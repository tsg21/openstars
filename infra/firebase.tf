# Enable required APIs.
resource "google_project_service" "firestore" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firebase" {
  service            = "firebase.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "identitytoolkit" {
  service            = "identitytoolkit.googleapis.com"
  disable_on_destroy = false
}

# Enable Firebase on the project (one-way — cannot be undone via Terraform).
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id

  depends_on = [google_project_service.firebase]
}

# Native-mode Firestore database in eur3 (EU multi-region).
resource "google_firestore_database" "default" {
  provider         = google-beta
  project          = var.project_id
  name             = "(default)"
  location_id      = "eur3"
  type             = "FIRESTORE_NATIVE"
  concurrency_mode = "OPTIMISTIC"

  depends_on = [
    google_project_service.firestore,
    google_firebase_project.default,
  ]
}

# Deploy security rules restricting client reads to games the token holder owns.
resource "google_firebaserules_ruleset" "firestore" {
  project  = var.project_id
  source {
    files {
      name    = "firestore.rules"
      content = file("${path.module}/firestore.rules")
    }
  }

  depends_on = [google_firestore_database.default]
}

resource "google_firebaserules_release" "firestore" {
  name         = "cloud.firestore"
  ruleset_name = google_firebaserules_ruleset.firestore.name
  project      = var.project_id
}
