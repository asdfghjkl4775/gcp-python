# gcp-monitoring-project/outputs.tf

output "vm_external_ips" {
  description = "External IP addresses of the created VM instances"
  value = {
    for vm in google_compute_instance.vm_instance : vm.name => vm.network_interface[0].access_config[0].nat_ip
  }
}