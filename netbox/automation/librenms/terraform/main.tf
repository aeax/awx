terraform {
  required_providers {
    http = {
      source = "hashicorp/http"
      version = "~> 3.0"
    }
  }
}

provider "http" {}

locals {
  librenms_headers = {
    "X-Auth-Token" = var.librenms_api_token
    "Content-Type" = "application/json"
  }
  
  # Import site definitions from YAML
  site_definitions = yamldecode(file("${path.module}/sites/sites.yaml"))
}

# Create null resources to manage devices
resource "null_resource" "devices" {
  for_each = local.site_definitions

  provisioner "local-exec" {
    command = <<-EOT
      # Add firewall
      echo "Adding firewall ${each.key}..."
      response=$(curl -s -X POST "${var.librenms_url}/api/v0/devices" \
        -H "X-Auth-Token: ${var.librenms_api_token}" \
        -H "Content-Type: application/json" \
        -d '{
          "hostname": "${each.value.firewall_ip}",
          "display": "${each.key} Firewall",
          "snmp_disable": true,
          "force_add": true,
          "location": "${try(each.value.existing_site_name, each.key)}"
        }')
      echo "Firewall response: $response"
      sleep 2

      # Add circuit
      echo "Adding circuit ${each.key}..."
      response=$(curl -s -X POST "${var.librenms_url}/api/v0/devices" \
        -H "X-Auth-Token: ${var.librenms_api_token}" \
        -H "Content-Type: application/json" \
        -d '{
          "hostname": "${each.value.circuit_ip}",
          "display": "${each.key} Circuit",
          "snmp_disable": true,
          "force_add": true,
          "location": "${try(each.value.existing_site_name, each.key)}"
        }')
      echo "Circuit response: $response"
      sleep 2

      # Add gateways
      %{ for idx, ip in each.value.gateway_ips }
      echo "Adding gateway ${idx + 1}..."
      response=$(curl -s -X POST "${var.librenms_url}/api/v0/devices" \
        -H "X-Auth-Token: ${var.librenms_api_token}" \
        -H "Content-Type: application/json" \
        -d '{
          "hostname": "${ip}",
          "display": "${each.value.gateway_prefix}${format("%02d", idx + 1)}",
          "snmp_disable": true,
          "force_add": true,
          "location": "${try(each.value.existing_site_name, each.key)}"
        }')
      echo "Gateway ${idx + 1} response: $response"
      sleep 2
      %{ endfor }

      # Add switches
      %{ for idx, ip in each.value.switch_ips }
      echo "Adding switch ${idx + 1}..."
      response=$(curl -s -X POST "${var.librenms_url}/api/v0/devices" \
        -H "X-Auth-Token: ${var.librenms_api_token}" \
        -H "Content-Type: application/json" \
        -d '{
          "hostname": "${ip}",
          "display": "${each.value.switch_prefix}${format("%02d", idx + 1)}",
          "snmp_disable": true,
          "force_add": true,
          "location": "${try(each.value.existing_site_name, each.key)}"
        }')
      echo "Switch ${idx + 1} response: $response"
      sleep 2
      %{ endfor }
    EOT
  }
} 