# gcp_vpc_project/variables.tf

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "782550109941" # 여기에 직접 입력하거나 실행 시점에 주입
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast3" # 서울 리전
}

variable "gcp_zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast3-a" # 서울 a 존
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "my-custom-vpc"
}

variable "subnet_name" {
  description = "Name of the subnetwork"
  type        = string
  default     = "my-custom-subnet"
}

variable "subnet_ip_cidr_range" {
  description = "IP CIDR range for the subnetwork"
  type        = string
  default     = "10.0.1.0/24"
}

variable "credentials_file_path" {
  description = "Path to the GCP service account key file"
  type        = string
  # default     = "credentials/gcp-key.json" # 실제 경로로 수정
}