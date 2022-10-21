#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Chris Santiago (chsantia@redhat.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: update_image
short_description: updates latest image to a new image version
description:
  - This module will build the latest version for a RHEL for Edge Image on console.redhat.com
version_added: "0.1.0"
options:
  name:
    description:
      - Name of image that will be updated
    required: true
    type: str
  packages:
    description:
      - Aditional packages to add for the new image
    required: false
    type: list
    elements: str
  output_type:
    description:
      - Type of image that will be built.
    required: false
    type: str
    default: commit
  username:
    description:
      - username that will be used for the new image
    required: false
    type: str
  sshkey:
    description:
      - sshkey that will be used for the new image
    required: false
    type: str

author:
  - Chris Santiago (@resoluteCoder)
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Update image
  hosts: CRC
  gather_facts: false
  tasks:
    - name: Update frontend image
      consoledot.edgemanagement.update_image:
        name: 'frontendv5'
        output_type: 'installer'
        username: 'user1'
        sshkey: 'ssh-rsa test123'
        packages:
          - "vim-enhanced"
          - "sssd"
          - "dnsmasq"
          - "buildah"
          - "containernetworking-plugins"
          - "python3-psutil"
          - "toolbox"
          - "audit"
          - "cronie"
          - "crypto-policies"
          - "crypto-policies-scripts"
          - "curl"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible.module_utils.six.moves.urllib.parse import quote
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    EDGE_API_IMAGES,
    EDGE_API_IMAGESETS_VIEW,
    EDGE_API_IMAGEBUILDER_PACKAGES
)

import json


def main():

    argspec = dict(
        name=dict(required=True, type='str'),
        packages=dict(required=False, type='list', default=[], elements="str"),
        output_type=dict(required=False, type='str', default='commit'),
        username=dict(required=False, type='str'),
        sshkey=dict(required=False, type='str', no_log=True)
    )

    module = AnsibleModule(
        argument_spec=argspec,
        supports_check_mode=True,
        required_if=[['output_type', 'installer', ['username', 'sshkey']]]
    )

    crc_request = ConsoleDotRequest(module)
    postdata = {}
    try:
        response = crc_request.get(EDGE_API_IMAGESETS_VIEW + '?name=%s' % module.params['name'])
        if response['count'] == 0:
            module.fail_json(msg='%s not found' % module.params['name'])
        if response['count'] > 1:
            module.fail_json(msg='found more than one image, image name must be unique')
        if response['data'][0]['Status'] == 'BUILDING':
            module.exit_json(msg='Image has been queued for updating.')
        if response['data'][0]['Status'] in ['SUCCESS', 'ERROR']:
            current_image = crc_request.get(EDGE_API_IMAGES + '/%s/details' % response['data'][0]['ImageID'])

            postdata = {
                'name': current_image['image']['Name'],
                'version': current_image['image']['Version'] + 1,
                'description': f'RHEL for Edge Image Updated by Ansible Module - {current_image["image"]["Name"]}',
                'distribution': current_image['image']['Distribution'],
                'packages': [],
                'imageType': 'rhel-edge-commit',
                'outputTypes': ["rhel-edge-commit"],
                'commit': {
                    'arch': current_image['image']['Commit']['Arch'],
                },
                'installer': {
                    'username': current_image['image']['Installer']['Username'],
                    'sshkey': current_image['image']['Installer']['SshKey'],
                },
                'thirdPartyRepositories': []
            }

            if module.params['output_type'] == 'installer':
                postdata['outputTypes'].append('rhel-edge-installer')
                postdata['imageType'] = 'rhel-edge-installer'

                postdata['installer']['username'] = module.params['username']
                postdata['installer']['sshkey'] = module.params['sshkey']

            for package in module.params["packages"]:
                distribution = current_image['image']['Distribution']
                architecture = current_image['image']['Commit']['Arch']
                custom_error_msg = 'Package: %s, not supported in distribution: %s and architecture: %s' % (package, distribution, architecture)
                verify_package_api = f'{EDGE_API_IMAGEBUILDER_PACKAGES}?distribution={distribution}&architecture={architecture}&search={package}'

                crc_request.get(
                    verify_package_api,
                    custom_error_msg=custom_error_msg
                )
                postdata['packages'].append(
                    {
                        'name': package,
                    }
                )

            response = crc_request.post(
                EDGE_API_IMAGES + '/%s/update' % current_image['image']['ID'],
                data=json.dumps(postdata),
            )
            module.exit_json(msg='Successfully queued image build', image=response, postdata=postdata)

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=postdata)


if __name__ == '__main__':
    main()
