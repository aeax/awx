# Adtran Dial Plan Configuration Playbook

This Ansible playbook configures the dial plan on Adtran Netvanta 900e devices and serves as an alternative to Adtran N-command.

## Features

- Checks for existing configurations before applying changes
- Removes existing voice trunk configurations (T92, T93, T94) if they exist
- Removes existing voice grouped-trunk configurations (MAIN, SIPEXT) if they exist
- Applies the new dial plan configuration
- Saves the configuration

## Requirements

- Ansible 2.9 or higher
- SSH access to the Adtran devices
- Python netmiko library: `pip install netmiko`

## Setup

1. Edit the `inventory.ini` file to add your Adtran device information:
   ```ini
   [adtran_devices]
   adtran1 ansible_host=192.168.1.1
   adtran2 ansible_host=192.168.1.2
   ```

2. For secure password management, use Ansible Vault:
   ```bash
   ansible-vault create vault.yml
   ```
   Add your credentials in the vault:
   ```yaml
   ansible_password: your_secure_password
   ```

3. Reference the vault in your playbook execution:
   ```bash
   ansible-playbook -i inventory.ini adtran_dial_plan.yml --ask-vault-pass
   ```

## Playbook Options

Two playbook options are available:

1. **adtran_dial_plan.yml**: Uses the Ansible network_cli connection and adtran_config module
2. **adtran_dial_plan_raw.yml**: Uses raw SSH commands for devices that might not support network_cli

## Customizing the Dial Plan

If you need to modify the dial plan configuration, edit the playbook files and update the configuration lines in the tasks section.

## Running the Playbook

```bash
ansible-playbook -i inventory.ini adtran_dial_plan.yml
```

If using a vault for credentials:
```bash
ansible-playbook -i inventory.ini adtran_dial_plan.yml --ask-vault-pass
```

If the standard playbook doesn't work with your device, try the raw SSH version:
```bash
ansible-playbook -i inventory.ini adtran_dial_plan_raw.yml
``` 