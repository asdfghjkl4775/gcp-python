# gcp-monitoring-project/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.region
  zone    = var.zone
  credentials = file(var.credentials_file_path)
}

# 1. VM들이 사용할 VPC 네트워크 생성
resource "google_compute_network" "vpc_network" {
  name                    = "monitoring-vpc"
  auto_create_subnetworks = false
}

# 2. VPC 네트워크 내에 서브넷 생성
resource "google_compute_subnetwork" "subnet" {
  name          = "monitoring-subnet"
  ip_cidr_range = "10.10.1.0/24"
  network       = google_compute_network.vpc_network.self_link
  region        = var.region
}

# 3. SSH (포트 22) 접속을 허용하는 방화벽 규칙 생성
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh-for-monitoring-vms"
  network = google_compute_network.vpc_network.self_link

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # 경고: 0.0.0.0/0은 모든 IP에서의 접속을 허용합니다.
  # 테스트 환경에서는 편리하지만, 실제 운영 환경에서는
  # 본인의 IP 주소 대역으로 제한하는 것이 안전합니다.
  source_ranges = ["0.0.0.0/0"]
}

# 4. 모니터링할 VM 인스턴스 2개 생성
resource "google_compute_instance" "vm_instance" {
  # for_each를 사용하여 'vm_names' 변수 리스트에 있는 각 이름에 대해 VM을 생성
  for_each = toset(var.vm_names)

  allow_stopping_for_update = true
  name         = each.value
  machine_type = "e2-micro" # 비용 효율적인 머신 타입 (무료 등급 포함 가능)
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11" # Debian 11 OS 이미지 사용
    }
  }

  network_interface {
    network    = google_compute_network.vpc_network.id
    # 👇👇👇 이 부분을 수정하세요! 👇👇👇
    subnetwork = google_compute_subnetwork.subnet.id # .subnet 을 추가
    access_config {
      # 외부 IP 주소를 할당하여 인터넷에서 접속 가능하게 함
    }
  }

  # 이 VM은 SSH 방화벽 규칙이 생성된 후에 만들어지도록 의존성 명시
  depends_on = [
    google_compute_firewall.allow_ssh
  ]
}

resource "google_compute_firewall" "allow_icmp" {
  name    = "allow-icmp-for-ping"
  network = google_compute_network.vpc_network.self_link
  allow {
    protocol = "icmp"
  }
  source_ranges = ["0.0.0.0/0"]
}