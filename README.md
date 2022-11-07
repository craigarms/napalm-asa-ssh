# NAPALM Cisco ASA SSH

It's a NAPALM Community Driver for Cisco ASA Firewalls using SSH, for ASAv and versions not able to use the REST API

## Supported Cisco ASA

This Driver has been tested against the following devices/versions

* Cisco ASA
	* 9.2(2)4
	
## Instructions

The driver is under development and iteration.

### Get info
| API   | Description  |
|--------|-----|
|  get_facts()                |  Return general device information |
|  get_config()               |  Read config |
|  get_arp_table()            |  Get device ARP table |

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


```