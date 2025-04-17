# Declare the Fortinet manufacturer
resource "netbox_manufacturer" "fortinet" {
  name = "Fortinet"
  slug = "fortinet"  # Match existing slug
}

# Declare device roles
resource "netbox_device_role" "firewall_role" {
  name      = "Firewall"
  color_hex = "00ff00"  # Added # prefix
  slug      = "firewall"  # Match existing slug
}

resource "netbox_device_role" "switch_role" {
  name      = "Switch"
  color_hex = "00ff00"  # Added # prefix
  slug      = "switch"  # Match existing slug
}

resource "netbox_device_role" "ap_role" {
  name      = "Access Point"
  color_hex = "00ff00"  # Added # prefix
  slug      = "access-point"  # Match existing slug
}

# Declare device types
resource "netbox_device_type" "fortigate" {
  model           = "FortiGate"
  manufacturer_id = netbox_manufacturer.fortinet.id
}

resource "netbox_device_type" "fortiswitch" {
  model           = "FortiSwitch"
  manufacturer_id = netbox_manufacturer.fortinet.id
}

resource "netbox_device_type" "fortiap" {
  model           = "FortiAP"
  manufacturer_id = netbox_manufacturer.fortinet.id
}

# Define the site
resource "netbox_site" "new_site" {
  name        = var.site_name
  slug        = lower(replace(var.site_name, " ", "-"))
  status      = "active"
  description = "New site added via Terraform"
}

# Add the firewall
resource "netbox_device" "firewall" {
  name            = "firewall-${var.site_name}"
  site_id         = netbox_site.new_site.id
  role_id         = netbox_device_role.firewall_role.id
  device_type_id  = netbox_device_type.fortigate.id
  status          = "active"
}

# Create an interface for the firewall
resource "netbox_device_interface" "firewall_interface" {
  name      = "eth0"
  device_id = netbox_device.firewall.id
  type      = "1000base-t"
  enabled   = true
}

# Set primary IP for firewall
resource "netbox_device_primary_ip" "firewall_primary" {
  device_id     = netbox_device.firewall.id
  ip_address_id = netbox_ip_address.firewall_ip.id
}

# Assign the firewall IP to the interface
resource "netbox_ip_address" "firewall_ip" {
  ip_address          = local.firewall_ip
  status              = "active"
  description         = "Firewall IP for ${var.site_name}"
  device_interface_id = netbox_device_interface.firewall_interface.id
}

# Add the circuit IP
resource "netbox_ip_address" "circuit_ip" {
  ip_address  = local.circuit_ip
  status      = "active"
  description = "Circuit IP for ${var.site_name}"
}

# Add the gateway IP
resource "netbox_ip_address" "gateway_ip" {
  ip_address  = local.gateway_ip
  status      = "active"
  description = "Gateway IP for ${var.site_name}"
}

locals {
  # Default IPs if not specified
  firewall_ip = coalesce(
    var.firewall_ip != null ? "${trimspace(var.firewall_ip)}/32" : null,
    "${var.network_prefix}.1/32"
  )
  
  circuit_ip = coalesce(
    var.circuit_ip != null ? "${trimspace(var.circuit_ip)}/32" : null,
    "${var.network_prefix}.3/32"
  )
  
  gateway_ip = coalesce(
    var.gateway_ip != null ? "${trimspace(var.gateway_ip)}/32" : null,
    "${var.network_prefix}.254/32"
  )

  # Generate switch names and IPs with custom IP allocation
  switches = {
    for i in range(var.switch_range.start, var.switch_range.end + 1) :
    format("%s-%02d", var.switch_name_prefix, i) => format("%s.%d/32", var.network_prefix, 
      # Start switches at .4 (skipping .1, .2, .3 for firewall, circuit)
      # Skip .9 and .10
      i < 6 ? (i + 3) : (i + 5)
    )
  }
}

# Use local.switches instead of var.switches in resources
resource "netbox_device" "switches" {
  for_each       = local.switches
  name           = each.key
  site_id        = netbox_site.new_site.id
  role_id        = netbox_device_role.switch_role.id
  device_type_id = netbox_device_type.fortiswitch.id
  status         = "active"
}

# Create interfaces for switches
resource "netbox_device_interface" "switch_interfaces" {
  for_each  = local.switches
  name      = "eth0"
  device_id = netbox_device.switches[each.key].id
  type      = "1000base-t"
  enabled   = true
}

# Set primary IPs for switches
resource "netbox_device_primary_ip" "switch_primary_ips" {
  for_each      = local.switches
  device_id     = netbox_device.switches[each.key].id
  ip_address_id = netbox_ip_address.switch_ips[each.key].id
}

# Assign switch IPs to interfaces
resource "netbox_ip_address" "switch_ips" {
  for_each     = local.switches
  ip_address   = each.value
  status       = "active"
  description  = "IP address for ${each.key}"
  interface_id = netbox_device_interface.switch_interfaces[each.key].id
  object_type  = "dcim.interface"
}

# Add Zabbix host for firewall
resource "zabbix_host" "firewall" {
  host = netbox_device.firewall.name
  name = netbox_device.firewall.name
  
  interface {
    type = "snmp"  # Changed from numeric to string
    ip   = trimsuffix(local.firewall_ip, "/32")
    main = true
    port = 161
  }

  groups    = ["2"]  # Must be numeric string ID of the group
  templates = [var.zabbix_template_id]
  
  macro {
    name  = "{$SNMP_COMMUNITY}"
    value = var.snmp_community
  }
}

# Add Zabbix hosts for switches
resource "zabbix_host" "switches" {
  for_each = local.switches
  
  host = each.key
  name = each.key
  
  interface {
    type = "snmp"  # Changed from numeric to string
    ip   = trimsuffix(each.value, "/32")
    main = true
    port = 161
  }

  groups = ["2"]  # Must be numeric string ID of the group
  
  macro {
    name  = "{$SNMP_COMMUNITY}"
    value = var.snmp_community
  }
}