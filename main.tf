# gcp_vpc_project/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0" # 최신 버전에 맞춰서 조정 가능
    }
  }
}

provider "google" {
  project     = var.gcp_project_id
  region      = var.gcp_region
  zone        = var.gcp_zone
  credentials = file(var.credentials_file_path) # 서비스 계정 키 파일 경로
}

# VPC 네트워크 생성
resource "google_compute_network" "vpc_network" {
  name                    = var.network_name
  auto_create_subnetworks = false # 커스텀 서브넷을 사용할 것이므로 false로 설정
  routing_mode            = "REGIONAL" # 또는 GLOBAL
}

# 서브넷 생성
resource "google_compute_subnetwork" "subnet" {
  name          = var.subnet_name
  ip_cidr_range = var.subnet_ip_cidr_range
  region        = var.gcp_region
  network       = google_compute_network.vpc_network.self_link # 생성된 VPC 네트워크에 연결
}