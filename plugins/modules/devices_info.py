#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (maxamillion@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: devices_info
short_description: Obtain information about one or many RHEL for Edge systems on console.redhat.com 
description:
  - This module obtains information about one or many RHEL for Edge systems on console.redhat.com, with filter options.
version_added: "0.1.0"
options:
  client_id:
    description:
      - Obtain only information of the device with provided RHC Client ID
    required: false
    type: str
  name:
    description:
      - Obtain only information of the device matching the provided name
    required: false
    type: str

author: Adam Miller @maxamillion 
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Get information about the device named "test-device"
  maxamillion.fleetmanager.devices_info
    name: test-device
  register: testdevice_info

- name: debugging output of the testdevice_info registered variable
  debug:
    var: testdevice_info
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible.module_utils.six.moves.urllib.parse import quote
from ansible_collections.maxamillion.fleetmanager.plugins.module_utils.fleetmanager import ConsoleDotRequest

import copy
import json


def main():

    argspec = dict(
        client_id=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    devices = {}

    try:
        if module.params["client_id"]:
            devices = crc_request.get(
                "/api/edge/v1/devices/{0}".format(module.params["client_id"])
            )

        else:
            query_strs = []

            if module.params["name"]:
                query_strs.append(
                    quote('hostname_or_id="{0}"'.format(to_text(module.params["name"])))
                )

            if query_strs:
                devices = crc_request.get(
                    "/api/edge/v1/devices?{0}".format("&".join(query_strs))
                )
            else:
                devices = crc_request.get("/api/edge/v1/devices/")


        if ('Status' in devices) and (devices['Status'] in [400, 403, 404]):
            module.fail_json(msg=devices)
    except e:
        module.fail_json(msg=to_text(e))

    module.exit_json(devices=devices, changed=False)


if __name__ == "__main__":
    main()
