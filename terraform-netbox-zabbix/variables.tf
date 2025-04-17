#######################
# variables.tf
#######################
# Site-specific variables
variable "site_name" {
  description = "The name of the new site"
  type        = string
}

variable "network_prefix" {
  type    = string
  default = "10.168.1"
}

variable "firewall_ip" {
  description = "The IP address for the firewall"
  type        = string
  default     = null
}

variable "circuit_ip" {
  description = "The IP address for the circuit"
  type        = string
  default     = null
}

variable "gateway_ip" {
  description = "The gateway IP address for the site"
  type        = string
  default     = null
}

variable "switch_range" {
  type = object({
    start = number
    end   = number
  })
}

# NetBox variables
variable "netbox_api_token" {
  description = "API token for NetBox"
  type        = string
  sensitive   = true
}

variable "netbox_url" {
  description = "URL for NetBox API"
  type        = string
  default     = "http://127.0.0.1:8000"
}

# Zabbix variables
variable "zabbix_username" {
  description = "Username for Zabbix API"
  type        = string
  sensitive   = true
}

variable "zabbix_password" {
  description = "Password for Zabbix API"
  type        = string
  sensitive   = true
}

variable "zabbix_url" {
  description = "URL for Zabbix API"
  type        = string
}

variable "zabbix_host_group" {
  description = "Zabbix host group for the devices"
  type        = string
}

variable "snmp_community" {
  description = "SNMP community string for firewall monitoring"
  type        = string
  sensitive   = true
}

variable "zabbix_template_id" {
  description = "Zabbix template ID to use"
  type        = string
  default     = "10604"
}

variable "switch_ip_start" {
  type        = string
  default     = "10"  # Switches will use IPs 10-30
  description = "Last octet where switch IPs start"
}

# Add this variable
variable "switch_name_prefix" {
  description = "Prefix for switch names (e.g., 'ILDOC-SW' will create ILDOC-SW-01)"
  type        = string
  default     = "switch"  # Default to maintain backward compatibility
}