# -*- coding: utf-8 -*-

import os
import time
from google.cloud import compute_v1, monitoring_v3
from pythonping import ping

# --- 설정: 이제 하드코딩 대신 환경 변수에서 값을 읽어옵니다 ---
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
ZONE = os.environ.get("GCP_ZONE")
CUSTOM_METRIC_TYPE = "custom.googleapis.com/vm/reachability"

def write_custom_metric(project_id, vm_name, instance_id, zone, value):
    """Cloud Monitoring에 커스텀 지표를 기록합니다."""
    metric_client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    series = monitoring_v3.TimeSeries()

    series.metric.type = CUSTOM_METRIC_TYPE
    series.metric.labels["instance_name"] = vm_name

    series.resource.type = "gce_instance"
    series.resource.labels["project_id"] = project_id
    series.resource.labels["zone"] = zone
    series.resource.labels["instance_id"] = instance_id

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": nanos}}
    )
    point = monitoring_v3.Point(
        {"interval": interval, "value": {"double_value": float(value)}}
    )
    series.points = [point]

    try:
        print(f"Writing metric for {vm_name} with value {value}...")
        metric_client.create_time_series(name=project_name, time_series=[series])
        print("Successfully wrote metric.")
    except Exception as e:
        print(f"Error writing time series data: {e}")

def monitor_vms_pubsub(event, context):
    """Pub/Sub에 의해 트리거되는 Cloud Function의 메인 함수."""
    print("Starting VM monitoring function...")
    if not PROJECT_ID or not ZONE:
        raise ValueError("GCP_PROJECT_ID and GCP_ZONE environment variables must be set.")

    try:
        instance_client = compute_v1.InstancesClient()
        instance_list = instance_client.list(project=PROJECT_ID, zone=ZONE)
        print(f"Found {len(instance_list.items)} instances in zone {ZONE}.")

        for instance in instance_list:
            external_ip = None
            if instance.network_interfaces and instance.network_interfaces[0].access_configs:
                external_ip = instance.network_interfaces[0].access_configs[0].nat_i_p

            print("-" * 30)
            print(f"Processing VM: {instance.name} (ID: {instance.id})")

            if external_ip:
                response = ping(external_ip, count=1, timeout=1)
                reachability_value = 1.0 if response.success() else 0.0
                print(f"Ping to {external_ip} successful: {response.success()}")
            else:
                reachability_value = 0.0
                print("No external IP found, marking as unreachable.")

            write_custom_metric(PROJECT_ID, instance.name, str(instance.id), ZONE, reachability_value)
            print("-" * 30)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")