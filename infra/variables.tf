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

variable "github_repo" {
  description = "GitHub repository in owner/repo format"
  type        = string
  default     = "tsg21/openstars"
}
