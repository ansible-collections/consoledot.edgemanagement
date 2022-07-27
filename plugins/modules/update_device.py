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
    - This module will deploy the latest version of a device's RHEL for Edge Image
      on console.redhat.com Edge Management
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
author:
    - Adam Miller (@maxamillion)
notes:
    - Either name or group must be provided
"""


# FIXME - provide correct example here
RETURN = """
"""

EXAMPLES = """
-   name: Upgrade a set of devices
    consoledot.edgemanagement.update_device:
        name:
            - device1
            - device2
            - device3
    register: deviceupdate_output

-   name: Upgrade groups of devices
    consoledot.edgemanagement.update_device:
        group:
            - group1
            - group2
    register: deviceupdate_output
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native

from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    EDGE_API_UPDATES,
)
import copy
import json


def main():

    argspec = dict(
        name=dict(required=False, type="list", elements="str"),
        group=dict(required=False, type="list", elements="str"),
    )

    module = AnsibleModule(
        argument_spec=argspec,
        required_one_of=[["name", "group"]],
        supports_check_mode=False,
    )

    crc_request = ConsoleDotRequest(module)

    def get_update_commit_id(ostree_hash: str):
        image_info = crc_request.get_image_by_hash(ostree_hash)

        imageset_info = crc_request.get_imageset_by_id(image_info["ImageSetID"])

        update_image = [
            image
            for image in imageset_info["images"]
            if image["image"]["Version"] == imageset_info["image_set"]["Version"]
        ]

        return update_image[0]["image"]["ID"]

    try:
        not_found_devices = []
        hosts_postdata = {}
        # Handle hosts
        if module.params["name"]:
            for name in module.params["name"]:
                inventory_hosts_data = crc_request.get_inventory_hosts(name)

                if inventory_hosts_data["count"] > 1:
                    module.fail_json(
                        f"Ambiguous selector provided for name: {name}. "
                        "More than one device returned by inventory service."
                    )
                if inventory_hosts_data["count"] == 0:
                    not_found_devices.append(name)
                    continue

                booted_ostree = [
                    ostree["checksum"]
                    for ostree in inventory_hosts_data["results"][0]["system_profile"][
                        "rpm_ostree_deployments"
                    ]
                    if ostree["booted"]
                ]

                update_commit_id = get_update_commit_id(booted_ostree[0])

                hosts_postdata.setdefault(update_commit_id, [])
                hosts_postdata[update_commit_id].append(
                    inventory_hosts_data["results"][0]["id"]
                )

        # Handle groups
        if module.params["group"]:
            for gname in module.params["group"]:
                group_data = crc_request.get_groups(name=gname)
                matched_group = crc_request.find_group(group_data, name=gname)[0]
                group_hosts = crc_request.get_group_hosts(
                    matched_group["DeviceGroup"]["ID"]
                )

                for device in group_hosts:
                    if device["AvailableHash"]:
                        update_commit_id = get_update_commit_id(device["AvailableHash"])

                        hosts_postdata.setdefault(update_commit_id, [])
                        hosts_postdata[update_commit_id].append(device["UUID"])
    except Exception as e:
        module.fail_json(
                msg=(
                    "ERROR: Unknown error occurred, please file an issue "
                    "ticket here: FIXME_NEED_LINK_TO_COLLECTION_REPO "
                    f"and provide this output: {to_native(e)}"
                )
            )

    hosts_responses = []
    try:
        for k, v in hosts_postdata.items():
            postdata = {"CommitID": k, "DevicesUUID": v}
            host_response = crc_request.post(
                EDGE_API_UPDATES, data=json.dumps(postdata)
            )
            hosts_responses.append(host_response)

    except Exception as e:
        module.fail_json(msg=to_text(e), hosts_postdata=hosts_postdata)

    module.exit_json(
        msg="Update Transaction scheduled with Edge Management",
        host_update_response=hosts_responses,
        changed=True,
    )
    # module.exit_json(msg="I dunno ... ", group_hosts=group_hosts)


if __name__ == "__main__":
    main()
