# GCP VM 자동 모니터링 및 알림 시스템 (Python + Terraform)

이 프로젝트는 Terraform을 사용하여 GCP에 모니터링 대상 VM 인프라를 구축하고, Python으로 작성된 Cloud Function을 통해 커스텀 지표(VM 도달 가능성)를 주기적으로 수집합니다. 수집된 지표는 Google Cloud Monitoring으로 전송되며, 정의된 조건(예: Ping 실패 지속)을 충족할 경우 자동으로 이메일 알림을 발송하는 시스템입니다.

**현재 상태:** 핵심 기능 (Phase 1-4) 완료.
* 인프라 프로비저닝 (VPC, VM, 방화벽)
* 서버리스 환경 구축 (Cloud Function, Cloud Scheduler, Pub/Sub, GCS 버킷)
* 커스텀 지표 수집 및 Cloud Monitoring 전송 자동화
* Cloud Monitoring 알림 정책 및 이메일 알림 채널 구성

---

## 주요 구현 기능

* **Terraform을 사용한 전체 인프라 코드화(IaC)**:
    * VPC 네트워크, 서브넷, 방화벽 규칙 (SSH, ICMP)
    * Compute Engine VM 인스턴스 2대
    * Cloud Storage 버킷 (Cloud Function 소스 코드 저장용)
    * Pub/Sub 토픽 (스케줄러와 함수 간 트리거용)
    * Cloud Function (Python 스크립트 실행 환경)
    * Cloud Scheduler (Cloud Function 주기적 실행)
    * Cloud Monitoring 알림 채널 (이메일)
    * Cloud Monitoring 알림 정책 (VM 도달 불가능 시 알림)
* **Python 기반 커스텀 지표 수집**:
    * Cloud Function 내에서 Python 스크립트 실행
    * VM 인스턴스의 네트워크 도달 가능성(Ping) 측정
* **자동화된 모니터링 및 알림**:
    * Cloud Scheduler에 의해 5분마다 모니터링 자동 실행
    * Cloud Monitoring으로 커스텀 지표 전송 및 시각화
    * 지정된 조건 충족 시 이메일을 통한 자동 알림 수신

---

## 사전 준비 사항

