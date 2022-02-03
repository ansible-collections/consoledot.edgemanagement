#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (maxamillion@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: imagesets_info
short_description: Obtain information about one or many RHEL for Edge ImageSets on console.redhat.com 
description:
  - This module obtains information about one or many RHEL for Edge ImageSets on console.redhat.com, with filter options.
version_added: "0.1.0"
options:
  id:
    description:
      - Obtain only information of the ImageSets with provided ID
    required: false
    type: int
  name:
    description:
      - Obtain only information of the ImageSet matching the provided name
    required: false
    type: str
notes:
  - You may provide many filters and they will all be applied, except for C(id)
    as that will return only the Rule identified by the unique ID provided.

author: Adam Miller @maxamillion 
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
- name: Get information about the Rule named "Custom Company DDoS Rule"
  maxamillion.fleetmanager.imagesets_info
    id: 1024
  register: imageset1024_info

- name: debugging output of the imageset1024_info registered variable
  debug:
    var: imageset1024_info
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

    argspec = dict(
        id=dict(required=False, type="int"),
        name=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    if module.params["id"]:
        imagesets = crc_request.get(
            "/api/edge/v1/image-sets/{0}".format(module.params["id"])
        )

    else:
        query_strs = []

        if module.params["name"]:
            query_strs.append("name={0}".format(quote(to_text(module.params["name"]))))

        if query_strs:
            imagesets = crc_request.get(
                "/api/edge/v1/image-sets?{0}".format("&".join(query_strs))
            )
        else:
            imagesets = crc_request.get("/api/edge/v1/image-sets/")

    module.exit_json(imagesets=imagesets, changed=False)


if __name__ == "__main__":
    main()
