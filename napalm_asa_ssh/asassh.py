# -*- coding: utf-8 -*-
# Copyright 2016 Dravetech AB. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Napalm driver for AsaSSH.

Read https://napalm.readthedocs.io for more information.
"""

from napalm.base import NetworkDriver, models
from napalm.base.exceptions import (
    ConnectionException,
    SessionLockedException,
    MergeConfigException,
    ReplaceConfigException,
    CommandErrorException,
)
from napalm.base.netmiko_helpers import netmiko_args
from typing import Any, Dict, List, Union
import socket
import re
from napalm.base.exceptions import ConnectionClosedException
from ipaddress import IPv4Address, IPv4Network, ip_address
from napalm_asa_ssh.utils.ttp_templates import AsaTemplates
from netmiko.utilities import get_structured_data


def _parse_interface_speed(speed: str) -> float:
    """
    Parse interface speed from ASA output
    """
    if speed == "auto":
        return 0.0
    elif speed == "10":
        return 10.0
    elif speed == "100":
        return 100.0
    elif speed == "1000":
        return 1000.0
    elif speed == "10000":
        return 10000.0
    elif speed == "40000":
        return 40000.0
    elif speed == "100000":
        return 100000.0
    else:
        return 0.0


def _parse_interface_data(interface: Dict[str, Any]) -> models.InterfaceDict:
    """
    Parse interface data from ASA output
    """
    data = {
        "is_up": interface["line_state"] == "up",
        "is_enabled": interface["admin_state"] == "up",
        "description": interface["if_description"],
        "last_flapped": -1.0,
        "speed": _parse_interface_speed(interface["bandwidth"]),
        "mtu": int(interface["mtu"]),
        "mac_address": interface["mac"],
    }
    return data


class AsaSSHDriver(NetworkDriver):
    platform = "cisco_asa"
    """Napalm driver for AsaSSH."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.vendor = "cisco"
        self.device_type = "cisco_asa"
        self.context = ""

        if optional_args is None:
            optional_args = {}

        self.netmiko_optional_args = netmiko_args(optional_args)
        self.netmiko_optional_args.setdefault("port", 22)

    def open(self):
        """Implement the NAPALM method open (mandatory)"""
        self.device = self._netmiko_open(
            self.device_type, netmiko_optional_args=self.netmiko_optional_args
        )

    def close(self) -> None:
        """Implement the NAPALM method close (mandatory)"""
        self._netmiko_close()

    def _send_command(
        self, command: Union[str, List], use_textfsm: bool = False
    ) -> Union[str, Dict[str, str]]:
        """Wrapper for self.device.send.command().
        If command is a list will iterate through commands until valid command.
        """
        try:
            output = ""
            if isinstance(command, list):
                for cmd in command:
                    output = self.device.send_command(cmd, use_textfsm=use_textfsm)
                    if not use_textfsm:
                        output = output.strip()
                    if "% Invalid" not in output:
                        break
            else:
                output = self.device.send_command(command, use_textfsm=use_textfsm)
                if not use_textfsm:
                    output = output.strip()

            return output
        except (socket.error, EOFError) as e:
            raise ConnectionClosedException(str(e))

    @staticmethod
    def _sanitize_config(config: str) -> str:
        """Remove sensitive information from config"""
        match_to_sanitize = [
            r"username\s+\S+\s+password.*\n",
            r"enable\s+password.*\n",
            r"snmp-server\s+usm-user.*\n.*\n",
            r"snmp-server community.*\n",
        ]
        config = re.sub("|".join(match_to_sanitize), "", config)

        return config

    @staticmethod
    def _format_interface_name(interface: str) -> str:
        """Format interface name"""
        if re.search(r"\d+", interface):
            interface_type = re.match(r"[A-Za-z]+", interface).group(0)
            interface_unit = (
                re.search(r"\d+(\/)?(\s+)?(\d+)?", interface).group(0).replace(" ", "")
            )
            interface = f"{interface_type.capitalize()} {interface_unit}"

        return interface

    @staticmethod
    def _format_uptime(uptime: str) -> float:
        """Format uptime in seconds"""
        uptime_sec = 0.0

        uptime_info = uptime.replace("and", "").replace(" ", "").split(",")

        for info in uptime_info:
            unit = re.search(r"[a-zA-Z]+", info).group(0)
            time_value = float(re.search(r"\d+(\.\d+)?", info).group(0))
            if unit == "days":
                uptime_sec += time_value * 86400.0
            elif unit == "hours":
                uptime_sec += time_value * 3600.0
            elif unit == "minutes":
                uptime_sec += time_value * 60.0
            elif unit == "seconds":
                uptime_sec += time_value

        return float(uptime_sec)

    @staticmethod
    def _get_ip_version(ip: str) -> str:
        """Get ip version (ip or ipv6)"""
        return "ip" if type(ip_address(ip)) is IPv4Address else "ipv6"

    def cli(
        self, commands: List[str], encoding: str = "text"
    ) -> Dict[str, Union[str, Dict[str, Any]]]:
        if encoding != "text":
            raise NotImplementedError(f"{encoding} is not a supported encoding")
        cli_output = dict()
        if not isinstance(commands, list):
            raise TypeError("Please enter a valid list of commands!")

        for command in commands:
            output = self._send_command(command)
            if "Incorrect usage" in output:
                raise ValueError(f"Unable to execute command {command}")
            cli_output.setdefault(command, {})
            cli_output[command] = output

        return cli_output

    def get_config(
        self, retrieve: str = "all", full: bool = False, sanitized: bool = False
    ) -> models.ConfigDict:
        data = {
            "startup": "",
            "running": "",
            "candidate": "",
        }

        if retrieve in ["all", "running"]:
            command = "show running-config"
            config = self._send_command(command)

            if sanitized:
                config = self._sanitize_config(config)

            data["running"] = config
        if retrieve in ["all", "startup"]:
            command = "show startup-config"
            config = self._send_command(command)

            if sanitized:
                config = self._sanitize_config(config)

            data["startup"] = config

        return data

    def get_arp_table(self, vrf: str = "") -> List[models.ARPTableDict]:
        command = "show arp"
        output = self._send_command(command, use_textfsm=True)

        data = []

        for entry in output:
            data.append(
                {
                    "interface": entry["interface"],
                    "mac": entry["mac"],
                    "ip": entry["address"],
                    "age": float(entry["age"]),
                }
            )

        return data

    def get_facts(self) -> models.FactsDict:
        commands = ["show version"]
        output = {}
        for command in commands:
            output[command] = self._send_command(command, use_textfsm=False)
            if "<context>" in output[command]:
                self.context = True

            output[command] = get_structured_data(output[command], platform=self.device_type, command=command)

        data = {
            "uptime": self._format_uptime(output["show version"][0]["uptime"]),
            "vendor": self.vendor,
            "os_version": output["show version"][0]["version"],
            "serial_number": output["show version"][0]["serial"][0],
            "model": output["show version"][0]["model"],
            "hostname": output["show version"][0]["hostname"],
            "fqdn": "",
            "interface_list": [
                self._format_interface_name(entry)
                for entry in output["show version"][0]["interfaces"]
            ],
        }

        return data

    def is_alive(self) -> models.AliveDict:
        null = chr(0)
        if self.device is None:
            return {"is_alive": False}
        try:
            # Try sending ASCII null byte to maintain the connection alive
            self.device.write_channel(null)
            return {"is_alive": self.device.remote_conn.transport.is_active()}
        except (socket.error, EOFError):
            # If unable to send, we can tell for sure that the connection is unusable
            return {"is_alive": False}

    def ping(
        self,
        destination: str,
        source: str = "",
        ttl: int = 255,
        timeout: int = 2,
        size: int = 100,
        count: int = 5,
        vrf: str = "",
        source_interface: str = "",
    ) -> models.PingResultDict:
        command = f"ping {destination} size {size} repeat {count}"
        output = self._send_command(command, use_textfsm=True)[0]

        data = {}

        if int(output["success_qty"]) == 0:
            data["error"] = f"unknown host {destination}"
        else:
            data["success"] = {
                "probes_sent": int(output["sent_qty"]),
                "packet_loss": int(output["sent_qty"]) - int(output["success_qty"]),
                "rtt_min": float(output["rtt_min"]),
                "rtt_max": float(output["rtt_max"]),
                "rtt_avg": float(output["rtt_avg"]),
                "rtt_stddev": -1.0,
                "results": [
                    {"ip_address": destination, "rtt": float(output["rtt_avg"])}
                ],
            }

        return data

    def get_interfaces(self) -> Dict[str, models.InterfaceDict]:
        """
                Returns a dictionary of dictionaries. The keys for the first dictionary will be the \
                interfaces in the devices. The inner dictionary will containing the following data for \
                each interface:

                 * is_up (True/False)
                 * is_enabled (True/False)
                 * description (string)
                 * last_flapped (float in seconds)
                 * speed (float in Mbit)
                 * MTU (in Bytes)
                 * mac_address (string)

                Example::

                    {
                    u'Management1':
                        {
                        'is_up': False,
                        'is_enabled': False,
                        'description': '',
                        'last_flapped': -1.0,
                        'speed': 1000.0,
                        'mtu': 1500,
                        'mac_address': 'FA:16:3E:57:33:61',
                        },
                    u'Ethernet1':
                        {
                        'is_up': True,
                        'is_enabled': True,
                        'description': 'foo',
                        'last_flapped': 1429978575.1554043,
                        'speed': 1000.0,
                        'mtu': 1500,
                        'mac_address': 'FA:16:3E:57:33:62',
                        },
                    u'Ethernet2':
                        {
                        'is_up': True,
                        'is_enabled': True,
                        'description': 'bla',
                        'last_flapped': 1429978575.1555667,
                        'speed': 1000.0,
                        'mtu': 1500,
                        'mac_address': 'FA:16:3E:57:33:63',
                        },
                    u'Ethernet3':
                        {
                        'is_up': False,
                        'is_enabled': True,
                        'description': 'bar',
                        'last_flapped': -1.0,
                        'speed': 1000.0,
                        'mtu': 1500,
                        'mac_address': 'FA:16:3E:57:33:64',
                        }
                    }
                """
        command = "show interface"
        ttp_parsing = AsaTemplates()

        output = ttp_parsing.get_structured_data(self._send_command(command, use_textfsm=False), command=command,
                                                 platform=self.device_type)

        data = {}
        if output:
            if len(output) > 0:
                if len(output[0]) > 0:
                    if "interface" in output[0][0]:
                        if isinstance(output[0][0]["interface"], list):
                            for interface in output[0][0]["interface"]:
                                data[interface["phy_if"]] = _parse_interface_data(interface)
                        elif isinstance(output[0][0]["interface"], dict):
                            data[output[0][0]["interface"]["phy_if"]] = _parse_interface_data(
                                output[0][0]["interface"])
        return data

