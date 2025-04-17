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

variable "gateway_ip" {
  description = "IP address of the gateway"
  type = string
}

variable "switch_ips" {
  description = "List of switch IP addresses"
  type = list(string)
}

# Create or use existing location
resource "librenms_location" "site" {
  name = var.existing_site ? var.existing_site_name : var.site_name
  count = var.existing_site ? 0 : 1
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

# Add gateway device
resource "librenms_device" "gateway" {
  hostname = var.gateway_ip
  display_name = "${var.site_name} Gateway"
  location = var.existing_site ? var.existing_site_name : librenms_location.site[0].name
  snmp_disable = true
  force_add = true
}

# Add switch devices
resource "librenms_device" "switches" {
  for_each = toset(var.switch_ips)
  
  hostname = each.value
  display_name = "${var.site_name} Switch ${index(var.switch_ips, each.value) + 1}"
  location = var.existing_site ? var.existing_site_name : librenms_location.site[0].name
  snmp_disable = true
  force_add = true
} 