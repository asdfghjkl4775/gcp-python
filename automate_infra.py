
# -*- coding: utf-8 -*-
# gcp_vpc_project/automate_infra.py


import os
from python_terraform import Terraform

# Terraform �۾� ���丮 (tf ���ϵ��� �ִ� ��)
TF_WORKING_DIR = "."  # ���� ���丮

# GCP ���� ���� Ű ���� ��� (Terraform ������ ��ġ��Ű�ų� ���� ����)
# �� ��ΰ� Terraform variables.tf ������ credentials_file_path �⺻���� ���ų�,
# �Ʒ� terraform.apply() ������ ������ �����ؾ� �մϴ�.
GCP_CREDENTIALS_FILE = "credentials/gcp-key.json" # ���� ��η� �����ϼ���.
GCP_PROJECT_ID = "782550109941"  # ���� ������Ʈ ID�� �����ϼ���.

def run_terraform():
    tf = Terraform(working_dir=TF_WORKING_DIR)

    print("Initializing Terraform...")
    # Terraform �ʱ�ȭ �� backend ���� ���� �ִٸ� ���⼭ ���� ����
    return_code, stdout, stderr = tf.init()
    if return_code != 0:
        print("Error initializing Terraform:")
        print(stdout)
        print(stderr)
        return
    print("Terraform initialized successfully.")
    print("-" * 30)

    # Terraform ���� ���� (variables.tf�� ���ǵ� ������)
    tf_vars = {
        "gcp_project_id": GCP_PROJECT_ID,
        "credentials_file_path": GCP_CREDENTIALS_FILE
        # variables.tf �� ���ǵ� �ٸ� �������� �⺻���� ����ϰų� ���⼭ �������̵� ����
        # "network_name": "prod-network",
    }

    print("Planning infrastructure changes...")
    return_code, stdout, stderr = tf.plan(capture_output=True, var=tf_vars)
    if return_code != 0 and not "Plan: 0 to add, 0 to change, 0 to destroy." in stdout : # ���� ������ ���� ���� return_code�� 0�� �ƴ� �� ����
        print("Error planning Terraform:")
        # print(f"Return code: {return_code}") # Debug
        # print(stdout) # Debug
        # print(stderr) # Debug
        # �� ���� �޽����� Ȯ���Ϸ��� �� �ּ��� �����ϼ���.
        # ���δ� plan ����� ���� ����(0 to add...) �� ���� return_code�� 0�� �ƴ� ��찡 �־�, stderr�� ���� ���� ���� �Ǵ�
        if stderr:
            print("Error during plan:")
            print(stdout)
            print(stderr)
            return
        elif "Error:" in stdout: # stdout�� ���� �޽����� ���Ե� ���
            print("Error during plan (captured in stdout):")
            print(stdout)
            return
    print("Terraform plan generated.")
    print(stdout) # Plan ��� ���
    print("-" * 30)


    print("Applying infrastructure changes...")
    # '-auto-approve' �ɼ����� ���� ���� ���� �ٷ� ����
    # capture_output=False�� �ϸ� �ǽð� ����� �� �� �ֽ��ϴ�.
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
    
    # init�� destroy ������ �ʿ��� �� �ֽ��ϴ�. (provider plugin �ε� ��)
    # �̹� init�� �Ǿ� �ִٸ� �����ص� �����ϳ�, �����ϰ� ����.
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
    # GCP ���� ���� Ű ���� ��θ� ȯ�� ������ ���� (���� ����, Terraform provider �������� ���� ��θ� ����ϸ� ���ʿ�)
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_CREDENTIALS_FILE

    # ������ ����
    run_terraform()

    # ������ ���� (�ʿ�� �ּ� ����)
    # user_input = input("Do you want to destroy the infrastructure? (yes/no): ")
    # if user_input.lower() == 'yes':
    #     destroy_terraform()