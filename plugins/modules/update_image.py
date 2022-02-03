#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (maxamillion@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: update_image
short_description: Update a new RHEL for Edge Image on console.redhat.com 
description:
  - This module will build a RHEL for Edge Image on console.redhat.com
version_added: "0.1.0"
options:
  id:
    description:
      - ID of Image that will be updated based on this new Image build request
    required: true
    type: int
  packages:
    description:
      - Aditional packages to add for this Image update build
    required: false
    type: list
  installer:
    description:
      - Update an installable ISO along with the RHEL for Edge Image ostree commit
    required: false
    type: bool
    default: true

author: Adam Miller @maxamillion
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Update image named "BuiltFromAnsible" with the added package "vim-enhanced"
  maxamillion.fleetmanager.update_image
    id: 6148
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
from ansible_collections.maxamillion.fleetmanager.plugins.module_utils.fleetmanager import (
    ConsoleDotRequest,
)

import copy
import json


def main():

    distro_choices = ["rhel-84", "rhel-85"]

    arch_choices = ["x86_64", "aarch64"]
    # FIXME - ambiguous results returned by image-sets name search, it defaults to partial-matching
    # name=dict(required=False, type="str"),
    # curl -H "Content-Type: application/json" --url https://console.redhat.com:443/api/edge/v1/image-sets?name="Ansible" | jq .Data[0].image_set.Images[0].ID
    argspec = dict(
        id=dict(required=True, type="int"),
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

    try:
        postdata = crc_request.get(f"/api/edge/v1/images/{module.params['id']}")

        with_installer = module.params["installer"]
        if with_installer and ("rhel-edge-installer" not in pastdata["OutputTypes"]):
            postdata["outputTypes"].append("rhel-edge-installer")

        for package in module.params["packages"]:
            postdata["packages"].append(
                {
                    "name": package,
                }
            )

        response = crc_request.post(
            f"/api/edge/v1/images/{module.params['id']}/update",
            data=json.dumps(postdata),
        )
        if response["Status"] not in [400, 403, 404]:
            module.exit_json(
                msg="Successfully queued image build", image=response, postdata=postdata
            )
        else:
            module.fail_json(msg=response, postdata=postdata)

    except e:
        module.fail_json(msg=to_text(e), postdata=postdata)


if __name__ == "__main__":
    main()
