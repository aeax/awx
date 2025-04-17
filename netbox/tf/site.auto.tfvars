#This will automatically create on Netbox & Zabbix
site_name      = "ILDOC Testing"
network_prefix = "17.30.21"


firewall_ip = "30.20.10.9"
circuit_ip  = "30.20.10.8"
gateway_ip  = "30.20.10.7"

# Switch configuration
# Start and end implies the total number of switches, it will automatically skip .9, and .10.
# The switch name will be in the format of ILDOC-SW01, ILDOC-SW02, etc.
switch_name_prefix = "TEST-SCRIPT"
switch_range = {
  start = 1
  end   = 10
}
