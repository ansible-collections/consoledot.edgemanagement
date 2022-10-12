#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Chris Santiago (resolutecoder@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
---
module: filter_systems
short_description: Filter systems with facts
description:
  - This module will filter systems with insights facts
version_added: "0.1.0"
options:
  host_type:
    description:
      - The host type to filter by
    required: false
    type: str
  display_name:
    description:
      - The display name to filter by
    required: false
    type: str
  hostname_or_id:
    description:
      - The hostname or id to filter by
    required: false
    type: str
  fqdn:
    description:
      - The fully qualified domain name to filter by
    required: false
    type: str
  insights_id:
    description:
      - The insights id to filter by
    required: false
    type: str
  ipv4:
    description:
      - The ipv4 address to filter by
    required: false
    type: str
  os_release:
    description:
      - The os release to filter by
    required: false
    type: str
  cores_per_socket:
    description:
      - The cores per socket to filter by
    required: false
    type: int
  infrastructure_vendor:
    description:
      - The infrastructure vendor to filter by
    required: false
    type: str
  number_of_cpus:
    description:
      - The number of cpus to filter by
    required: false
    type: int
  number_of_sockets:
    description:
      - The number of sockets to filter by
    required: false
    type: int
  os_kernel_version:
    description:
      - The os kernel version to filter by
    required: false
    type: str
  enabled_services:
    description:
      - The enabled services to filter by
    required: false
    type: list
    elements: str
  installed_services:
    description:
      - The installed services to filter by
    required: false
    type: list
    elements: str

notes:
    - Edge related data (edge_device_id, edge_image_id, edge_update_available)  is injected in system info if host type is edge
author:
  - Chris Santiago (@resoluteCoder)
"""

EXAMPLES = """
- name: Filter systems
  tasks:
    - name: Filter systems by insight facts
      consoledot.edgemanagement.filter_systems:
        host_type: 'edge'
        ipv4: '192.168.122.[22:199]'
        os_release: '8.5'
        cores_per_socket: 1
        infrastructure_vendor: 'kvm'
        number_of_cpus: 1
        number_of_sockets: 1
        os_kernel_version: '4.18.0'
        enabled_services:
          - 'firewalld'
          - 'rhcd'
        installed_services:
          - 'rhsm'
          - 'rhcd'
      register: filtered_systems

    - debug: var=filtered_systems['matched_systems']
"""

RETURN = """
"""

from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
    INVENTORY_API_HOSTS,
    EDGE_API_DEVICES,
)


def parse_ip_pattern(section):
    if section == '[]':
        return (0, 255)

    if ':' not in section:
        return (int(section), int(section))

    min, max = section.replace('[', '').replace(']', '').split(':')
    return (int(min), int(max))


def get_queries(facts):
    top_level_filters = ['display_name',
                         'fqdn', 'hostname_or_id', 'insights_id']
    queries = []
    for fact in facts:
        fact_key, fact_value = fact

        excluded_params = ['host_type', 'ipv4']
        if fact_key in excluded_params or fact_value is None:
            continue

        filter_string = ''
        if fact_key in top_level_filters:
            filter_string = '%s=%s' % (
                fact_key, fact_value)
            queries.append(filter_string)
        elif isinstance(fact_value, list):
            for value in fact_value:
                filter_string = 'filter[system_profile][%s][]=%s' % (
                    fact_key, value)
                queries.append(filter_string)
        else:
            filter_string = 'filter[system_profile][%s][]=%s' % (
                fact_key, fact_value)
            queries.append(filter_string)
    return queries


def get_matched_systems_by_ipv4(systems, ipv4_sections):
    matched_systems = []
    for system in systems:
        for ip in system['ip_addresses']:
            if ':' not in ip and ip != '127.0.0.1':
                for index, section in enumerate(ipv4_sections):
                    min, max = parse_ip_pattern(section)
                    ip_section = int(ip.split('.')[index])
                    if ip_section < min or ip_section > max:
                        break
                    if index == 3:  # last element in list
                        matched_systems.append(system)
    return matched_systems


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
        mutually_exclusive=[['display_name', 'fqdn', 'hostname_or_id', 'insights_id']])

    crc_request = ConsoleDotRequest(module)

    try:
        queries = get_queries(module.params.items())
        api_request = '%s?%s' % (
            INVENTORY_API_HOSTS, '&'.join(queries))
        response = crc_request.get(api_request)

        if module.params['ipv4']:
            matched_systems = get_matched_systems_by_ipv4(response['results'], module.params['ipv4'].split('.'))
        else:
            matched_systems = response['results']

        if module.params['host_type'] == 'edge':
            edge_device_ids = []
            for system in matched_systems:
                api_request = '%s/%s' % (EDGE_API_DEVICES, system['id'])
                response = crc_request.get(api_request)

                edge_device_ids.append(response['Device']['ID'])

                system['edge_device_id'] = response['Device']['ID']
                system['edge_image_id'] = response['Device']['ImageID']
                system['edge_update_available'] = response['Device']['UpdateAvailable']

            module.exit_json(
                msg='ran', changed=False, matched_systems=matched_systems, edge_device_ids=edge_device_ids)
        else:
            module.exit_json(
                msg='ran', changed=False, matched_systems=matched_systems, edge_device_ids=[])
    except Exception as e:
        module.fail_json(msg=to_text(e), changed=False, matched_systems=[], edge_device_ids=[])


if __name__ == "__main__":
    main()
