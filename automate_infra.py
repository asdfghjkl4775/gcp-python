
# -*- coding: utf-8 -*-
# gcp_vpc_project/automate_infra.py


import os
from python_terraform import Terraform

# Terraform 작업 디렉토리 (tf 파일들이 있는 곳)
TF_WORKING_DIR = "."  # 현재 디렉토리

# GCP 서비스 계정 키 파일 경로 (Terraform 변수와 일치시키거나 직접 지정)
# 이 경로가 Terraform variables.tf 파일의 credentials_file_path 기본값과 같거나,
# 아래 terraform.apply() 시점에 변수로 전달해야 합니다.
GCP_CREDENTIALS_FILE = "credentials/gcp-key.json" # 실제 경로로 수정하세요.
GCP_PROJECT_ID = "782550109941"  # 실제 프로젝트 ID로 수정하세요.

def run_terraform():
    tf = Terraform(working_dir=TF_WORKING_DIR)

    print("Initializing Terraform...")
    # Terraform 초기화 시 backend 설정 등이 있다면 여기서 구성 가능
    return_code, stdout, stderr = tf.init()
    if return_code != 0:
        print("Error initializing Terraform:")
        print(stdout)
        print(stderr)
        return
    print("Terraform initialized successfully.")
    print("-" * 30)

    # Terraform 변수 설정 (variables.tf에 정의된 변수들)
    tf_vars = {
        "gcp_project_id": GCP_PROJECT_ID,
        "credentials_file_path": GCP_CREDENTIALS_FILE
        # variables.tf 에 정의된 다른 변수들의 기본값을 사용하거나 여기서 오버라이드 가능
        # "network_name": "prod-network",
    }

    print("Planning infrastructure changes...")
    return_code, stdout, stderr = tf.plan(capture_output=True, var=tf_vars)
    if return_code != 0 and not "Plan: 0 to add, 0 to change, 0 to destroy." in stdout : # 변경 사항이 없을 때도 return_code가 0이 아닐 수 있음
        print("Error planning Terraform:")
        # print(f"Return code: {return_code}") # Debug
        # print(stdout) # Debug
        # print(stderr) # Debug
        # 상세 에러 메시지를 확인하려면 위 주석을 해제하세요.
        # 때로는 plan 결과가 변경 없음(0 to add...) 일 때도 return_code가 0이 아닌 경우가 있어, stderr로 실제 에러 유무 판단
        if stderr:
            print("Error during plan:")
            print(stdout)
            print(stderr)
            return
        elif "Error:" in stdout: # stdout에 에러 메시지가 포함된 경우
            print("Error during plan (captured in stdout):")
            print(stdout)
            return
    print("Terraform plan generated.")
    print(stdout) # Plan 결과 출력
    print("-" * 30)


    print("Applying infrastructure changes...")
    # '-auto-approve' 옵션으로 별도 승인 없이 바로 적용
    # capture_output=False로 하면 실시간 출력을 볼 수 있습니다.
    # return_code, stdout, stderr = tf.apply(skip_plan=True, auto_approve=IsFlagged, capture_output=False, var=tf_vars)
    return_code, stdout, stderr = tf.apply(skip_plan=True, auto_approve=True, var=tf_vars)

    if return_code != 0:
        print("Error applying Terraform configuration:")
        print(stdout)
        print(stderr)
        return
    print("Terraform apply completed successfully.")
    print(stdout)
    print("-" * 30)

    print("Terraform outputs:")
    outputs = tf.output()
    if outputs:
        for name, value in outputs.items():
            print(f"- {name}: {value['value']}")
    else:
        print("No outputs defined or an error occurred.")
    print("-" * 30)

def destroy_terraform():
    tf = Terraform(working_dir=TF_WORKING_DIR)
    
    # init은 destroy 전에도 필요할 수 있습니다. (provider plugin 로드 등)
    # 이미 init이 되어 있다면 생략해도 무방하나, 안전하게 포함.
    print("Initializing Terraform for destroy...")
    tf.init()

    tf_vars = {
        "gcp_project_id": GCP_PROJECT_ID,
        "credentials_file_path": GCP_CREDENTIALS_FILE
    }

    print("Destroying infrastructure...")
    return_code, stdout, stderr = tf.destroy(auto_approve=True, var=tf_vars)
    if return_code != 0:
        print("Error destroying Terraform infrastructure:")
        print(stdout)
        print(stderr)
        return
    print("Terraform destroy completed successfully.")
    print(stdout)

if __name__ == "__main__":
    # GCP 서비스 계정 키 파일 경로를 환경 변수로 설정 (선택 사항, Terraform provider 설정에서 직접 경로를 사용하면 불필요)
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_CREDENTIALS_FILE

    # 인프라 생성
    run_terraform()

    # 인프라 삭제 (필요시 주석 해제)
    # user_input = input("Do you want to destroy the infrastructure? (yes/no): ")
    # if user_input.lower() == 'yes':
    #     destroy_terraform()