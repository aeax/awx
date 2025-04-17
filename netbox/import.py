import pynetbox
import re
from slugify import slugify
import os
from ipaddress import ip_network, IPv4Address

# Initialize Netbox API
nb_url = 'http://0.0.0.0:8000/'
nb_token = 'c8f3f3e9343120e9b60c61258b73e8df367dca00'
nb = pynetbox.api(nb_url, token=nb_token)

# Site information
site_name = "Riverside County"

def get_or_create_site(name):
    """Get or create site with proper error handling"""
    site = nb.dcim.sites.get(name=name)
    if not site:
        try:
            site = nb.dcim.sites.create(
                name=name,
                slug=slugify(name),
                status='active'
            )
            print(f"Created site: {name}")
        except Exception as e:
            print(f"Error creating site {name}: {str(e)}")
            return None
    return site

site = get_or_create_site(site_name)

# Expanded device role mappings
device_roles = {
    'Firewall': 'Firewall',
    'Switch': 'Switch',
    'Gateway': 'Gateway',
    'UPS': 'UPS',
    'Server': 'Server',
    'Router': 'Router',
    'VideoSw': 'Switch',
    'ISPRtr': 'Router',
    'VideoServer': 'Server',
    'VisitationServer': 'Server'
}

# Expanded manufacturer mappings
manufacturers = {
    'FortiGate': 'Fortinet',
    'NV': 'ADTRAN',
    'NetVanta': 'ADTRAN',
    'Generic': 'Generic',
    'APC': 'APC',
    'Adtran': 'ADTRAN',
    'SRX': 'Juniper',
    'FortiSwitch': 'Fortinet'
}

# Device type mappings
device_types = {
    'Firewall': ('FortiGate', 'Fortinet'),
    'Switch': ('Generic Switch', 'Generic'),
    'Gateway': ('Generic Gateway', 'Generic'),
    'Server': ('Generic Server', 'Generic'),
    'UPS': ('Generic UPS', 'Generic'),
    'Router': ('Generic Router', 'Generic'),
    'VideoSw': ('Generic Switch', 'Generic')
}

def parse_hostname(hostname):
    """Parse device name and interface from Nagios hostname."""
    try:
        parts = hostname.split('.')
        if len(parts) < 3:
            return hostname, None
            
        device_part = parts[2]
        interface = None
        
        if '-' in device_part:
            device_name, interface = device_part.split('-', 1)
            interface = interface.replace('_', '/').lower()
        else:
            device_name = device_part
            
        return device_name, interface
        
    except Exception as e:
        print(f"Error parsing hostname {hostname}: {str(e)}")
        return hostname, None

def get_or_create_manufacturer(name):
    """Get or create manufacturer with proper error handling"""
    if not name:
        return None
        
    manufacturer = nb.dcim.manufacturers.get(name=name)
    if not manufacturer:
        try:
            manufacturer = nb.dcim.manufacturers.create(
                name=name,
                slug=slugify(name)
            )
            print(f"Created manufacturer: {name}")
        except Exception as e:
            print(f"Error creating manufacturer {name}: {str(e)}")
            return None
    return manufacturer

def get_or_create_device_type(name, manufacturer):
    """Fixed device type creation with proper RecordSet handling"""
    manufacturer_obj = get_or_create_manufacturer(manufacturer)
    if not manufacturer_obj:
        return None

    # Convert RecordSet to list
    existing = list(nb.dcim.device_types.filter(model=name, manufacturer_id=manufacturer_obj.id))
    if existing:
        return existing[0]

    try:
        device_type = nb.dcim.device_types.create(
            model=name,
            manufacturer=manufacturer_obj.id,
            slug=slugify(f"{manufacturer}-{name}"),
            u_height=1
        )
        print(f"Created device type: {manufacturer} {name}")
        return device_type
    except Exception as e:
        print(f"Error creating device type {name}: {str(e)}")
        return None

def get_or_create_device_role(name):
    """Get or create device role with proper error handling"""
    if not name:
        return None
        
    # Try to get existing role first
    role = nb.dcim.device_roles.get(name=name)
    if role:
        return role
        
    # Try to get by slug if name lookup fails
    role = nb.dcim.device_roles.get(slug=slugify(name))
    if role:
        return role
        
    # Create new role if it doesn't exist
    try:
        role = nb.dcim.device_roles.create(
            name=name,
            slug=slugify(name),
            color="ff0000"
        )
        print(f"Created device role: {name}")
    except Exception as e:
        # If creation fails, try one more time to get existing role
        role = nb.dcim.device_roles.get(slug=slugify(name))
        if role:
            return role
        print(f"Error creating device role {name}: {str(e)}")
        return None
        
    return role

