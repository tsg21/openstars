# Required for google_project_iam_custom_role below (projects.roles.*).
# Was never explicitly enabled — earlier applies ran via CI service-account
# credentials, which don't hit the same quota-project enablement check that
# user ADC credentials do once billing_project/user_project_override is set.
resource "google_project_service" "iam" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions CI/CD"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"
}

# Grant the backend Cloud Run service account Firestore access and the ability
# to sign Firebase custom tokens using default credentials.
locals {
  backend_sa = "${var.project_number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "backend_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${local.backend_sa}"
}

# serviceAccountTokenCreator on itself lets the default SA sign JWTs for
# Firebase custom tokens without a separate key file.
resource "google_service_account_iam_member" "backend_token_creator" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${local.backend_sa}"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${local.backend_sa}"
}

# Allow the GitHub Actions workflow to impersonate the service account.
resource "google_service_account_iam_member" "github_wif" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# Push images to Artifact Registry and deploy Cloud Run services (project-level grants).
resource "google_project_iam_member" "github_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Narrow custom role (rather than roles/firebase.viewer, which bundles
# read access to unrelated products) so CI can read the web app's SDK
# config to inject into the frontend build.
resource "google_project_iam_custom_role" "firebase_web_config_reader" {
  role_id     = "firebaseWebConfigReader"
  title       = "Firebase Web Config Reader"
  description = "Read-only access to Firebase web app config"
  permissions = [
    "firebase.projects.get",
    "firebase.clients.get",
    "firebase.clients.list",
  ]

  depends_on = [google_project_service.iam]
}

resource "google_project_iam_member" "github_firebase_web_config_reader" {
  project = var.project_id
  role    = google_project_iam_custom_role.firebase_web_config_reader.id
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# WIF-issued tokens have no implicit quota project, so calling the Firebase
# REST API with an explicit X-Goog-User-Project header (as build-frontend.yml
# does) needs this to avoid a quota-project permission error.
resource "google_project_iam_member" "github_service_usage_consumer" {
  project = var.project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
