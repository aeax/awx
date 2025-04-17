# Configure SNMPv3 users on FortiGate firewalls
terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

# Load the YAML file containing SNMPv3 credentials
locals {
  snmpv3_yaml = yamldecode(file("${path.module}/snmpv3_credentials.yml"))
  snmpv3_users = local.snmpv3_yaml.snmpv3_credentials

  # Read inventory.ini and parse it
  inventory = [
    for line in compact(split("\n", file("${path.module}/inventory.ini"))) :
    line
    if length(regexall("^#", line)) == 0 && length(regexall("^\\[|^$|ansible", line)) == 0
  ]
}

resource "null_resource" "snmpv3_config" {
  for_each = {
    for idx, user in local.snmpv3_users : "${user.username}" => user
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Starting SNMP configuration..."
      sshpass -p '${var.firewall_password}' ssh -o StrictHostKeyChecking=no ${var.firewall_username}@${local.inventory[0]} '
      config global
      config system snmp sysinfo
      set status enable
      end
      
      config system snmp user
      edit "${each.value.username}"
      set status enable
      set trap-status enable
      set trap-lport 162
      set trap-rport 162
      set queries enable
      set query-port 161
      set notify-hosts 172.20.27.91
      set security-level auth-priv
      set auth-proto ${each.value.auth_protocol}
      set auth-pwd "${each.value.auth_password}"
      set priv-proto ${each.value.priv_protocol}
      set priv-pwd "${each.value.priv_password}"
      next
      end
      end
      
      # Verify configuration
      config global
      config system snmp user
      show
      end
      end
      ' 2>&1 | tee snmp_config.log
      echo "Configuration attempt completed. Check snmp_config.log for details."
    EOT
  }
}

resource "null_resource" "snmp_sysinfo" {
  provisioner "local-exec" {
    command = <<-EOT
      sshpass -p '${var.firewall_password}' ssh -o StrictHostKeyChecking=no ${var.firewall_username}@${local.inventory[0]} '
      config global
      config system snmp sysinfo
      set status enable
      set description "FortiGate SNMP"
      end
      end
      '
    EOT
  }
}

# Variables file reference
variable "firewall_username" {
  description = "Username for firewall authentication"
  type        = string
}

variable "firewall_password" {
  description = "Password for firewall authentication"
  type        = string
  sensitive   = true
} 