# Expanded device type mappings with model detection
def get_model_from_alias(alias):
    """Extract model information from device alias"""
    if not alias:
        return None
        
    # Common model patterns
    model_patterns = {
        r'NV\s*(\d{4})': ('ADTRAN', 'NetVanta {}'),
        r'NetVanta\s*(\d{4})': ('ADTRAN', 'NetVanta {}'),
        r'FortiGate\s*(\d+\w?)': ('Fortinet', 'FortiGate {}'),
        r'FortiSwitch\s*(\d+\w?)': ('Fortinet', 'FortiSwitch {}'),
        r'SRX\s*(\d+)': ('Juniper', 'SRX {}'),
        r'APC\s*UPS': ('APC', 'Smart-UPS')
    }
    
    # Check for exact matches first
    alias_lower = alias.lower()
    if 'netvanta switch' in alias_lower:
        return ('ADTRAN', 'NetVanta 1534')  # Default model for Netvanta switches
    if 'srx firewall' in alias_lower:
        return ('Juniper', 'SRX 300')  # Default model for SRX firewalls
    
    # Then check regex patterns
    for pattern, (mfg, model_fmt) in model_patterns.items():
        match = re.search(pattern, alias, re.IGNORECASE)
        if match:
            model = model_fmt.format(match.group(1))
            return mfg, model
            
    return None

def get_device_type_and_role(hostname, alias):
    """Enhanced device type and role detection"""
    device_type = ('Generic Device', 'Generic')
    role_name = 'Unknown'
    
    # First check alias for model info
    model_info = get_model_from_alias(alias)
    if model_info:
        device_type = (model_info[1], model_info[0])
    
    # Determine role from hostname and alias
    hostname_lower = hostname.lower()
    alias_lower = alias.lower() if alias else ''
    
    role_patterns = {
        'firewall': ('fw', 'firewall', 'fwl'),
        'switch': ('sw', 'switch'),
        'gateway': ('gwy', 'gateway'),
        'router': ('rtr', 'router', 'modem'),  # Added 'modem'
        'ups': ('ups',),
        'server': ('server', 'srv', '41', '42', '43'),
        'visitation': ('visit',)
    }
    
    for role, patterns in role_patterns.items():
        if any(p in hostname_lower or (alias_lower and p in alias_lower) for p in patterns):
            role_name = role.title()
            if not model_info:
                if 'netvanta' in alias_lower:
                    device_type = ('NetVanta 1534', 'ADTRAN')
                elif 'srx' in alias_lower:
                    device_type = ('SRX 300', 'Juniper')
                else:
                    device_type = device_types.get(role_name, ('Generic Device', 'Generic'))
            break
    
    return device_type, role_name

def process_host(host):
    """Fixed process_host with proper interface handling"""
    try:
        if not site:
            print(f"Error: Site '{site_name}' not found")
            return

        hostname = host['host_name']
        alias = host.get('alias', '')
        raw_ip = host['address'].strip()
        
        print(f"\nProcessing host: {hostname}")

        # Validate IP without subnet first
        try:
            # Validate just the IP portion
            IPv4Address(raw_ip)
            # If valid, add the /28 subnet
            ip_addr = f"{raw_ip}/28" if '/' not in raw_ip else raw_ip
        except ValueError:
            print(f"Invalid IP: {raw_ip}")
            return

        device_name, interface = parse_hostname(hostname)
        if not device_name:
            print(f"Couldn't parse device name from {hostname}")
            return

        if 'FW' in hostname.upper() or 'firewall' in alias.lower():
            device_type_info = device_types['Firewall']
            role_name = 'Firewall'
        else:
            device_type_info, role_name = get_device_type_and_role(hostname, alias)

        device_type_name, manufacturer_name = device_type_info

        device_type = get_or_create_device_type(device_type_name, manufacturer_name)
        if not device_type:
            return
            
        device_role = get_or_create_device_role(role_name)
        if not device_role:
            return

        # Get or create device with error handling
        try:
            device = nb.dcim.devices.get(name=device_name)
            if not device:
                device = nb.dcim.devices.create(
                    name=device_name,
                    device_type=device_type.id,
                    role=device_role.id,
                    site=site.id,
                    status='active'
                )
                print(f"Created device: {device_name}")
        except Exception as e:
            print(f"Device creation error: {str(e)}")
            return

        # Interface handling with explicit list conversion
        iface = None
        if interface:
            interfaces = list(nb.dcim.interfaces.filter(device_id=device.id, name=interface))
            if interfaces:
                iface = interfaces[0]
            else:
                try:
                    iface = nb.dcim.interfaces.create(
                        device=device.id,
                        name=interface,
                        type='1000base-t'
                    )
                    print(f"Created interface {interface} on {device_name}")
                except Exception as e:
                    print(f"Interface creation error: {str(e)}")
        else:
            interfaces = list(nb.dcim.interfaces.filter(device_id=device.id))
            if interfaces:
                iface = interfaces[0]
            else:
                try:
                    iface = nb.dcim.interfaces.create(
                        device=device.id,
                        name='eth0',
                        type='1000base-t'
                    )
                    print(f"Created default interface on {device_name}")
                except Exception as e:
                    print(f"Default interface error: {str(e)}")
                    return

        if not iface:
            print(f"No interface available for {device_name}")
            return

        # IP address handling with explicit checks
        try:
            # First try to get the IP by exact address
            ip = nb.ipam.ip_addresses.get(address=ip_addr)
            if not ip:
                # If not found with /28, try with /32 (common duplicate case)
                base_ip = ip_addr.split('/')[0]
                ip = nb.ipam.ip_addresses.get(address=f"{base_ip}/32")
            
            if ip:
                # IP exists, update its assignment
                if not ip.assigned_object or ip.assigned_object.id != iface.id:
                    ip.assigned_object_type = 'dcim.interface'
                    ip.assigned_object_id = iface.id
                    ip.save()
                    print(f"Updated IP assignment for {ip.address}")
            else:
                # IP doesn't exist, create new
                try:
                    ip = nb.ipam.ip_addresses.create(
                        address=ip_addr,
                        assigned_object_type='dcim.interface',
                        assigned_object_id=iface.id
                    )
                    print(f"Created IP {ip_addr} for {device_name}")
                except Exception as e:
                    if 'Duplicate IP address found' in str(e):
                        # One more try to get the IP if it was created in parallel
                        ip = nb.ipam.ip_addresses.get(address=ip_addr)
                        if ip:
                            ip.assigned_object_type = 'dcim.interface'
                            ip.assigned_object_id = iface.id
                            ip.save()
                            print(f"Updated IP assignment for {ip.address}")
                        else:
                            raise

            # Set primary IPv4 for management
            if ip:
                device.primary_ip4 = ip.id
                device.save()
                print(f"Set primary IPv4 {ip.address} for {device_name}")

        except Exception as e:
            print(f"IP handling error: {str(e)}")

    except Exception as e:
        print(f"Critical error processing {hostname}: {str(e)}")

