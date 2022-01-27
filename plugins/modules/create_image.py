#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (maxamillion@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: create_image
short_description: Create a new RHEL for Edge Image on console.redhat.com 
description:
  - This module will build a RHEL for Edge Image on console.redhat.com
version_added: "0.1.0"
options:
  name:
    description:
      - Name ImageSet that will be created based on this new Image build request
    required: true
    type: str
  packages:
    description:
      - Name ImageSet that will be created based on this new Image build request
    required: false
    type: list
  ssh_pubkey:
    description:
      - ssh public key to allow user C(ssh_user) to access to devices provisioned using this Image
    required: true
    type: str
  ssh_user:
    description:
      - user to allow ssh access too devices provisioned using this Image
    required: true
    type: str
  rhel_release:
    description:
      - which RHEL Release to base this on
    required: false
    type: str
    choices: [ "rhel-85", "rhel-84" ]

author: Adam Miller @maxamillion 
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Create image named "BuiltFromAnsible" with the added package "vim-enhanced"
  maxamillion.fleetmanager.create_image
    name: "BuildFromAnsible"
    packages:
      - "vim-enhanced"
  register: imagebuild_info

- name: debugging output of the imagebuild_info registered variable
  debug:
    var: imagebuild_info
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible.module_utils.six.moves.urllib.parse import quote
from ansible_collections.maxamillion.fleetmanager.plugins.module_utils.fleetmanager import ConsoleDotRequest

import copy
import json


def main():

    argspec = dict(
        name=dict(required=True, type="str"),
        packages=dict(required=False, type="list"),
        ssh_user=dict(required=True, type="str"),
        ssh_pubkey=dict(required=True, type="str"),
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    postdata = {
        "version": 0,
        "name": module.params['name'],
        "description": f'RHEL for Edge Image Created by Ansible Module - {module.params["name"]}',
        "selected-packages": [],
    }

    for package in module.params['packages']:
        postdata['selected-packages'].append({
            "selected": True,
            "name": package,
        })


if __name__ == "__main__":
    main()
