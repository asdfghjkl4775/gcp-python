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
#  credentials = file(var.credentials_file_path)
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

# --- Phase 3: 서버리스 자동화 ---

# 6. Cloud Function 소스 코드를 업로드할 GCS 버킷 생성
resource "google_storage_bucket" "source_bucket" {
  # 버킷 이름은 전역적으로 고유해야 하므로, 프로젝트 ID를 포함시킵니다.
  name     = "${var.gcp_project_id}-function-source"
  location = var.region
  uniform_bucket_level_access = true
}

# 7. functions 폴더를 zip으로 압축
data "archive_file" "source_zip" {
  type        = "zip"
  source_dir  = "${path.module}/functions" # functions 폴더 경로
  output_path = "${path.module}/source.zip"
}

# 8. 압축된 소스 코드를 GCS 버킷에 업로드
resource "google_storage_bucket_object" "source_object" {
  name   = "source.zip"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.source_zip.output_path
}

# 10. 스케줄러와 함수를 연결할 Pub/Sub 토픽
resource "google_pubsub_topic" "monitoring_trigger" {
  name = "monitoring-trigger-topic"
}


resource "google_cloudfunctions2_function" "monitoring_function" {
  name     = "vm-monitoring-function"
  location = var.region

  build_config {
    runtime     = "python311" 
    entry_point = "monitor_vms_pubsub"
    source {
      storage_source {
        bucket = google_storage_bucket.source_bucket.name
        object = google_storage_bucket_object.source_object.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    # 👇👇👇 이 부분을 직접 서비스 계정 이메일로 수정합니다. 👇👇👇
    service_account_email = "practerraform@golden-forge-460511-m5.iam.gserviceaccount.com" # 본인의 서비스 계정 전체 이메일

    environment_variables = {
      GCP_PROJECT_ID = var.gcp_project_id
      GCP_ZONE       = var.zone
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.monitoring_trigger.id
  }

  depends_on = [google_storage_bucket_object.source_object]
}

# 12. Cloud Scheduler 작업 정의
resource "google_cloud_scheduler_job" "monitoring_scheduler" {
  name     = "vm-monitoring-scheduler"
  schedule = "*/5 * * * *" # 매 5분마다 실행 (Crontab 형식)
  
  pubsub_target {
    topic_name = google_pubsub_topic.monitoring_trigger.id
    data       = base64encode("start") # 함수에 전달할 메시지 (필수는 아님)
  }
}


# --- Phase 4: 자동 알림 설정 ---

# 13. 알림을 받을 이메일 채널 생성
resource "google_monitoring_notification_channel" "email_channel" {
  project      = var.gcp_project_id // 명시적으로 프로젝트 ID 지정
  display_name = "Admin Email Notification"
  type         = "email" // 다른 타입 예시: "sms", "slack", "pagerduty" 등
  labels = {
    # 👇👇👇 알림을 받을 실제 본인의 이메일 주소로 변경하세요! 👇👇👇
    email_address = "asdfghjkl4775@gmail.com"
  }
  description = "Notification channel for critical VM alerts via email."
}


# 14. VM 도달 불가능 시 알림을 보내는 정책
resource "google_monitoring_alert_policy" "vm_unreachable_alert" {
  project      = var.gcp_project_id // 명시적으로 프로젝트 ID 지정
  display_name = "VM Unreachable Alert"
  combiner     = "OR" // 여러 조건 중 하나라도 만족하면 알림 (여기서는 조건이 하나)

  conditions {
    display_name = "VM is unreachable (Ping Failed)"
    condition_threshold {
      # 모니터링할 지표를 지정합니다.
      filter     = "metric.type=\"custom.googleapis.com/vm/reachability\" resource.type=\"gce_instance\""
      
      # 비교 조건: 값이 0.5보다 "작으면" (즉, 0이면)
      comparison = "COMPARISON_LT" 
      threshold_value = 0.5        
      
      # 지속 시간: 위 조건이 5분(300초) 동안 지속되면 알림 발생
      duration   = "300s"         
      
      trigger {
        # 지속 시간 내에 조건이 1번 발생하면 트리거
        count = 1 
      }
      
      # 집계 방식: 5분 동안의 데이터를 어떻게 처리할지
      aggregations {
        alignment_period   = "300s"         // 5분 간격으로 데이터를 정렬/집계
        per_series_aligner = "ALIGN_MEAN"     // 5분 동안의 평균값 사용 (0 또는 1)
      }
    }
  }

  # 알림을 보낼 채널 지정
  notification_channels = [
    google_monitoring_notification_channel.email_channel.id // 위에서 만든 이메일 채널의 ID 참조
  ]

  # 알림에 추가적인 사용자 정의 라벨을 넣을 수 있음
  user_labels = {
    severity = "critical"
    category = "availability"
  }
}