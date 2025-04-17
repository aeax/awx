#!/usr/bin/env python3
import re
import os
import time
import json
import requests

# LibreNMS API Configuration
HOST_NAME = "172.20.27.91"
PROTO = "http"
API_URL = f"{PROTO}://{HOST_NAME}/api/v0"

# LibreNMS API Token
API_TOKEN = "ad9daeaf543f9699d4d689c477c26114"

# Nagios Config Directory Path
NAGIOS_CFG_DIR = "/Users/chris/Desktop/Networking/netbox/hosts/"

def sanitize_name(name):
    """Sanitize name to comply with LibreNMS naming rules."""
    # Replace forward slashes with underscores
    name = name.replace('/', '_')
    # Replace any other invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '_', name)
    return sanitized

def extract_facility_name(hostname, filename, host_alias=None):
    """Extract facility name from hostname or filename."""
    # Special handling for known multi-site files
    if filename == "ILDOC.cfg":
        # Try to extract facility name from hostname or alias
        for pattern in [
            r"ILDOC-([A-Za-z]+)",  # Match ILDOC-FacilityName
            r"IL-([A-Za-z]+)",     # Match IL-FacilityName
            r"([A-Za-z]+)CC\.",    # Match FacilityCC.
            r"([A-Za-z]+)CF\."     # Match FacilityCF.
        ]:
            match = re.search(pattern, hostname)
            if match:
                return f"ILDOC_{match.group(1)}"
        
        # If no match in hostname, try alias
        if host_alias:
            # Look for facility name in alias
            facility_names = [
                "Centralia", "Menard", "Pontiac", "Stateville",
                "Big Muddy", "Dixon", "Graham", "Hill", "Lawrence",
                "Lincoln", "Logan", "Pinckneyville", "Robinson",
                "Shawnee", "Sheridan", "Vandalia", "Vienna",
                "Western Illinois"
            ]
            for facility in facility_names:
                if facility.lower() in host_alias.lower():
                    return f"ILDOC_{facility.replace(' ', '_')}"
    
    # Add similar handling for other known multi-site files
    if filename == "KSDOC.cfg":
        # Extract facility name from hostname or alias
        for pattern in [
            r"KSDOC-([A-Za-z]+)",
            r"KS-([A-Za-z]+)"
        ]:
            match = re.search(pattern, hostname)
            if match:
                return f"KSDOC_{match.group(1)}"
    
    if filename == "WIDOC-CTL.cfg":
        # Extract facility name from hostname or alias
        for pattern in [
            r"WIDOC-([A-Za-z]+)",
            r"WI-([A-Za-z]+)"
        ]:
            match = re.search(pattern, hostname)
            if match:
                return f"WIDOC_{match.group(1)}"
    
    # Default handling for single-site files
    facility = os.path.splitext(filename)[0]
    facility = re.sub(r'([a-z])([A-Z])', r'\1 \2', facility)
    facility = facility.replace('_', ' ')
    
    return sanitize_name(facility)

def parse_nagios_cfg(file_path, filename):
    """Parse Nagios config file to extract host details with facility grouping."""
    hosts = []
    try:
        with open(file_path, "r") as file:
            data = file.read()
            
        # Look for facility sections in the file
        sections = re.split(r'#+\s*([A-Za-z\s]+)\s*#+', data)
        if len(sections) > 1:
            print(f"  Found multiple sections in {filename}:")
            for i in range(1, len(sections), 2):
                print(f"    - {sections[i].strip()}")
        
        # Find all host definition blocks (including commented ones)
        all_blocks = re.finditer(r'(?:^|\n)(\s*#*\s*)(define host\s*{.*?})', data, re.DOTALL)
        
        for block in all_blocks:
            comment_prefix = block.group(1).strip()
            host_def = block.group(2)
            
            # Skip if the host definition is commented out
            if comment_prefix.startswith('#'):
                continue
            
            # Parse the active host definition
            host_name = re.search(r"host_name\s+(\S+)", host_def)
            address = re.search(r"address\s+(\S+)", host_def)
            alias = re.search(r"alias\s+(.+?)(?:\n|$)", host_def)
            hostgroups = re.search(r"hostgroups\s+(.+?)(?:\n|$)", host_def)

            if host_name and address:
                ip_address = address.group(1).strip()
                hostname = host_name.group(1).strip()
                alias_text = alias.group(1).strip() if alias else hostname
                
                # Extract facility name using both hostname and alias
                facility = extract_facility_name(hostname, filename, alias_text)
                
                # Extract groups if available
                groups = []
                if hostgroups:
                    groups = [g.strip() for g in hostgroups.group(1).split(',')]
                
                hosts.append({
                    'hostname': sanitize_name(hostname),
                    'original_hostname': hostname,
                    'ip': ip_address,
                    'alias': alias_text,
                    'facility': facility,
                    'groups': groups
                })
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return hosts

