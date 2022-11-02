# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (admiller@redhat.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type
from ansible.module_utils.connection import Connection

INVENTORY_API_HOSTS = '/api/inventory/v1/hosts'

EDGE_API_DEVICES = '/api/edge/v1/devices'
EDGE_API_DEVICESVIEW = '/api/edge/v1/devices/devicesview'
EDGE_API_GROUPS = '/api/edge/v1/device-groups'
EDGE_API_IMAGES = '/api/edge/v1/images'
EDGE_API_IMAGESETS = '/api/edge/v1/image-sets'
EDGE_API_IMAGESETS_VIEW = '/api/edge/v1/image-sets/view'
EDGE_API_THIRDPARTYREPO = '/api/edge/v1/thirdpartyrepo'
EDGE_API_IMAGEBUILDER_PACKAGES = '/api/image-builder/v1/packages'


class ConsoleDotRequest(object):
    def __init__(self, module, headers=None):

        self.module = module
        self.connection = Connection(self.module._socket_path)

    def _httpapi_error_handle(self, method, path, custom_error_msg='', data=None):
        # FIXME - make use of handle_httperror(self, exception) where applicable
        #   https://docs.ansible.com/ansible/latest/network/dev_guide/developing_plugins_network.html#developing-plugins-httpapi

        try:
            code, response = self.connection.send_request(method, path, data=data)
            return response
        except Exception as e:
            if custom_error_msg == '':
                self.module.fail_json(msg=f"[{method}] - {e}")
            else:
                self.module.fail_json(msg=custom_error_msg)

    def get(self, path, **kwargs):
        return self._httpapi_error_handle("GET", path, **kwargs)

    def put(self, path, **kwargs):
        return self._httpapi_error_handle("PUT", path, **kwargs)

    def post(self, path, **kwargs):
        return self._httpapi_error_handle("POST", path, **kwargs)

    def patch(self, path, **kwargs):
        return self._httpapi_error_handle("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._httpapi_error_handle("DELETE", path, **kwargs)
