import re
import json
import os
import sys

def parse_config_file(file_path):
    """Parse a config file and extract device information."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Extract region from filename (e.g., "WIDOC" from "WIDOC-CTL.cfg")
        region_match = re.match(r'([A-Za-z]+)', os.path.basename(file_path))
        if region_match:
            region = region_match.group(1)
        else:
            region = os.path.splitext(os.path.basename(file_path))[0]
        
        # Find all host entries
        host_entries = re.finditer(r'host_name\s+([^\n]+)', content)
        
        sites = {}
        device_id = 1
        
        for host_entry in host_entries:
            host_name = host_entry.group(1).strip()
            
            # Extract site name from host_name
            site_match = re.search(r'[^-]+-([^\.]+)', host_name)
            if site_match:
                site_name = site_match.group(1)
                # Handle special cases like "av.WIDOCFW_28" to extract just "Dodge"
                if '.' in site_name:
                    site_name = site_name.split('.')[0]
            else:
                site_name = "Unknown"
            
            # Find IP addresses and aliases near this host entry
            # Look for the position of this host entry in the content
            pos = host_entry.start()
            
            # Search for address entries after this host entry
            address_entries = re.finditer(r'address\s+([0-9\.]+)', content[pos:pos+500])
            alias_entries = re.finditer(r'alias\s+([^\n]+)', content[pos:pos+500])
            
            addresses = [addr.group(1) for addr in address_entries]
            aliases = [alias.group(1).strip() for alias in alias_entries]
            
            # Create devices for each address found
            for i, addr in enumerate(addresses):
                description = aliases[i] if i < len(aliases) else "Unknown"
                device_type = description.split()[0] if description != "Unknown" else "Unknown"
                
                # Only include firewall devices
                if "firewall" in description.lower() or "fw" in description.lower() or "firewall" in device_type.lower():
                    if site_name not in sites:
                        sites[site_name] = []
                    
                    device = {
                        "id": str(device_id),
                        "region": region,
                        "siteName": site_name,
                        "ipAddress": addr,
                        "description": description,
                        "deviceType": "Firewall"  # Set device type explicitly to Firewall
                    }
                    
                    sites[site_name].append(device)
                    device_id += 1
        
        # Convert sites dictionary to the required format
        result = {
            "name": region,
            "sites": [{"name": site, "devices": devices} for site, devices in sites.items()]
        }
        
        return result
    
    except Exception as e:
        print(f"Error parsing {file_path}: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python config_to_json.py <config_file>")
        return
    
    config_file = sys.argv[1]
    if not os.path.exists(config_file):
        print(f"Error: File {config_file} not found")
        return
    
    result = parse_config_file(config_file)
    if result:
        # Create output filename
        output_file = os.path.splitext(config_file)[0] + ".json"
        
        # Write to JSON file
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Successfully converted {config_file} to {output_file}")

if __name__ == "__main__":
    main() 