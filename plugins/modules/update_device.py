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
  client_id:
    description:
      - RHC Client ID of device to upgrade
    required: true
    type: str
  imageset_id:
    description:
      - Id of ImageSet to use for the device upgrade
    required: true
    type: str

author: Adam Miller @maxamillion 
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Get ImageSet Info for named image "WesternRegionTerminalPOS"
  consoledot.edgemanagement.imagesets_info:
    name: "WesternRegionTerminalPOS"
  register: imageinfo_output

- name: Upgrade device 2ae43de4-bce7-4cfb-9039-af77458260ea with latest WesternRegionTerminalPOS image
  consoledot.edgemanagement.update_device:
    client_id: "2ae43de4-bce7-4cfb-9039-af77458260ea"
    imageset_id: "{{ im
  register: imagebuild_info

- name: debugging output of the imagebuild_info registered variable
  debug:
    var: imagebuild_info
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible.module_utils.six.moves.urllib.parse import quote
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.fleetmanager import (
    ConsoleDotRequest,
)

import copy
import json


def main():

    distro_choices = ["rhel-84", "rhel-85"]

    arch_choices = ["x86_64", "aarch64"]

    argspec = dict(
        name=dict(required=True, type="str"),
        packages=dict(required=False, type="list"),
        ssh_user=dict(required=True, type="str"),
        ssh_pubkey=dict(required=True, type="str"),
        distribution=dict(
            required=False, type="str", default="rhel-85", choices=distro_choices
        ),
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
        "name": module.params["name"],
        "version": 0,
        "distribution": module.params["distribution"],
        "imageType": "rhel-edge-installer",
        "packages": [],
        "outputTypes": [
            "rhel-edge-commit",
        ],
        "commit": {"arch": "x86_64"},
        "installer": {
            "username": module.params["ssh_user"],
            "sshkey": module.params["ssh_pubkey"],
        },
        "description": f'RHEL for Edge Image Created by Ansible Module - {module.params["name"]}',
    }

    with_installer = module.params["installer"]
    if with_installer:
        postdata["outputTypes"].append("rhel-edge-installer")

    for package in module.params["packages"]:
        postdata["packages"].append(
            {
                "name": package,
            }
        )

    try:
        response = crc_request.post("/api/edge/v1/images/", data=json.dumps(postdata))
        if response["Status"] not in [400, 403, 404]:
            module.exit_json(
                msg="Successfully queued image build", image=response, postdata=postdata
            )
        else:
            module.fail_json(msg=response, postdata=postdata)

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=postdata)


if __name__ == "__main__":
    main()
