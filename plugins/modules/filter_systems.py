#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Chris Santiago (resolutecoder@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function
import json
import q
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
)
__metaclass__ = type

DOCUMENTATION = """
---
module: groups
short_description: Create and remove groups
description:
  - This module will create and remove groups
version_added: "0.1.0"
options:
  facts:
    description:
      - Insight facts to be filtered on
    required: true
    type: list

notes:
    - Supported input for creating group(s) are a string and a string with a sequence ([1:10]) at the end.
    - Supported input for removing group(s) are a string, string with a wildcard (* is only supported), and a sequence ([2:6] inclusive).
author:
  - Chris Santiago (@resoluteCoder)
"""

EXAMPLES = """
- name: Filter by systems
  consoledot.edgemanagement.filter_systems:
    facts:
      - display_name: 'test'
      - fqdn: 'test.test'
      - cpu_model: 'test'
"""

RETURN = """
"""


def parse_ip_pattern(section):
    if section == '[]':
        return (0, 255)

    if ':' not in section:
        return (int(section), int(section))

    min, max = section.replace('[', '').replace(']', '').split(':')
    return (int(min), int(max))


def main():
    argspec = dict(
        host_type=dict(required=False, type="str"),
        display_name=dict(required=False, type="str"),
        fqdn=dict(required=False, type="str"),
        ipv4=dict(required=False, type="str"),
        hostname_or_id=dict(required=False, type="str"),
        insights_id=dict(required=False, type="str"),
        os_release=dict(required=False, type="str"),
        os_kernel_version=dict(required=False, type="str"),
        infrastructure_vendor=dict(required=False, type="str"),
        cores_per_socket=dict(required=False, type="int"),
        number_of_cpus=dict(required=False, type="int"),
        number_of_sockets=dict(required=False, type="int"),
        enabled_services=dict(required=False, type="list", elements='str'),
        installed_services=dict(required=False, type="list", elements='str'),
    )

    module = AnsibleModule(
        argument_spec=argspec, supports_check_mode=True,
        mutually_exclusive=['display_name', 'fqdn', 'hostname_or_id', 'insights_id'])

    crc_request = ConsoleDotRequest(module)

    INVENTORY_API = '/api/inventory/v1/hosts'
    EDGE_DEVICES_API = '/api/edge/v1/devices'

    top_level_filters = ['display_name',
                         'fqdn', 'hostname_or_id', 'insights_id']

    try:
        queries = []
        for param in module.params.items():
            fact_key, fact_value = param

            excluded_params = ['host_type', 'ipv4']
            if fact_key in excluded_params or fact_value is None:
                continue

            filter_string = ''
            if fact_key in top_level_filters:
                filter_string = '%s=%s' % (
                    fact_key, fact_value)
                queries.append(filter_string)
            elif type(fact_value) is list:
                for value in fact_value:
                    filter_string = 'filter[system_profile][%s][]=%s' % (
                        fact_key, value)
                    queries.append(filter_string)
            else:
                filter_string = 'filter[system_profile][%s][]=%s' % (
                    fact_key, fact_value)
                queries.append(filter_string)

        api_request = '%s?%s' % (
            INVENTORY_API, '&'.join(queries))
        response = crc_request.get(api_request)

        matched_systems = []
        for system in response['results']:
            for ip in system['ip_addresses']:
                if ':' not in ip:
                    if ip != '127.0.0.1':
                        for index, section in enumerate(module.params['ipv4'].split('.')):
                            min, max = parse_ip_pattern(section)
                            ip_section = int(ip.split('.')[index])
                            if ip_section < min or ip_section > max:
                                break
                            if index == 3:
                                matched_systems.append(system)
                                q.q(ip)
        q.q(len(matched_systems))

        if module.params['host_type'] == 'edge':
            edge_systems = []
            for result in response['results']:
                api_request = '%s/%s' % (
                    EDGE_DEVICES_API, result['id'])
                response = crc_request.get(api_request)
                edge_systems.append(response['Device']['ID'])
            module.exit_json(
                msg='ran', edge_systems=edge_systems, inventory_systems=[])
        else:
            module.exit_json(msg='ran', edge_systems=[],
                             inventory_systems=matched_systems)
    except Exception as e:
        module.fail_json(msg=to_text(e))


if __name__ == "__main__":
    main()