def create_librenms_session():
    """Create and return a session for LibreNMS API."""
    session = requests.session()
    session.headers['X-Auth-Token'] = API_TOKEN
    session.headers['Accept'] = 'application/json'
    return session

def get_existing_devices(session):
    """Get list of existing devices from LibreNMS."""
    try:
        resp = session.get(f"{API_URL}/devices")
        if resp.status_code == 200:
            devices = resp.json()['devices']
            return {device['hostname'] for device in devices}
        return set()
    except Exception as e:
        print(f"Error getting existing devices: {str(e)}")
        return set()

def add_devices_to_librenms(session, hosts_by_facility):
    """Add devices to LibreNMS using API."""
    # Get existing devices first
    existing_devices = get_existing_devices(session)
    print(f"Found {len(existing_devices)} existing devices in LibreNMS")
    
    for facility, hosts in hosts_by_facility.items():
        print(f"\nProcessing facility: {facility} ({len(hosts)} hosts)")
        
        # Filter out existing hosts
        new_hosts = []
        for host in hosts:
            if host['hostname'] in existing_devices:
                print(f"  Skipping existing device: {host['original_hostname']}")
                continue
            new_hosts.append(host)
        
        if not new_hosts:
            print(f"  No new devices to add in {facility}")
            continue
        
        print(f"  Adding {len(new_hosts)} new devices to {facility}")
        
        # Add devices one by one
        for host in new_hosts:
            try:
                # Add device with minimal configuration for ping monitoring
                resp = session.post(
                    f"{API_URL}/devices",
                    json={
                        "hostname": host['ip'],
                        "display": host['original_hostname'],
                        "snmp_disable": True,  # Disable SNMP
                        "force_add": True,
                        "location": facility
                    }
                )
                
                if resp.status_code == 200:
                    print(f"  Successfully added device: {host['original_hostname']}")
                else:
                    print(f"  Error adding device {host['original_hostname']}: {resp.text}")
                
                # Add a small delay between adds
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Error adding device {host['original_hostname']}: {str(e)}")

def main():
    all_hosts = []
    facilities = {}
    
    # Process each Nagios config file
    cfg_files = [f for f in os.listdir(NAGIOS_CFG_DIR) if f.endswith(".cfg")]
    total_files = len(cfg_files)
    print(f"Found {total_files} Nagios config files")
    
    # Process each file
    for idx, filename in enumerate(sorted(cfg_files), 1):
        file_path = os.path.join(NAGIOS_CFG_DIR, filename)
        print(f"Processing file {idx}/{total_files}: {filename}")
        hosts_in_file = parse_nagios_cfg(file_path, filename)
        print(f"  Found {len(hosts_in_file)} valid hosts")
        
        # Group hosts by facility
        for host in hosts_in_file:
            facility = host['facility']
            if facility not in facilities:
                facilities[facility] = []
            facilities[facility].append(host)
        
        all_hosts.extend(hosts_in_file)
    
    print(f"\nTotal valid hosts found: {len(all_hosts)}")
    print(f"Grouped into {len(facilities)} facilities")
    
    # Create API session
    session = create_librenms_session()
    
    # Add devices to LibreNMS by facility
    add_devices_to_librenms(session, facilities)

if __name__ == "__main__":
    main()