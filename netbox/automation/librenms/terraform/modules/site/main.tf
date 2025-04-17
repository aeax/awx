# Check if location exists
data "librenms_locations" "existing" {
  count = var.existing_site ? 1 : 0
}

# Get existing devices if this is an existing site
data "librenms_devices" "existing_switches" {
  count = var.existing_site ? 1 : 0
  location = var.existing_site_name
}

locals {
  location_exists = var.existing_site ? contains(data.librenms_locations.existing[0].names, var.existing_site_name) : false
  
  # Extract existing switch numbers if this is an existing site
  existing_switch_numbers = var.existing_site ? [
    for device in data.librenms_devices.existing_switches[0].devices :
    tonumber(regex("_([0-9]+)$", device.display_name)[0])
    if can(regex("${var.switch_prefix}_[0-9]+$", device.display_name))
  ] : []
  
  # Find the highest existing switch number
  max_switch_number = length(local.existing_switch_numbers) > 0 ? max(local.existing_switch_numbers...) : 0
  
  # Create switch names with sequential numbers
  switch_configs = [
    for i, ip in var.switch_ips : {
      ip = ip
      name = "${var.switch_prefix}${format("%02d", local.max_switch_number + i + 1)}"
    }
  ]

  # Add gateway numbering logic
  existing_gateway_numbers = var.existing_site ? [
    for device in data.librenms_devices.existing_switches[0].devices :
    tonumber(regex("_([0-9]+)$", device.display_name)[0])
    if can(regex("${var.gateway_prefix}_[0-9]+$", device.display_name))
  ] : []
  
  max_gateway_number = length(local.existing_gateway_numbers) > 0 ? max(local.existing_gateway_numbers...) : 0
  
  gateway_configs = [
    for i, ip in var.gateway_ips : {
      ip = ip
      name = "${var.gateway_prefix}_${format("%02d", local.max_gateway_number + i + 1)}"
    }
  ]
}

variable "site_name" {
  description = "Name of the site"
  type = string
}

variable "network_prefix" {
  description = "Network prefix for the site"
  type = string
}

variable "existing_site" {
  description = "Whether this is part of an existing site"
  type = bool
  default = false
}

variable "existing_site_name" {
  description = "Name of existing site if this is a subsite"
  type = string
  default = ""
}

variable "firewall_ip" {
  description = "IP address of the firewall"
  type = string
}

variable "circuit_ip" {
  description = "IP address of the circuit"
  type = string
}

variable "gateway_prefix" {
  description = "Prefix for gateway names (e.g., 'ILDOC-CentraliaCC.c.GW')"
  type = string
}

variable "gateway_ips" {
  description = "List of gateway IP addresses"
  type = list(string)
}

variable "switch_prefix" {
  description = "Prefix for switch names (e.g., 'ILDOC-CentraliaCC.c.ILDOCSW')"
  type = string
}

variable "switch_ips" {
  description = "List of switch IP addresses"
  type = list(string)
}

# Create or use existing location
resource "librenms_location" "site" {
  count = var.existing_site ? (local.location_exists ? 0 : 1) : 1
  name = var.existing_site ? var.existing_site_name : var.site_name

  lifecycle {
    precondition {
      condition = !var.existing_site || local.location_exists
      error_message = "Specified existing site '${var.existing_site_name}' does not exist in LibreNMS"
    }
  }
}

# Add firewall device
resource "librenms_device" "firewall" {
  hostname = var.firewall_ip
  display_name = "${var.site_name} Firewall"
  location = var.existing_site ? var.existing_site_name : librenms_location.site[0].name
  snmp_disable = true
  force_add = true
}

# Add circuit device
resource "librenms_device" "circuit" {
  hostname = var.circuit_ip
  display_name = "${var.site_name} Circuit"
  location = var.existing_site ? var.existing_site_name : librenms_location.site[0].name
  snmp_disable = true
  force_add = true
}

# Replace single gateway resource with multiple
resource "librenms_device" "gateways" {
  for_each = { for gw in local.gateway_configs : gw.ip => gw }
  
  hostname = each.value.ip
  display_name = each.value.name
  location = var.existing_site ? var.existing_site_name : librenms_location.site[0].name
  snmp_disable = true
  force_add = true
}

# Add switch devices
resource "librenms_device" "switches" {
  for_each = { for switch in local.switch_configs : switch.ip => switch }
  
  hostname = each.value.ip
  display_name = each.value.name
  location = var.existing_site ? var.existing_site_name : librenms_location.site[0].name
  snmp_disable = true
  force_add = true
} 