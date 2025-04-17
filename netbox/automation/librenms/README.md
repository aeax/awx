# LibreNMS Automation

Tools for managing LibreNMS monitoring system.

## Import Tools

The `import/` directory contains scripts for importing existing configurations:
- `checkmk.py` - Import Nagios/Check_MK configurations into LibreNMS

## Terraform Configuration

The `terraform/` directory contains Infrastructure as Code for managing LibreNMS:
- Site definitions in YAML format
- Modular configuration for easy site additions
- Support for both new and existing sites

### Adding a New Site

1. Edit `terraform/sites/sites.yaml`:
   ```yaml
   NewSite:
     network_prefix: "10.x.y.0/24"
     firewall_ip: "10.x.y.1"
     circuit_ip: "10.x.y.2"
     gateway_ip: "10.x.y.254"
     switch_ips:
       - "10.x.y.10"
       - "10.x.y.11"
   ```

2. Apply changes:
   ```bash
   cd terraform
   terraform plan
   terraform apply
   ``` 