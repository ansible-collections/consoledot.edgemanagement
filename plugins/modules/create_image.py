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
  distribution:
    description:
      - which RHEL Release to use to create this Image
    required: false
    type: str
    choices: [ "rhel-85", "rhel-84" ]
    default: "rhel-85"
  arch:
    description:
      - Computer architecture the Image will be installed on
    required: false
    type: str
    choices: [ "x86_64", "aarch64" ]
    default: "x86_64"
  installer:
    description:
      - Create an installable ISO along with the RHEL for Edge Image ostree commit
    required: false
    type: bool
    default: true

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

    distro_choices = [
        "rhel-84",
        "rhel-85"
    ]

    arch_choices = [ 
        "x86_64",
        "aarch64"
    ]

    argspec = dict(
        name=dict(required=True, type="str"),
        packages=dict(required=False, type="list"),
        ssh_user=dict(required=True, type="str"),
        ssh_pubkey=dict(required=True, type="str"),
        distribution=dict(required=False, type="str", default="rhel-85", choices=distro_choices),
        arch=dict(required=False, type="str", default="x86_64", choices=arch_choices),
        installer=dict(required=False, type="bool", default=True),
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    # {
    #  "name": "jhdskfjsdkfjdsjfjdsfkjk",
    #  "version": 0,
    #  "distribution": "rhel-85",
    #  "imageType": "rhel-edge-installer",
    #  "packages": [
    #    {
    #      "name": "tmux"
    #    }
    #  ],
    #  "outputTypes": [
    #    "rhel-edge-installer",
    #    "rhel-edge-commit"
    #  ],
    #  "commit": {
    #    "arch": "x86_64"
    #  },
    #  "installer": {
    #    "username": "user1",
    #    "sshkey": "ssh-rsa k"
    #  }
    # }
    postdata = {
        "name": module.params['name'],
        "version": 0,
        "distribution": module.params['distribution'],
        "imageType": "rhel-edge-installer",
        "packages": [],
        "outputTypes": [
            "rhel-edge-commit",
        ],
        "commit": {
            "arch": "x86_64"
        },
        "installer": {
            "username": module.params['ssh_user'],
            "sshkey": module.params['ssh_pubkey'],
        },
        "description": f'RHEL for Edge Image Created by Ansible Module - {module.params["name"]}',
    }

    with_installer = module.params['installer']
    if with_installer:
        postdata['outputTypes'].append('rhel-edge-installer')

    for package in module.params['packages']:
        postdata['packages'].append({
            "name": package,
        })

    try:
        response = crc_request.post("/api/edge/v1/images/", data=json.dumps(postdata))
        if response['Status'] not in [400, 403, 404]:
            module.exit_json(msg=to_text(response), postdata=postdata)
        else:
            module.fail_json(msg=to_text(response), postdata=postdata)

    except e:
        module.fail_json(msg=to_text(e), postdata=postdata)


if __name__ == "__main__":
    main()
