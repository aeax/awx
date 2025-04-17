# Network Automation Tools

This directory contains automation tools for managing network monitoring and configuration.

## Directory Structure

- `librenms/` - Tools for LibreNMS monitoring system
  - `import/` - Scripts for importing existing configurations
  - `terraform/` - Infrastructure as Code for LibreNMS management

## Quick Start

1. For importing existing Nagios configs to LibreNMS:
   ```bash
   cd librenms/import
   python3 checkmk.py
   ```

2. For managing sites with Terraform:
   ```bash
   cd librenms/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your settings
   terraform init
   terraform plan
   terraform apply
   ``` 