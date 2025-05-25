# gcp-monitoring-project/collect_metrics.py

import time
from google.cloud import compute_v1, monitoring_v3
from google.protobuf.timestamp_pb2 import Timestamp
from pythonping import ping

# --- 설정 (자신의 환경에 맞게 수정) ---
PROJECT_ID = "golden-forge-460511-m5"  # 1단계에서 확인한 본인의 '프로젝트 ID'
ZONE = "asia-northeast3-a"           # VM이 생성된 존
CUSTOM_METRIC_TYPE = "custom.googleapis.com/vm/reachability" # 우리가 만들 커스텀 지표 이름

def list_instances(project_id, zone):
    """지정된 프로젝트와 존에 있는 모든 VM 인스턴스의 목록을 반환합니다."""
    try:
        instance_client = compute_v1.InstancesClient()
        instance_list = instance_client.list(project=project_id, zone=zone)
        print(f"Found {len(instance_list.items)} instances in zone {zone}.")
        return list(instance_list)
    except Exception as e:
        print(f"Error listing instances: {e}")
        return []

def check_instance_reachability(ip_address):
    """주어진 IP 주소로 Ping을 보내고 성공 여부를 반환합니다."""
    if not ip_address:
        return 0.0  # IP 주소가 없으면 실패로 간주

    try:
        print(f"Pinging {ip_address}...")
        response = ping(ip_address, count=1, timeout=1)
        if response.success():
            print("Ping successful.")
            return 1.0  # 성공 시 1.0 (float)
        else:
            print("Ping failed.")
            return 0.0  # 실패 시 0.0 (float)
    except Exception as e:
        # 권한 문제 등으로 Ping이 실패할 수 있음 (예: ICMP가 방화벽에서 차단)
        print(f"An error occurred during ping: {e}")
        return 0.0

def write_custom_metric(project_id, vm_name, instance_id, value):
    """Cloud Monitoring에 커스텀 지표를 기록합니다."""
    metric_client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    # 시계열(Time Series) 데이터 생성
    series = monitoring_v3.TimeSeries()

    # 1. 어떤 종류의 지표인지 정의
    series.metric.type = CUSTOM_METRIC_TYPE
    series.metric.labels["instance_name"] = vm_name  # 커스텀 라벨: VM 이름

    # 2. 어떤 리소스에 대한 지표인지 정의
    series.resource.type = "gce_instance"
    series.resource.labels["project_id"] = project_id
    series.resource.labels["zone"] = ZONE
    series.resource.labels["instance_id"] = instance_id

    # 3. 실제 값과 시간을 기록
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": nanos}}
    )
    point = monitoring_v3.Point(
        {"interval": interval, "value": {"double_value": value}}
    )
    series.points = [point]

    try:
        print(f"Writing metric for {vm_name} with value {value}...")
        metric_client.create_time_series(name=project_name, time_series=[series])
        print("Successfully wrote metric.")
    except Exception as e:
        print(f"Error writing time series data: {e}")

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    instances = list_instances(PROJECT_ID, ZONE)

    if not instances:
        print("No instances found to monitor.")
    else:
        for instance in instances:
            # 외부 IP가 있는 경우에만 Ping 테스트 수행
            external_ip = None
            if instance.network_interfaces and instance.network_interfaces[0].access_configs:
                # 👇👇👇 이 부분을 수정하세요! (nat_ip -> nat_i_p) 👇👇👇
                external_ip = instance.network_interfaces[0].access_configs[0].nat_i_p

            print("-" * 30)
            print(f"Processing VM: {instance.name} (ID: {instance.id})")

            # Ping 테스트 실행
            reachability_value = check_instance_reachability(external_ip)

            # Cloud Monitoring에 결과 기록
            write_custom_metric(PROJECT_ID, instance.name, str(instance.id), reachability_value)
            print("-" * 30)