#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Chris Santiago (resolutecoder@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function
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
    required: true
    type: str
    choices: ['present', 'absent']

notes:
    - Supported input for creating group(s) are a string and a string with a sequence ([1:10]) at the end.
    - Supported input for removing group(s) are a string, string with a wildcard (* is only supported), and a sequence ([2:6] inclusive).
author:
  - Chris Santiago (@resoluteCoder)
"""

EXAMPLES = """
- name: Create a single group
  consoledot.edgemanagement.groups:
    name: 'AnsibleGroup42'
    state: 'present'

- name: Create ten groups
  consoledot.edgemanagement.groups:
    name: 'AnsibleGroup[1:10]'
    state: 'present'

- name: Remove a single group
  consoledot.edgemanagement.groups:
    name: 'AnsibleGroup42'
    state: 'absent'

# Removing with a wildcard
- name: Remove multiple groups
  consoledot.edgemanagement.groups:
    name: 'AnsibleGroup*'
    state: 'absent'

# Removing with a sequence
- name: Remove multiple groups
  consoledot.edgemanagement.groups:
    name: 'AnsibleGroup[5:6]'
    state: 'absent'
"""

from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    EDGE_API_GROUPS,
)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.parse import quote
import re
import fnmatch
import json
import ansible.module_utils.six.moves.urllib as url_lib


def main():

    argspec = dict(
        name=dict(required=True, type="str"),
        state=dict(required=True, type="str", choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    create_group_data = {"name": module.params["name"], "type": "static"}

    def post_group(name):
        group_data = {
            'name': name,
            'type': 'static'
        }
        return crc_request.post(f'{EDGE_API_GROUPS}', data=json.dumps(group_data))

    def remove_group(group):
        group_id = group['DeviceGroup']['ID']
        return crc_request.delete(f'{EDGE_API_GROUPS}/{group_id}')

    def parse_sequence(match):
        start, end = match.group().replace(
            '[', '').replace(']', '').split(':')
        return (int(start), int(end))

    def split_group_input(name: str):
        first_word, last_word = re.split(
            pattern, module.params['name'], 1)
        return (first_word, last_word)

    def expand_group_sequence(first_word: str, last_word: str, start: int, end: int):
        group_names = []
        for i in range(int(start), int(end) + 1):
            group_name = ''.join((first_word, str(i), last_word))
            group_names.append(group_name)
        return group_names

    def create_multiple_groups(first_word, group_names):
        has_been_changed = False
        message = 'Nothing changed'

        # limit the results to iterate
        group_data = crc_request.get_groups(first_word)

        for name in group_names:
            group_match = crc_request.find_group(group_data, name)
            if len(group_match) == 0:
                post_group(name)
                if (not has_been_changed):
                    has_been_changed = True
                    message = 'Groups created successfully'

        module.exit_json(msg=message, changed=has_been_changed)

    def remove_multiple_groups(first_word, group_names):
        has_been_changed = False
        message = 'Nothing changed'

        # limit the results to iterate
        group_data = crc_request.get_groups(first_word)

        for name in group_names:
            group_match = crc_request.find_group(group_data, name)
            if len(group_match) == 1:
                remove_group(group_match[0])
                if (not has_been_changed):
                    has_been_changed = True
                    message = 'Groups removed successfully'

        module.exit_json(msg=message, changed=has_been_changed)

    try:
        if module.params['state'] == 'present':
            # create multiple groups
            pattern = r'\[\d+:\d+\]'
            match = re.search(pattern, module.params['name'])
            if match:
                first_word, last_word = split_group_input(
                    module.params['name'])
                start, end = parse_sequence(match)
                group_names = expand_group_sequence(
                    first_word, last_word, start, end)

                create_multiple_groups(first_word, group_names)

            # create single group
            group_data = crc_request.get_groups()
            group_match = crc_request.find_group(group_data)

            if len(group_match) == 1:
                module.exit_json(
                    msg="Nothing changed", changed=False, postdata=create_group_data
                )

            post_group(module.params['name'])

            module.exit_json(
                msg='Group created successfully',
                changed=True,
                postdata=create_group_data
            )

        if module.params['state'] == 'absent':
            # remove multiple groups with sequence
            pattern = r'\[\d+:\d+\]'
            match = re.search(pattern, module.params['name'])
            if match:
                first_word, last_word = split_group_input(
                    module.params['name'])
                start, end = parse_sequence(match)
                group_names = expand_group_sequence(
                    first_word, last_word, start, end)
                remove_multiple_groups(first_word, group_names)

            # remove multiple groups with *
            if '*' in module.params['name']:
                first_word = ''
                for string in module.params['name'].split('*'):
                    if string != '':
                        first_word = string
                        break

                # limit the results to iterate
                group_data = crc_request.get_groups(first_word)

                if group_data['data'] is None:
                    module.exit_json(msg='Nothing changed', changed=False)

                for group in group_data['data']:
                    name = group['DeviceGroup']['Name']
                    found_match = fnmatch.fnmatch(name, module.params['name'])
                    if found_match:
                        remove_group(group)

                module.exit_json(
                    msg='Removed groups successfully', changed=True)

            # remove single group
            group_data = crc_request.get_groups()

            group_match = crc_request.find_group(group_data)
            if len(group_match) == 0:
                module.exit_json(
                    msg="Nothing changed", changed=False, postdata=group_data
                )

            response = remove_group(group_match[0])

            group_data = crc_request.get_groups()
            group_match = crc_request.find_group(group_data)

            if len(group_match) == 0:
                module.exit_json(
                    msg="Group removed successfully", changed=True, postdata=group_data
                )
            else:
                module.fail_json(msg=response, postdata=create_group_data)

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=create_group_data)


if __name__ == "__main__":
    main()