def parse_nagios_config(file_path):
    """Parse Nagios configuration file"""
    hosts = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        host_blocks = re.findall(r'define host\s*{([^}]+)}', content)
        
        for block in host_blocks:
            host = {}
            for line in block.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        host[key.strip()] = value.strip()
            
            if 'host_name' in host and 'address' in host:
                hosts.append(host)
                
        return hosts
        
    except Exception as e:
        print(f"Config parsing error: {str(e)}")
        return []

def parse_site_name(hostname):
    """Extract and format site name from hostname"""
    # Split on first dot to get site portion
    site_part = hostname.split('.')[0]
    
    # Common replacements
    replacements = {
        'Co': 'County',
        'Jail': '',
        'DC': '',
        'CI': '',
        'CoJail': 'County',
        'CoJailOH': 'County',
        'CoJailPA': 'County',
        'CoCA': 'County',
        'CoMD': 'County',
        'CoMO': 'County',
        'CoNC': 'County',
        'CoOR': 'County',
        'CoTX': 'County',
        'CoUT': 'County',
        'CoVA': 'County',
        'CoWA': 'County'
    }
    
    # Replace common abbreviations
    name_parts = []
    current_part = ''
    
    # Split into parts while preserving camel case
    for char in site_part:
        if char.isupper() and current_part:
            name_parts.append(current_part)
            current_part = char
        else:
            current_part += char
    if current_part:
        name_parts.append(current_part)
    
    # Process each part
    processed_parts = []
    i = 0
    while i < len(name_parts):
        combined = ''.join(name_parts[i:i+2]) if i+1 < len(name_parts) else name_parts[i]
        if combined in replacements:
            processed_parts.append(replacements[combined])
            i += 2
        else:
            processed_parts.append(replacements.get(name_parts[i], name_parts[i]))
            i += 1
    
    # Join parts and clean up
    site_name = ' '.join(processed_parts).strip()
    return site_name

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hosts_dir = os.path.join(script_dir, "hosts")
    
    try:
        # Get all .cfg files
        cfg_files = [f for f in os.listdir(hosts_dir) if f.endswith('.cfg')]
        print(f"Found {len(cfg_files)} configuration files")
        
        for cfg_file in sorted(cfg_files):
            config_file = os.path.join(hosts_dir, cfg_file)
            print(f"\nProcessing file: {cfg_file}")
            
            # Parse hosts from the current file
            hosts = parse_nagios_config(config_file)
            if not hosts:
                print("No valid hosts found")
                continue
            
            # Group hosts by site
            sites = {}
            for host in hosts:
                hostname = host['host_name']
                site_name = parse_site_name(hostname)
                if site_name not in sites:
                    sites[site_name] = []
                sites[site_name].append(host)
            
            # Process each site
            for site_name, site_hosts in sites.items():
                print(f"\nProcessing site: {site_name}")
                global site
                site = get_or_create_site(site_name)
                
                if not site:
                    print(f"Failed to create/get site {site_name}, skipping hosts")
                    continue
                
                print(f"Processing {len(site_hosts)} hosts for {site_name}")
                for index, host in enumerate(site_hosts, 1):
                    print(f"\nProcessing host {index}/{len(site_hosts)}")
                    process_host(host)
            
        print("\nImport completed successfully!")
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main()