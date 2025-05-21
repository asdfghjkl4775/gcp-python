# gcp_vpc_project/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0" # �ֽ� ������ ���缭 ���� ����
    }
  }
}

provider "google" {
  project     = var.gcp_project_id
  region      = var.gcp_region
  zone        = var.gcp_zone
  credentials = file(var.credentials_file_path) # ���� ���� Ű ���� ���
}

# VPC ��Ʈ��ũ ����
resource "google_compute_network" "vpc_network" {
  name                    = var.network_name
  auto_create_subnetworks = false # Ŀ���� ������� ����� ���̹Ƿ� false�� ����
  routing_mode            = "REGIONAL" # �Ǵ� GLOBAL
}

# ����� ����
resource "google_compute_subnetwork" "subnet" {
  name          = var.subnet_name
  ip_cidr_range = var.subnet_ip_cidr_range
  region        = var.gcp_region
  network       = google_compute_network.vpc_network.self_link # ������ VPC ��Ʈ��ũ�� ����
}