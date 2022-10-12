#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (admiller@redhat.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: update_systems
short_description: Create a new RHEL for Edge Image on console.redhat.com
description:
  - This module will build a RHEL for Edge Image on console.redhat.com
version_added: "0.1.0"
options:
  name:
    description:
      - RHC Client ID of device to upgrade
    required: false
    type: list
    elements: str
  group:
    description:
      - Group name to upgrade
    required: false
    type: list
    elements: str
  imageset_id:
    description:
      - Id of ImageSet to use for the device upgrade
    required: true
    type: str
author:
  - Adam Miller (@maxamillion)
notes:
  - Either C(name) or C(group) must be provided
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Upgrade a set of devices
  consoledot.edgemanagement.update_device:
    name:
      - device1
      - device2
      - device3
  register: deviceupdate_output

- name: Upgrade two groups of devices
  consoledot.edgemanagement.update_device:
    group:
      - group1
      - group2
  register: deviceupdate_output
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
)
import copy
import json


def main():

    argspec = dict(
        systems=dict(required=False, type="list", elements="str"),
        groups=dict(required=False, type="list", elements="str"),
    )

    module = AnsibleModule(
        argument_spec=argspec,
        required_one_of=[["name", "group"]],
        supports_check_mode=False)

    crc_request = ConsoleDotRequest(module)

    # used with filter systems module
    if module.params['systems']:

    if module.params['ids']:
    if module.params['groups']:


if __name__ == "__main__":
    main()
