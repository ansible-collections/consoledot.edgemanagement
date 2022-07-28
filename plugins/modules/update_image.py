#!/usr/bin/python


# (c) 2022, Adam Miller (admiller@redhat.com)
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
    elements: str

author:
  - Adam Miller (@maxamillion)
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Update image named "BuiltFromAnsible" with the added package "vim-enhanced"
  consoledot.edgemanagement.update_image:
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
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    EDGE_API_IMAGES,
    EDGE_API_IMAGESETS,
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
        packages=dict(required=False, type="list", default=[], elements="str"),
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    postdata = {}
    try:
        old_image = crc_request.get(f"{EDGE_API_IMAGES}/{module.params['id']}")
        image_set = crc_request.get(
            f"{EDGE_API_IMAGESETS}/{old_image['ImageSetID']}"
        )
        #   {
        #     "name": "tpapaioa-20220204-1",
        #     "version": 2,
        #     "description": "",
        #     "distribution": "rhel-85",
        #     "imageType": "rhel-edge-commit",
        #     "packages": [],
        #     "outputTypes": [
        #       "rhel-edge-commit"
        #     ],
        #     "commit": {
        #       "arch": "x86_64"
        #     },
        #     "installer": {
        #       "username": "",
        #       "sshkey": ""
        #     }
        #   }
        postdata.update(
            {
                "Name": old_image["Name"],
                "Version": image_set["Data"]["image_set"]["Version"] + 1,
                "Description": f'RHEL for Edge Image Updated by Ansible Module - {old_image["Name"]}',
                "Distribution": old_image["Distribution"],
                "Packages": [],
                "OutputTypes": ["rhel-edge-commit"],
                "Commit": {
                    "arch": old_image["Commit"]["Arch"],
                },
                "Installer": {
                    "Username": "",
                    "Sshkey": "",
                },
            }
        )

        # FIXME - maybe deal with installer later
        # with_installer = module.params["installer"]
        # if with_installer and ("rhel-edge-installer" not in postdata["OutputTypes"]):
        #    postdata["OutputTypes"].append("rhel-edge-installer")

        for package in module.params["packages"]:
            postdata["Packages"].append(
                {
                    "name": package,
                }
            )

        response = crc_request.post(
            f"{EDGE_API_IMAGES}/{image_set['Data']['images'][0]['image']['ID']}/update",
            data=json.dumps(postdata),
        )
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
