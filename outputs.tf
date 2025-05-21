# gcp_vpc_project/outputs.tf

output "network_name" {
  description = "The name of the created VPC network"
  value       = google_compute_network.vpc_network.name
}

output "network_self_link" {
  description = "The self_link of the created VPC network"
  value       = google_compute_network.vpc_network.self_link
}

output "subnet_name" {
  description = "The name of the created subnetwork"
  value       = google_compute_subnetwork.subnet.name
}

output "subnet_self_link" {
  description = "The self_link of the created subnetwork"
  value       = google_compute_subnetwork.subnet.self_link
}