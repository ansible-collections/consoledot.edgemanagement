#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (admiller@redhat.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: update_device
short_description: Create a new RHEL for Edge Image on console.redhat.com
description:
  - This module will build a RHEL for Edge Image on console.redhat.com
version_added: "0.1.0"
options:
  name:
    description:
      - RHC Client ID of device to upgrade
    required: false
    type: list
    elements: str
  group:
    description:
      - Group name to upgrade
    required: false
    type: list
    elements: str
  imageset_id:
    description:
      - Id of ImageSet to use for the device upgrade
    required: true
    type: str
author:
  - Adam Miller (@maxamillion)
notes:
  - Either C(name) or C(group) must be provided
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Upgrade a set of devices
  consoledot.edgemanagement.update_device:
    name:
      - device1
      - device2
      - device3
  register: deviceupdate_output

- name: Upgrade two groups of devices
  consoledot.edgemanagement.update_device:
    group:
      - group1
      - group2
  register: deviceupdate_output
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
)
import copy
import json


def main():

    argspec = dict(
        name=dict(required=False, type="list", elements="str"),
        group=dict(required=False, type="list", elements="str"),
        imageset_id=dict(required=True, type="str"),
    )

    module = AnsibleModule(
        argument_spec=argspec,
        required_one_of=[["name", "group"]],
        supports_check_mode=False)

    crc_request = ConsoleDotRequest(module)

    module.fail_json(msg="ERROR: Module not implemented")

    devices = []

    if module.params['group']:
        # get list of devices in group
        devices.append()

    # FIXME - THIS MODULE IS NOT YET IMPLEMENTED


#    try:
#        response = crc_request.post("/api/edge/v1/updates/", data=json.dumps(postdata))
#        if response["Status"] not in [400, 403, 404]:
#            module.exit_json(
#                msg="Successfully queued image build", image=response, postdata=postdata
#            )
#        else:
#            module.fail_json(msg=response, postdata=postdata)
#
#    except Exception as e:
#        module.fail_json(msg=to_text(e), postdata=postdata)


if __name__ == "__main__":
    main()