* Google Cloud Platform (GCP) 계정 및 과금 활성화
* [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install) 설치 및 초기화
* [Terraform](https://developer.hashicorp.com/terraform/downloads) 설치 및 PATH 설정
* Python 3.7 이상

---

## 설치 및 실행 방법

1.  **저장소 복제 (Clone)**
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd gcp-monitoring-project
    ```

2.  **GCP API 활성화**
    GCP 프로젝트에서 다음 API들이 활성화되어 있는지 확인합니다:
    - Compute Engine API
    - Cloud Monitoring API
    - Cloud Functions API
    - Cloud Scheduler API
    - Cloud Pub/Sub API
    - Eventarc API
    - Cloud Run Admin API
    - Cloud Build API
    - IAM API

3.  **서비스 계정 설정**
    * Cloud Function 실행을 위한 서비스 계정(`practerraform@...`)이 필요하며, 이 계정에는 최소한 `Compute 뷰어`, `Monitoring 측정항목 작성자`, `Pub/Sub 게시자` 등의 역할이 필요합니다. (Terraform 배포 시 사용한 사용자 계정이 프로젝트 소유자라면 대부분의 권한 문제를 해결해줍니다.)
    * Terraform 실행은 로컬에서 `gcloud auth application-default login`을 통해 사용자 계정으로 인증합니다.

4.  **Terraform 변수 파일 생성 (`terraform.tfvars`)**
    프로젝트 루트에 `terraform.tfvars` 파일을 생성하고 아래 내용을 채웁니다.
    ```terraform
    gcp_project_id = "YOUR-GCP-PROJECT-ID" // 예: golden-forge-460511-m5
    ```
    **주의:** 이 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않도록 합니다.

5.  **`main.tf` Cloud Function 서비스 계정 확인**
    `main.tf` 파일 내 `google_cloudfunctions2_function` 리소스의 `service_config` 블록에 있는 `service_account_email`이 올바른 서비스 계정 이메일로 설정되어 있는지 확인합니다.
    ```terraform
    service_config {
      # ...
      service_account_email = "practerraform@golden-forge-460511-m5.iam.gserviceaccount.com" // Cloud Function 실행용 서비스 계정
      # ...
    }
    ```

6.  **인프라 및 서버리스 환경 배포**
    ```bash
    terraform init
    terraform apply -auto-approve
    ```

7.  **이메일 알림 채널 인증**
    `terraform apply` 실행 후, `google_monitoring_notification_channel`에 지정한 이메일 주소로 수신된 Google Cloud 인증 메일의 링크를 클릭하여 채널을 활성화합니다.

8.  **시스템 작동 확인**
    * Cloud Scheduler가 5분마다 Cloud Function을 트리거합니다.
    * Cloud Function 로그에서 Python 스크립트 실행 기록을 확인합니다.
    * Cloud Monitoring의 Metrics Explorer에서 `custom.googleapis.com/vm/reachability` 지표가 5분마다 업데이트되는지 확인합니다.

9.  **알림 테스트**
    * VM 중 하나를 중지시키거나 ICMP 방화벽 규칙을 일시적으로 제거하여 Ping 실패를 유도합니다.
    * 몇 분 후 (알림 정책의 `duration` + 함수 실행 주기) 설정한 이메일로 알림이 오는지 확인합니다.
    * 테스트 후 VM 및 방화벽 설정을 원상 복구합니다.

---

## 인프라 삭제 (Teardown)

프로젝트 사용이 끝나면 모든 리소스를 삭제하여 불필요한 과금을 방지합니다.
```bash
terraform destroy -auto-approve


## 아키텍처
┌───────────────────────────┐                                  ┌────────────────────────────────────────────────────────────────────────┐
│      로컬 PC (Your PC)      │                                  │                            Google Cloud Platform (GCP)               │
│                           │                                  │                                                                        │
│   ┌───────────────────┐   │  1. `terraform apply`            │  ┌──────────────────┐     ┌──────────────────┐    ┌────────────────────┐
│   │   Terraform 코드   ├────────────────────────────────────> │  │   VM Instance x2 │<───┤   Cloud Function   │<──┤   Cloud Scheduler │ 
│   │  (main.tf, etc.)  │   │ (인프라 및 서버리스 환경 구축)     │  │  (monitoring-vpc)│     │  (Python 코드 실행)│   │  (매 5분마다 트리거)│ 
│   └───────────────────┘   │                                  │  └─────────┬────────┘     └─────────┬────────┘    └──────────┬────────┘ 
│                           │                                  │            │ 3. Ping 테스트        │ 4. 커스텀 지표  │ 2. Pub/Sub 호출 │ 
│   ┌───────────────────┐   │                                  │            │                     │    전송         │                 │ 
│   │      GitHub       │<──┼───────────────────────────────────┘            │                     ▼                 ▼                 
│   │ (코드 저장소)     │   │  6. `git push` (코드 변경사항)                 │               ┌──────────────────┐  ┌──────────────────┐  
│   └───────────────────┘   │                                  │               │            Cloud Monitoring  │  │   Pub/Sub Topic  
│                           │                                  │               └─────────────────────> │  (Metrics Explorer │  └───────┬────────┘  │  │
│                           │                                  │                               │   & Alerting)    │          │          │  │
│                           │                                  │                               └─────────┬────────┘          │          │  │
│                           │                                  │                                         │ 5. 알림 조건    │          │          │  │
│                           │                                  │                                         │    충족 시      │          │          │  │
│                           │                                  │                                         ▼                 │          │          │  │
│                           │                                  │                               ┌──────────────────┐          │          │  │
│                           │                                  │                               │  알림 채널 (Email)├<─────────┘          │  │
│                           │                                  │                               └──────────────────┘                        │  │
└───────────────────────────┘                                  └────────────────────────────────────────────────────────────────────────┘
