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
from ansible.module_utils.urls import Request
from ansible.errors import AnsibleError
from distutils.version import LooseVersion
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
        url = "%s/api/edge/v1/devices/devicesview?" % (self.server)
        strict = self.get_option('strict')
        selection = self.get_option('selection')
        vars_prefix = self.get_option('vars_prefix')
        systems_by_id = {}
        system_tags = {}
        results = []

        self.headers = {"Accept": "application/json"}
        self.request = Request(url_username=self.get_option('user'), url_password=self.get_option('password'))

        first_page = json.load(self.request.get(url))
        import q; q.q(first_page)

        pagination_step = 20
        for offset in range(0, first_page['count'], pagination_step):
            response = json.load(self.request.get(url + "limit=%d&offset=%d" % (pagination_step,offset)))

            if response.status_code != 200:
                raise AnsibleError("http error (%s): %s" %
                                   (response.status_code, response.text))
            elif response.status_code == 200:
                results += response['devices']


        for host in results:
            host_name = self.inventory.add_host(host['DeviceName'])
            systems_by_id[host['DeviceUUID']] = host_name
            for item in host.keys():
                self.inventory.set_variable(host_name, vars_prefix + item, host[item])
                if item == selection:
                    self.inventory.set_variable(host_name, 'ansible_host', host[item])

