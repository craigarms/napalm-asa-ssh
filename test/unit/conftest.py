"""Test fixtures."""
from builtins import super

import pytest
from napalm.base import models
from napalm.base.test import conftest as parent_conftest

from napalm.base.test.double import BaseTestDouble
from netmiko.utilities import get_structured_data

from napalm_asa_ssh import AsaSSHDriver


@pytest.fixture(scope='class')
def set_device_parameters(request):
    """Set up the class."""
    def fin():
        request.cls.device.close()
    request.addfinalizer(fin)

    request.cls.driver = AsaSSHDriver
    request.cls.patched_driver = PatchedAsaSSHDriver
    request.cls.vendor = 'AsaSSH'
    parent_conftest.set_device_parameters(request)


def pytest_generate_tests(metafunc):
    """Generate test cases dynamically."""
    parent_conftest.pytest_generate_tests(metafunc, __file__)


class PatchedAsaSSHDriver(AsaSSHDriver):
    """Patched AsaSSH Driver."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Patched AsaSSH Driver constructor."""
        super().__init__(hostname, username, password, timeout, optional_args)

        self.patched_attrs = ['device']
        self.device = FakeAsaSSHDevice()

    def open(self):
        pass

    def close(self) -> None:
        pass

    def is_alive(self):
        return {"is_alive": True}


class FakeAsaSSHDevice(BaseTestDouble):
    """AsaSSH device test double."""

    def __init__(self):
        self.device_type = "cisco_asa"

    def send_command(self, command, **kwargs):
        filename = "{}.txt".format(self.sanitize_text(command))
        full_path = self.find_file(filename)
        data = self.read_txt_file(full_path)

        if kwargs["use_textfsm"]:
            data = get_structured_data(data, platform=self.device_type, command=command)

        return data

