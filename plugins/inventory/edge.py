from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: maxamillion.fleetmanager.edge
    plugin_type: inventory
    short_description: Red Hat Edge Manager Inventory Plugin
    description:
        - Creates dynamic inventory from the console.redhat.com Edge Manager inventory service.
        - Uses a YAML configuration file that ends with ``hostinventory.(yml|yaml)``.
    extends_documentation_fragment:
        - constructed
    options:
      plugin:
        description: the name of this plugin, it should always be set to 'maxamillion.fleetmanager.edge' for this plugin to recognize it as it's own.
        required: True
        choices: ['maxamillion.fleetmanager.edge']
      user:
        description: Red Hat username
        required: True
        env:
            - name: EDGE_USER
      password:
        description: Red Hat password
        required: True
        env:
            - name: EDGE_PASSWORD
      server:
        description: Inventory server to connect to
        default: https://console.redhat.com
      selection:
        description: Choose what variable to use for ansible_host
        default: fqdn
        type: str
      vars_prefix:
        description: prefix to apply to host variables
        default: rhedge 
        type: str
'''

EXAMPLES = '''
# basic example using environment vars for auth and no extra config
plugin: maxamilion.fleetmanager.rhhinventory
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.module_utils.six.moves.urllib.parse import urlencode, quote_plus
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.urls import Request
from ansible.errors import AnsibleError
from distutils.version import LooseVersion
import ansible.module_utils.six.moves.urllib.error as urllib_error
import json

class InventoryModule(BaseInventoryPlugin, Constructable):
    ''' Host inventory parser for ansible using Red Hat Edge Manager as source. '''

    NAME = 'maxamillion.fleetmanager.edge'

    def parse_tags(self, tag_list):
        results = {}
        if len(tag_list) > 0:
            for tag in tag_list:
                if tag['namespace'] not in results.keys():
                    results[tag['namespace']] = {tag['key']: tag['value']}
                else:
                    results[tag['namespace']].update({tag['key']: tag['value']})
        return results

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('edge.yaml', 'edge.yml')):
                valid = True
            else:
                self.display.vvv('Skipping due to inventory source not ending in "edge.yaml" nor "edge.yml"')
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        self.server = self.get_option('server')
        edge_device_view_url = "%s/api/edge/v1/devices/devicesview?" % (self.server)
        inventory_hosts_url = "%s/api/inventory/v1/hosts/" % (self.server)
        strict = self.get_option('strict')
        selection = self.get_option('selection')
        vars_prefix = self.get_option('vars_prefix')
        username = self.get_option('user')
        password = self.get_option('password')

        self.headers = {"Accept": "application/json"}
        self.request = Request(
            url_username=username, url_password=password,
            use_proxy=True, headers=self.headers, force_basic_auth=True
        )

        first_page = json.load(self.request.get(edge_device_view_url + "limit=1"))

        pagination_step = 20
        results = []
        for offset in range(0, first_page['count'], pagination_step):
            try:
                response = json.load(
                    self.request.get(edge_device_view_url + "limit=%d&offset=%d" % (pagination_step,offset))
                )
                results += response['data']['devices']
            except urllib_error.HTTPError as e:
                raise AnsibleError("http error: %s" % to_native(e))
            except IndexError as e:
                raise AnsibleError(
                    "Invalid Response from server(%s): %s" % (to_native(self.server), to_native(e))
                )

        for host in results:

            try:

                device_inventory_check = json.load(self.request.get(inventory_hosts_url + host['DeviceUUID']))
                if 'count' in device_inventory_check and device_inventory_check['count'] == 0:
                    continue

                sysprofile = json.load(self.request.get(inventory_hosts_url + "%s/system_profile" % host['DeviceUUID']))
                for interface in sysprofile['results'][0]['system_profile']['network_interfaces']:
                    if 'ipv4_addresses' in interface:
                        if '127.0.0.1' not in interface['ipv4_addresses']:
                            for ipaddr in interface['ipv4_addresses']:
                                host_name = self.inventory.add_host(ipaddr)
                                for item in host.keys():
                                    self.inventory.set_variable(host_name, vars_prefix + item, host[item])
                                    if item == selection:
                                        self.inventory.set_variable(host_name, 'ansible_host', host[item])

                                if 'DeviceGroups' in host and host['DeviceGroups']:
                                    for group in host['DeviceGroups']:
                                        self.inventory.add_group(self._sanitize_group_name(group['Name']))
                                        self.inventory.add_host(host_name, group=self._sanitize_group_name(group['Name']))


            except urllib_error.HTTPError as e:
                raise AnsibleError("Host Inventory Service HTTP Error: %s" % to_native(e))

 
