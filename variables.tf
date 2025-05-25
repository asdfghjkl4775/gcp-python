# project_id = 782550109941
# gcp-monitoring-project/variables.tf
# terraform plan -var="782550109941"

variable "gcp_project_id" {
  description = "782550109941"
  type        = string
}

variable "credentials_file_path" {
  description = "Path to the GCP service account key file"
  type        = string
  default     = "credentials/gcp-key.json"
}

variable "region" {
  description = "GCP Region for the resources"
  type        = string
  default     = "asia-northeast3" # 서울 리전
}

variable "zone" {
  description = "GCP Zone for the resources"
  type        = string
  default     = "asia-northeast3-a" # 서울 a 존
}

variable "vm_names" {
  description = "A list of VM instance names to create"
  type        = list(string)
  default     = ["monitor-target-vm-1", "monitor-target-vm-2"]
}