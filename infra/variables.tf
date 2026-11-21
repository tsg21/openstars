variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "openstars"
}

variable "project_number" {
  description = "GCP project number"
  type        = string
  default     = "1044626254790"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "europe-west1"
}

variable "google_oauth_client_id" {
  description = "OAuth 2.0 web client ID backing Google sign-in (auto-created by the Firebase console)"
  type        = string
}

variable "google_oauth_client_secret" {
  description = "OAuth 2.0 web client secret backing Google sign-in"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository in owner/repo format"
  type        = string
  default     = "tsg21/openstars"
}
