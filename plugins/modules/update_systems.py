#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (admiller@redhat.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: update_systems
short_description: Update systems
description:
  - This module will update systems to the latest update or to a specific version
version_added: "0.1.0"
options:
  systems:
    description:
      - Systems that are passed from the filter systems module to be updated.
    required: false
    type: list
    elements: dict
  uuids:
    description:
      - System UUIDs to be updated
    required: false
    type: list
    elements: str
  groups:
    description:
      - Group to be updated
    required: false
    type: list
    elements: str
  version:
    description:
      - Image version the system(s) will be set to.
    required: false
    type: int
author:
  - Chris Santiago (@resoluteCoder)
notes:
  - systems will only work if the input is supplied by the filter systems module
"""

EXAMPLES = """
- name: Update systems
  hosts: CRC
  gather_facts: false
  tasks:
    - name: Update systems to latest version using ids
      consoledot.edgemanagement.update_systems:
        uuids:
          - '160adfc2-00b1-48d5-b607-8b5ae7f4a861'
        version: 7
      register: output

- name: Filter systems
  hosts: CRC
  gather_facts: false
  tasks:
    - name: Filter systems by insight facts
      consoledot.edgemanagement.filter_systems:
        host_type: 'edge'
        ipv4: '192.168.122.[22:199]'
        display_name: 'frontendv8'
        os_release: '8.5'
        cores_per_socket: 1
        infrastructure_vendor: 'kvm'
        number_of_cpus: 1
        number_of_sockets: 1
        os_kernel_version: '4.18.0'
        enabled_services:
          - 'firewalld'
          - 'rhcd'
        installed_services:
          - 'rhsm'
          - 'rhcd'
      register: filtered_systems

    - name: Update systems to latest version using ids
      consoledot.edgemanagement.update_systems:
        systems: '{{ filtered_systems["matched_systems"] }}'
        version: 7
      register: output
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    EDGE_API_UPDATES,
    EDGE_API_IMAGESETS
)
import json


def batch_edge_systems(systems: list, isUUIDS=True) -> dict:
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

    def update_systems(systems, commit_id=0):
        for image_set_id, system_uuids in systems.items():
            system_post_data = {
                'CommitID': commit_id,
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
        if module.params['version']:
            imageset_id = module.params['systems'][0]['edge_image_set_id']
            for system in module.params['systems']:
                if system['edge_image_set_id'] != imageset_id:
                    module.exit_json(msg='systems have multiple image sets, \
                                     systems need to have the same image set')

            # FIXME - properly handle pagination
            edge_api_image_set_versions = EDGE_API_IMAGESETS + '/view/%s/versions' % imageset_id
            response = crc_request.get(edge_api_image_set_versions)
            if module.params['version'] > response['count']:
                module.exit_json(msg='version provided not found')

            version_image_id = 0
            for version in response['data']:
                if version['Version'] == module.params['version']:
                    version_image_id = version['ID']

            edge_api_image_set = EDGE_API_IMAGESETS + '/view/%s/versions/%s' \
                % (imageset_id, version_image_id)
            response = crc_request.get(edge_api_image_set)
            image_commit_id = response['ImageDetails']['image']['CommitID']

            systems = []
            for system in module.params['systems']:
                systems.append(system['id'])

            update_systems({imageset_id: systems}, image_commit_id)
            dispatched_updated = True
        else:
            systems_with_updates = []
            for system in module.params['systems']:
                if system['edge_update_available'] and system['edge_system_status'] == 'RUNNING':
                    systems_with_updates.append(system)

            batched_systems = batch_edge_systems(systems_with_updates, isUUIDS=False)
            update_systems(batched_systems)
            dispatched_updated = True

    if module.params['uuids']:
        systems_with_updates = []
        for uuid in module.params['uuids']:
            edge_system_data = crc_request.get_edge_system(uuid)

            if edge_system_data['UpdateAvailable'] and edge_system_data['Status'] == 'RUNNING':
                systems_with_updates.append(edge_system_data)

        batched_systems = batch_edge_systems(systems_with_updates)
        update_systems(batched_systems)
        dispatched_updated = True

    if module.params['groups']:
        for group_name in module.params['groups']:
            response = crc_request.get_groups(group_name)
            group_data = crc_request.find_group(response, group_name)

            if len(group_data) == 0:
                module.fail_json(msg='%s cannot be found' % group_name)

            edge_systems = group_data[0]['DeviceGroup']['Devices']
            for system in edge_systems:
                if system['UpdateAvailable']:
                    # key is dummy image set id to match function param
                    update_systems({0: [system['UUID']]})

    module.exit_json(msg='ran succesfully', changed=dispatched_updated)


if __name__ == "__main__":
    main()
