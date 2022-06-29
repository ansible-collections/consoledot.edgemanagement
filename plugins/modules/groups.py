#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (maxamillion@gmail.com)
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
import q

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


def main():

    argspec = dict(
        name=dict(required=True, type='str'),
        state=dict(required=True, type='str')
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
    create_group_data = {
        "name": module.params["name"],
        'type': 'static'
    }

    # with_installer = module.params["installer"]
    # if with_installer:
    #     postdata["outputTypes"].append("rhel-edge-installer")

    # for package in module.params["packages"]:
    #     postdata["packages"].append(
    #         {
    #             "name": package,
    #         }
    #     )

    # if module.params['state'] == 'absent':
    #     response = crc_request.post(
    #         "/api/edge/v1/device-groups/", data=json.dumps(create_group_data))

    try:
        if module.params['state'] == 'present':
            response = crc_request.post(
                "/api/edge/v1/device-groups/", data=json.dumps(create_group_data))

            group_data = crc_request.get(
                '/api/edge/v1/device-groups?name=%s'.format(module.params['name']))

            if group_data['count'] == 0:
                module.fail_json(msg='failure to create group',
                                 postdata=group_data)
            else:
                module.exit_json(
                    msg="Successfully created group through ansible!! not the ui!",
                    image=response,
                    postdata=create_group_data
                )

        if module.params['state'] == 'absent':
            group_data = crc_request.get(
                '/api/edge/v1/device-groups?name=%s'.format(module.params['name']))
            q.q(module.params['name'])

            name_match = [
                for group in group_data['data'] if group['DeviceGroup']['ID'] == module.params['name']
            ]
            # import q
            # q.q(group_data)
            q.q(group_data['count'])
            # if group_data['count'] == 0:
            if len(name_match) == 0:
                module.exit_json(msg='nothing changed',
                                 change=False, postdata=group_data)

            # group_id = group_data['data'][0]['DeviceGroup']['ID']
            group_id = name_match[0]['DeviceGroup']['ID']
            q.q(group_id)
            response = crc_request.delete(
                "/api/edge/v1/device-groups/%s".format(group_id))
            q.q(response)
            # response = crc_request.delete(
            #     "/api/edge/v1/device-groups/27346")
            # "/api/edge/v1/device-groups/%s".format(group_data['data'][0]['DeviceGroup']['ID']), data=json.dumps(create_group_data))
            group_data = crc_request.get(
                '/api/edge/v1/device-groups?name=%s'.format(module.params['name']))
            # import q
            # q.q(group_data)

            if group_data['count'] == 0:
                module.exit_json(msg='group removed successfully',
                                 change=True, postdata=group_data)

            # if response["Status"] not in [400, 403, 404]:
            #     module.exit_json(
            #         msg="Successfully created group through ansible!! not the ui!",
            #         image=response,
            #         postdata=create_group_data
            #     )
            else:
                module.fail_json(msg=response, postdata=create_group_data)

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=create_group_data)


if __name__ == "__main__":
    main()
