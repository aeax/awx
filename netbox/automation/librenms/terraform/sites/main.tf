terraform {
  required_providers {
    librenms = {
      source = "healyt/librenms"
      version = "~> 1.0"
    }
  }
}

provider "librenms" {
  url = var.librenms_url
  api_token = var.librenms_api_token
}

# Import site definitions
locals {
  site_definitions = yamldecode(file("${path.module}/sites.yaml"))
}

# Create sites and devices from YAML definitions
module "sites" {
  source = "../modules/site"
  for_each = local.site_definitions

  site_name = each.key
  network_prefix = each.value.network_prefix
  existing_site = try(each.value.existing_site, false)
  existing_site_name = try(each.value.existing_site_name, "")
  
  firewall_ip = each.value.firewall_ip
  circuit_ip = each.value.circuit_ip
  gateway_ip = each.value.gateway_ip
  switch_ips = each.value.switch_ips
} 