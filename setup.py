"""setup.py file."""

import uuid

from setuptools import setup, find_packages

__author__ = 'Craig Armstrong <cag@izec.fr>'

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-asa-ssh",
    version="0.1.0",
    packages=find_packages(),
    author="Craig Armstrong",
    author_email="cag@izec.fr",
    description="Network Automation and Programmability Abstraction Layer with Multivendor support",
    classifiers=[
        'Topic :: Utilities',
         'Programming Language :: Python',
         'Programming Language :: Python :: 2',
         'Programming Language :: Python :: 2.7',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    url="https://github.com/craigarms/napalm-asa-ssh",
    include_package_data=True,
    install_requires=reqs,
)
