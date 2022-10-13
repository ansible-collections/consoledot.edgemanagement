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
    EDGE_API_UPDATES
)
import q
import copy
import json

def batch_edge_systems(systems: list, isUUIDS = True) -> dict:
    if isUUIDS:
        image_set_key = 'ImageSetID'
        system_id_key = 'DeviceUUID'
    else:
        image_set_key = 'edge_image_set_id'
        system_id_key = 'id'

    image_set_ids = {}
    for system in systems:
        if system[image_set_key] in image_set_ids:
            image_set_ids[system[image_set_key]].append(system[system_id_key])
        else:
            image_set_ids[system[image_set_key]] = [system[system_id_key]]
    return image_set_ids


def main():

    argspec = dict(
        systems=dict(required=False, type="list", elements="dict"),
        uuids=dict(required=False, type="list", elements="str"),
        groups=dict(required=False, type="list", elements="str"),
        version=dict(required=False, type="int"),
    )

    module = AnsibleModule(
        argument_spec=argspec,
        )

    crc_request = ConsoleDotRequest(module)

    def update_systems(systems):
        for _, system_uuids in systems.items():
            system_post_data = {
                'CommitID': 0,
                'DevicesUUID': system_uuids
            }
            try:
                crc_request.post(
                    EDGE_API_UPDATES, data=json.dumps(system_post_data)
                )
            except Exception as e:
                module.fail_json(msg=e)

    dispatched_updated = False

    # used with filter systems module
    if module.params['systems']:
        systems_with_updates = []
        for system in module.params['systems']:
            if system['edge_update_available'] and \
            system['edge_system_status'] == 'RUNNING':
                systems_with_updates.append(system)

        batched_systems = batch_edge_systems(systems_with_updates, isUUIDS=False)
        update_systems(batched_systems)
        dispatched_updated = True

    if module.params['uuids']:
        systems_with_updates = []
        for uuid in module.params['uuids']:
            edge_system_data = crc_request.get_edge_system(uuid)

            if edge_system_data['UpdateAvailable'] and \
            edge_system_data['Status'] == 'RUNNING':
                systems_with_updates.append(edge_system_data)

        batched_systems = batch_edge_systems(systems_with_updates)
        update_systems(batched_systems)
        dispatched_updated = True

    if module.params['groups']:
        pass

    module.exit_json(msg='ran succesfully', changed=dispatched_updated)

if __name__ == "__main__":
    main()
