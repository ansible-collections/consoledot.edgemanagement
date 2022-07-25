#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Chris Santiago (resolutecoder@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
---
module: add_devices_to_group
short_description: Create and remove devices to and from a group
description:
  - This module will create and remove devices to and from a group
version_added: "0.1.0"
options:
  name:
    description:
      - Group name for adding devices to
    required: true
    type: str
  devices:
    description:
      - List of devices to be added to a group
    required: true
    type: list
    elements: int
  state:
    description:
      - Should the devices exist or not
    required: true
    type: str
    choices: ['present', 'absent']

author:
  - Chris Santiago (@resolutecoder)
"""

EXAMPLES = """
- name: Add devices to a group
  hosts: CRC
  gather_facts: false
  tasks:
    - name:
      consoledot.edgemanagement.add_devices_to_group:
        name: 'ansible-group-santiago'
        devices:
          - 21402
          - 21365
          - 31601
        state: 'present'

- name: Remove devices to a group
  hosts: CRC
  gather_facts: false
  tasks:
    - name:
      consoledot.edgemanagement.add_devices_to_group:
        name: 'ansible-group-santiago'
        devices:
          - 21402
          - 21365
          - 31601
        state: 'absent'
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    EDGE_API_GROUPS,
)
import json


def find_group(name, group_data):
    if group_data["data"] is None:
        return []
    return [
        group
        for group in group_data["data"]
        if group["DeviceGroup"]["Name"] == name
    ]


def format_group_data(group_id, device_ids):
    group_data = {"Devices": [], "ID": None}
    for device_id in device_ids:
        group_data["Devices"].append({"ID": device_id})
    group_data['ID'] = group_id
    return group_data


def main():

    argspec = dict(
        name=dict(required=True, type="str"),
        devices=dict(required=True, type="list", elements="int"),
        state=dict(required=True, type="str", choices=["present", "absent"]),
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    try:
        group_data = crc_request.get('%s?name=%s' % (EDGE_API_GROUPS, module.params["name"]))
        group_match = find_group(module.params['name'], group_data)

        if len(group_match) == 0:
            module.fail_json(msg="Group does not exist", changed=False)

        group_id = group_data["data"][0]["DeviceGroup"]["ID"]
        device_group_data = format_group_data(group_id, module.params['devices'])

        if module.params["state"] == "present":

            group_devices = group_data['data'][0]['DeviceGroup']['Devices']
            if len(group_devices) > 0:
                group_device_ids = []
                for device in group_devices:
                    group_device_ids.append(device['ID'])

                new_device_ids = []
                for device_id in module.params['devices']:
                    if device_id not in group_device_ids:
                        new_device_ids.append(device_id)

                if len(new_device_ids) == 0:
                    module.exit_json(
                        msg='Nothing changed',
                        changed=False,
                        postdata=device_group_data,
                    )

                device_group_data = format_group_data(group_id, new_device_ids)

            crc_request.post(
                '%s/%s/devices' % (EDGE_API_GROUPS, group_id), data=json.dumps(device_group_data)
            )
            module.exit_json(
                msg='Added devices to %s successfully' % module.params['name'],
                changed=True,
                postdata=device_group_data,
            )

        if module.params["state"] == "absent":
            crc_request.delete(
                '%s/%s/devices' % (EDGE_API_GROUPS, group_id), data=json.dumps(device_group_data)
            )

            module.exit_json(
                msg='Removed devices to %s successfully' % module.params['name'],
                changed=True,
                postdata=device_group_data,
            )

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=device_group_data)


if __name__ == "__main__":
    main()
