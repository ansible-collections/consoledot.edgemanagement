# (c) 2022 Adam Miller
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
author: Adam Miller <maxamillion>
httpapi : consoledot
short_description: HttpApi Plugin for console.redhat.com
description:
  - This HttpApi plugin provides methods to connect to console.redhat.com
    services via HTTP(S)-based api.
version_added: "0.1.0"
"""

import json

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.connection import ConnectionError
from ansible_collections.ibm.qradar.plugins.module_utils.qradar import BASE_HEADERS


class HttpApi(HttpApiBase):
    def send_request(self, request_method, path, data=None, headers=None):
        headers = headers if headers else BASE_HEADERS

        try:
            self._display_request(request_method)
            response, response_data = self.connection.send(
                path, data, method=request_method, headers=headers
            )
            value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(value)
        except HTTPError as e:
            error = json.loads(e.read())
            return e.code, error

    def _display_request(self, request_method):
        self.connection.queue_message(
            "vvvv", "Web Services: %s %s" % (request_method, self.connection._url)
        )

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            raise ConnectionError("Invalid JSON response: %s" % response_text)

    def update_auth(self, response, response_text):
        cookie = response.info().get("Set-Cookie")
        # Set the 'SEC' header
        if "SEC" in cookie:
            return {"SEC": cookie.split(";")[0].split("=")[-1]}

        return None

    def logout(self):
        self.send_request("POST", "/auth/logout")

        # Clean up tokens
        self.connection._auth = None
