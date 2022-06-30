#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Chris Santiago (resolutecoder@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function
import json
import copy
from ansible_collections.maxamillion.fleetmanager.plugins.module_utils.fleetmanager import (
    ConsoleDotRequest,
)
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: groups
short_description: Create and remove groups
description:
  - This module will create and remove groups
version_added: "0.1.0"
options:
  name:
    description:
      - Group name that will be created
    required: true
    type: str
  state:
    description:
      - Should the group exist or not
    required  true
    type: str
    choices: ['present', 'absent']

author: Chris Santiago @resolutecoder
"""

EXAMPLES = """
- name: Create a group
  maxamillion.fleetmanager.groups
    name: 'AnsibleGroup42'
    state: 'present'
"""


def main():

    EDGE_API_GROUPS = '/api/edge/v1/device-groups'

    argspec = dict(
        name=dict(required=True, type='str'),
        state=dict(required=True, type='str')
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    create_group_data = {
        "name": module.params["name"],
        'type': 'static'
    }

    def find_group(group_data):
        if group_data['data'] == None:
            return []
        return [
            group for group in group_data['data'] if group['DeviceGroup']['Name'] == module.params['name']
        ]

    def get_groups():
        return crc_request.get(f'{EDGE_API_GROUPS}?name={module.params["name"]}')

    def post_group():
        return crc_request.post(f'{EDGE_API_GROUPS}', data=json.dumps(create_group_data))

    def remove_group(group):
        group_id = group[0]['DeviceGroup']['ID']
        return crc_request.delete(f'{EDGE_API_GROUPS}/{group_id}')

    try:
        if module.params['state'] == 'present':
            group_data = get_groups()
            group_match = find_group(group_data)

            if len(group_match) == 1:
                module.exit_json(
                    msg="Nothing changed",
                    changed=False,
                    postdata=create_group_data
                )

            response = post_group()

            group_data = get_groups()

            group_match = find_group(group_data)
            if len(group_match) == 0:
                module.fail_json(msg='Failure to create group',
                                 postdata=group_data)
            else:
                module.exit_json(
                    msg='Group created successfully',
                    changed=True,
                    postdata=create_group_data
                )

        if module.params['state'] == 'absent':
            group_data = get_groups()

            group_match = find_group(group_data)
            if len(group_match) == 0:
                module.exit_json(msg='Nothing changed',
                                 changed=False, postdata=group_data)

            response = remove_group(group_match)

            group_data = get_groups()
            group_match = find_group(group_data)

            if len(group_match) == 0:
                module.exit_json(msg='Group removed successfully',
                                 changed=True, postdata=group_data)
            else:
                module.fail_json(msg=response, postdata=create_group_data)

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=create_group_data)


if __name__ == "__main__":
    main()
