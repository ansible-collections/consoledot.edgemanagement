#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (maxamillion@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type
from ansible.module_utils.urls import CertificateError
from ansible.module_utils.six.moves.urllib.parse import urlencode, quote_plus
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.connection import Connection
from ansible.module_utils._text import to_text

import json

BASE_HEADERS = {"Content-Type": "application/json"}

class ConsoleDotRequest(object):
    def __init__(self, module, headers=None, not_rest_data_keys=None):

        self.module = module
        self.connection = Connection(self.module._socket_path)

        self.headers = headers if headers else BASE_HEADERS

    def _httpapi_error_handle(self, method, path, data=None):
        # FIXME - make use of handle_httperror(self, exception) where applicable
        #   https://docs.ansible.com/ansible/latest/network/dev_guide/developing_plugins_network.html#developing-plugins-httpapi

        try:
            code, response = self.connection.send_request(
                method, path, data=data, headers=self.headers
            )

        except ConnectionError as e:
            self.module.fail_json(msg=f"connection error occurred: {e}")
        except CertificateError as e:
            self.module.fail_json(msg=f"certificate error occurred: {e}")
        except ValueError as e:
            self.module.fail_json(msg=f"certificate not found: {e}")

        if code == 500:
            self.module.fail_json(msg=f"Error-500: {response}")

        return response

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
