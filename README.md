# NAPALM Cisco ASA SSH

It's a NAPALM Community Driver for Cisco ASA Firewalls using SSH, for ASAv and versions not able to use the REST API

[![Pytest](https://github.com/craigarms/napalm-asa-ssh/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/craigarms/napalm-asa-ssh/actions/workflows/python-app.yml)

## Supported Cisco ASA

This Driver has been tested against the following devices/versions

* Cisco ASA
	* 9.2(2)4
	
## Instructions

The driver is under development and iteration.

## Quick start

```python
from napalm import get_network_driver
driver = get_network_driver('asa_ssh')
device = driver(hostname='192.168.76.10', username='admin', password='this_is_not_a_secure_password')
device.open()

# Send Any CLI command
send_command = device.cli(['show version'])

#  Return general device information
get_facts = device.get_facts()
print(get_facts)

# other API
device.get_config()
device.get_arp_table()
device.get_interfaces()
device.get_interfaces_ip()
```

### Get info
| API                 | Description                       |
|---------------------|-----------------------------------|
| get_facts()         | Return general device information |
| get_config()        | Read config                       |
| get_arp_table()     | Get device ARP table              |
| get_intefaces()     | Get device Interfaces             |
| get_interfaces_ip() | Get device Interfaces IP           |

### Config

| API   | Description  |
|--------|-----|
|  cli()                      |  Send any cli commands  |

### Other tools
| API   | Description  |
|--------|-----|
|  is_active()                |  get devices active status  |
|  ping()                     |  Ping remote ip  |


## How to Install

TODO: When I figure out how to get onto PyPi


## Supported Getters

Getter order is sort of a priority list to support

| Getter                    | Support  |
|---------------------------|----------|
| get_facts                 |  ✅      |
| is_alive                  |  ✅      |
| ping                      |  ✅      |
| get_config                |  ✅      |
| get_arp_table             |  ✅      |
| get_interfaces            |  ✅      |
| get_interfaces_ip         |  ✅      |
| get_interfaces_counters   |  ❌      |
| get_environment           |  ❌      |
| traceroute                |  ❌      |
| get_route_to              |  ❌      |
| get_firewall_policies     |  ❌      |
| get_mac_address_table     |  ❌      |
| get_snmp_information      |  ❌      |
| get_users                 |  ❌      |
| get_bgp_config            |  ❌      |
| get_bgp_neighbors         |  ❌      |
| get_bgp_neighbors_detail  |  ❌      |
| get_ipv6_neighbors_table  |  ❌      |
| get_network_instances     |  ❌      |
| get_ntp_peers             |  ❌      |
| get_ntp_servers           |  ❌      |
| get_ntp_stats             |  ❌      |
| get_optics                |  ❌      |
| get_probes_config         |  ❌      |
| get_probes_results        |  ❌      |
| get_lldp_neighbors        |  ❌      |
| get_lldp_neighbors_detail |  ❌      |
