# (c) 2022 Adam Miller
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
author:
 - Adam Miller (@maxamillion)
name: consoledot
short_description: HttpApi Plugin for console.redhat.com
description:
  - This HttpApi plugin provides methods to connect to console.redhat.com
    services via HTTP(S)-based api.
version_added: "0.1.0"
options:
  offline_token:
    type: str
    description:
      - Red Hat SSO Offline Token (https://access.redhat.com/articles/3626371)
    default: ""
    vars:
      - name: ansible_httpapi_consoledot_offline_token
  token_domain:
    type: str
    description:
      - Domain to authenticate against
    default: sso.redhat.com
    vars:
      - name: ansible_httpapi_consoledot_token_domain
"""

import json
import time

from ansible.module_utils.basic import to_text, to_bytes, to_native
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.urls import Request
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.utils.display import Display

display = Display()

BASE_HEADERS = {
    "Content-Type": "application/json",
}


class HttpApi(HttpApiBase):
    def _hack_the_auth(self):
        # I am committing sins against humanity because the Red Hat SSO does
        # not just use straight API keys but instead an API auth key that will
        # allow an user to provision a secondary API key that is temporary.
        # That secondary API key can actually be used to talk to REST APIs
        # in console.redhat.com
        #   Docs: https://access.redhat.com/articles/3626371
        if not self.connection._auth and self.get_option("offline_token"):
            request = Request()
            token_request_form_data = {
                "grant_type": "refresh_token",
                "client_id": "rhsm-api",
                "refresh_token": self.get_option("offline_token"),
            }

            result = []
            for key, values in token_request_form_data.items():
                values = [values]
                for value in values:
                    if value is not None:
                        result.append((to_text(key), to_text(value)))

            results = json.load(
                request.open(
                    "POST",
                    "https://%s/auth/realms/redhat-external/protocol/openid-connect/token"
                    % self.get_option("token_domain"),
                    data=to_text(urlencode(result, doseq=True)),
                )
            )

            self.connection._auth = {
                "Authorization": "Bearer %s" % to_text(results["access_token"])
            }

    def send_request(self, request_method, path, data=None, headers=None):

        self._hack_the_auth()

        try:
            headers = headers if headers else BASE_HEADERS
            headers["User-Agent"] = "curl/7.82.0"
            self._display_request(request_method)
            if self.connection._auth:
                headers.update(self.connection._auth)
            response, response_data = self.connection.send(
                path, data, method=request_method, headers=headers
            )
            value = to_text(response_data.getvalue())

            return response.getcode(), self._response_to_json(value)
        except HTTPError as e:
            error = json.loads(e.read())
            return e.code, error

    def _display_request(self, request_method):
        display.vvvvv("Web Services: %s %s" % (request_method, self.connection._url))

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            raise ConnectionError("Invalid JSON response: %s" % response_text)

    def update_auth(self, response, response_text):
        self._hack_the_auth()
        return self.connection._auth if self.connection._auth else None
