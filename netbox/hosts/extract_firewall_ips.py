#!/usr/bin/env python3
"""
Script to extract IP addresses from Nagios hosts that have 'Firewall' or 'FW' in their alias.
Simplifies host names and outputs only host name and IP address.
"""

import os
import re
import argparse
import csv
from pathlib import Path


def simplify_hostname(hostname):
    """
    Simplify complex hostnames to more readable names.
    
    Args:
        hostname (str): Original hostname
        
    Returns:
        str: Simplified hostname
    """
    # Remove common suffixes and prefixes
    simplified = re.sub(r'\..*$', '', hostname)  # Remove domain parts
    simplified = re.sub(r'[_\-.]', ' ', simplified)  # Replace separators with spaces
    
    # Handle specific patterns like "MontgomeryCoJail.b.MCJALFw" -> "Montgomery County"
    if 'co' in simplified.lower():
        # Extract county name
        match = re.match(r'([A-Za-z]+)Co', simplified, re.IGNORECASE)
        if match:
            county_name = match.group(1)
            return f"{county_name} County"
    
    # Handle common abbreviations (add more as needed)
    common_abbrevs = ['DOC', 'IL', 'FW', 'PD', 'SD', 'HQ', 'CTY', 'CO', 'ISP', 'WI']
    common_abbrevs_lower = [abbr.lower() for abbr in common_abbrevs]
    
    # Process each part (word) in the hostname
    result_parts = []
    for part in simplified.split():
        part_lower = part.lower()
        
        # Check if the entire word is made up of abbreviations
        current_pos = 0
        found_abbrevs = []
        remaining = part_lower
        
        # Try to find all abbreviations within the word
        while remaining and current_pos < len(part_lower):
            found = False
            for i, abbrev in enumerate(common_abbrevs_lower):
                if remaining.startswith(abbrev):
                    found_abbrevs.append(common_abbrevs[i])  # Use the uppercase version
                    current_pos += len(abbrev)
                    remaining = part_lower[current_pos:]
                    found = True
                    break
            if not found:
                break
        
        # If the entire word was made up of abbreviations, join them together
        if found_abbrevs and current_pos == len(part_lower):
            result_parts.append(''.join(found_abbrevs))
        else:
            result_parts.append(part.capitalize())
    
    return ' '.join(result_parts)


def parse_nagios_config(config_dir):
    """
    Parse Nagios host configuration files to extract hosts with firewall-related aliases.
    
    Args:
        config_dir (str): Path to the Nagios configuration directory
        
    Returns:
        list: List of dictionaries containing host information (hostname, ip)
    """
    firewall_hosts = []
    
    # Walk through all files in the config directory
    for root, _, files in os.walk(config_dir):
        for file in files:
            if file.endswith(('.cfg', '.conf')):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                        # Find all host definitions
                        host_blocks = re.findall(r'define\s+host\s*{[^}]+}', content, re.DOTALL)
                        
                        for block in host_blocks:
                            # Extract hostname, alias, and address
                            hostname = re.search(r'host_name\s+([^\s;#]+)', block)
                            alias = re.search(r'alias\s+([^;#\n]+)', block)
                            address = re.search(r'address\s+([^\s;#]+)', block)
                            
                            if hostname and alias and address:
                                hostname = hostname.group(1).strip()
                                alias = alias.group(1).strip()
                                address = address.group(1).strip()
                                
                                # Check if alias contains 'firewall' or 'fw' (case insensitive)
                                if re.search(r'firewall|fw', alias, re.IGNORECASE):
                                    # Simplify the hostname
                                    simple_name = simplify_hostname(hostname)
                                    
                                    firewall_hosts.append({
                                        'hostname': simple_name,
                                        'ip': address
                                    })
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
    
    return firewall_hosts


def export_to_csv(hosts, output_file):
    """
    Export the list of firewall hosts to a CSV file.
    
    Args:
        hosts (list): List of host dictionaries
        output_file (str): Path to the output CSV file
    """
    if not hosts:
        print("No firewall hosts found.")
        return
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['hostname', 'ip']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for host in hosts:
            writer.writerow(host)
    
    print(f"Exported {len(hosts)} firewall hosts to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Extract firewall IPs from Nagios configuration.')
    parser.add_argument('--config-dir', '-c', required=True, help='Path to Nagios configuration directory')
    parser.add_argument('--output', '-o', default='firewall_ips.csv', help='Output CSV file (default: firewall_ips.csv)')
    parser.add_argument('--list', '-l', action='store_true', help='List results to console')
    
    args = parser.parse_args()
    
    # Validate config directory
    if not os.path.isdir(args.config_dir):
        print(f"Error: {args.config_dir} is not a valid directory")
        return
    
    # Parse Nagios configuration
    print(f"Searching for firewall hosts in {args.config_dir}...")
    firewall_hosts = parse_nagios_config(args.config_dir)
    
    # Display results
    if args.list:
        print("\nFirewall Hosts Found:")
        print("-" * 50)
        for host in firewall_hosts:
            print(f"Hostname: {host['hostname']}")
            print(f"IP: {host['ip']}")
            print("-" * 50)
    
    # Export to CSV
    export_to_csv(firewall_hosts, args.output)
    
    print(f"Found {len(firewall_hosts)} firewall hosts.")


if __name__ == "__main__":
    main() 