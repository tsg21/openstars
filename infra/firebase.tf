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

# Initialise Identity Platform / Firebase Authentication for the project.
# Enabling identitytoolkit.googleapis.com alone does not create this config —
# without it, signInWithCustomToken (and any other Identity Toolkit call)
# fails with CONFIGURATION_NOT_FOUND.
resource "google_identity_platform_config" "default" {
  provider = google-beta
  project  = var.project_id

  depends_on = [
    google_project_service.identitytoolkit,
    google_firebase_project.default,
  ]
}

# Native-mode Firestore database in var.region (single region, cheapest).
resource "google_firestore_database" "default" {
  provider         = google-beta
  project          = var.project_id
  name             = "(default)"
  location_id      = var.region
  type             = "FIRESTORE_NATIVE"
  concurrency_mode = "OPTIMISTIC"

  depends_on = [
    google_project_service.firestore,
    google_firebase_project.default,
  ]
}

# Composite index for list_games_for_player: filters on `players` (array-contains)
# and orders by `created_at`. Firestore auto-creates single-field indexes but
# requires an explicit composite index for a filter + order-by on different
# fields — the local emulator doesn't enforce this, so the gap only shows up
# against real Firestore.
resource "google_firestore_index" "games_by_player_created_at" {
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "games"

  fields {
    field_path   = "players"
    array_config = "CONTAINS"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }
}

# Composite index for the override half of list_games_for_player_or_override:
# filters on `allow_player_override` and orders by `created_at`.
#
# The task file specified `updated_at` here, but the query orders by `created_at`
# to match list_games_for_player above — the two result sets are merged and sorted
# together in Python, and ordering the halves by different fields would make the
# merged "most-recent first" contract meaningless. Ordering on `updated_at` would
# also reshuffle the list every time a player submitted a turn.
resource "google_firestore_index" "games_by_override_created_at" {
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "games"

  fields {
    field_path = "allow_player_override"
    order      = "ASCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }
}

# Deploy security rules restricting client reads to games the token holder owns.
resource "google_firebaserules_ruleset" "firestore" {
  project = var.project_id
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

# Web app registration — required to get a Firebase Web API key for the frontend.
resource "google_firebase_web_app" "frontend" {
  provider     = google-beta
  project      = var.project_id
  display_name = "openstars-frontend"

  depends_on = [google_firebase_project.default]
}

data "google_firebase_web_app_config" "frontend" {
  provider   = google-beta
  project    = var.project_id
  web_app_id = google_firebase_web_app.frontend.app_id
}

output "firebase_web_api_key" {
  value = data.google_firebase_web_app_config.frontend.api_key
}

output "firebase_web_auth_domain" {
  value = data.google_firebase_web_app_config.frontend.auth_domain
}
