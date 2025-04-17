terraform {
  required_providers {
    netbox = {
      source  = "e-breuninger/netbox"
      version = "3.10.0"
    }
    zabbix = {
      source  = "tpretz/zabbix"
      version = "0.17.0"
    }
  }
}

provider "netbox" {
  server_url = var.netbox_url
  api_token  = var.netbox_api_token
}

provider "zabbix" {
  url      = var.zabbix_url
  username = var.zabbix_username
  password = var.zabbix_password
  # Add this if you need to skip TLS verification
  # tls_insecure = true
}

