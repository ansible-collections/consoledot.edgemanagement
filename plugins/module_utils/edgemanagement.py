# -*- coding: utf-8 -*-

# (c) 2022, Adam Miller (admiller@redhat.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type
from ansible.module_utils._text import to_native
from ansible.module_utils.connection import Connection
import ansible.module_utils.six.moves.urllib as url_lib
import json

INVENTORY_API_HOSTS = "/api/inventory/v1/hosts"

EDGE_API_DEVICES = "/api/edge/v1/devices"
EDGE_API_GROUPS = "/api/edge/v1/device-groups"
EDGE_API_IMAGES = "/api/edge/v1/images"
EDGE_API_IMAGESETS = "/api/edge/v1/image-sets"
EDGE_API_THIRDPARTYREPO = "/api/edge/v1/thirdpartyrepo"

INVENTORY_API_HOSTS = "/api/inventory/v1/hosts"

# Only get "edge" systems and system_profile fields consistently with edge-api
INVENTORY_API_FILTERPARAMS = "?staleness=fresh&filter[system_profile][host_type]=edge&fields[system_profile]=host_type,operating_system,greenboot_status,greenboot_fallback_detected,rpm_ostree_deployments,rhc_client_id,rhc_config_state"  # noqa

EDGE_API_DEVICES = "/api/edge/v1/devices"
EDGE_API_GROUPS = "/api/edge/v1/device-groups"
EDGE_API_IMAGES = "/api/edge/v1/images"
EDGE_API_IMAGESETS = "/api/edge/v1/image-sets"
EDGE_API_THIRDPARTYREPO = "/api/edge/v1/thirdpartyrepo"
EDGE_API_UPDATES = "/api/edge/v1/updates"


class ConsoleDotRequest(object):
    def __init__(self, module, headers=None):

        self.module = module
        self.connection = Connection(self.module._socket_path)

    def _httpapi_error_handle(self, method, path, data=None):
        # FIXME - make use of handle_httperror(self, exception) where applicable
        #   https://docs.ansible.com/ansible/latest/network/dev_guide/developing_plugins_network.html#developing-plugins-httpapi

        code, response = self.connection.send_request(method, path, data=data)

        # if code == 500:
        if code not in [200, 201]:
            self.module.fail_json(msg=f"[{method}] Error-{code}: {response}")

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

    def get_groups(self, name: str = ""):
        if not name:
            name = self.module.params["name"]

        return self.get(f"{EDGE_API_GROUPS}?name={url_lib.parse.quote(name)}")

    def find_group(self, group_data, name: str = ""):
        if not name:
            name = self.module.params["name"]

        if group_data["data"] is None:
            return []

        return [
            group
            for group in group_data["data"]
            if group["DeviceGroup"]["Name"] == name
        ]

    def get_hosts(self, name: str = ""):
        if not name:
            name = self.module.params["name"]

        return self.get(
            f"{EDGE_API_DEVICES}?hostname_or_id={url_lib.parse.quote(name)}"
        )

    def get_inventory_hosts(self, name: str):

        return self.get(
            f"{INVENTORY_API_HOSTS}{INVENTORY_API_FILTERPARAMS}&display_name={url_lib.parse.quote(name)}"
        )

    def get_device_by_id(self, uuid: str):
        return self.get(f"{EDGE_API_DEVICES}?hostname_or_id={uuid}")

    def get_image_by_hash(self, hash: str):
        return self.get(f"{EDGE_API_IMAGES}/{hash}/info")

    def get_all_hosts(self):

        first_page = json.load(
            self.request.get(
                f"{INVENTORY_API_HOSTS}{INVENTORY_API_FILTERPARAMS}&per_page=1"
            )
        )

        pagination_step = 50
        results = []
        page_offset = 0
        for offset in range(0, first_page["total"], pagination_step):
            page_offset += 1
            try:
                response = json.load(
                    self.request.get(
                        f"{INVENTORY_API_HOSTS}/{INVENTORY_API_FILTERPARAMS}&"
                        + f"per_page={pagination_step}&page={page_offset}"
                    )
                )
                results += response["data"]["devices"]
            except url_lib.error.HTTPError as e:
                self.module.fail_json(f"http error: {to_native(e)}")
            except url_lib.error.IndexError as e:
                self.module.fail_json(f"Invalid Response from host:{to_native(e)}")

    def get_imageset(self, name: str):
        imagesets = self.get(f"{EDGE_API_IMAGESETS}?name={name}")

        if imagesets["Count"] > 1:
            iset_names = [iset["Name"] for iset in imagesets["Data"]]
            self.module.fail_json(
                msg=f"Ambiguous image name provided: {name}."
                + "More than one image found: "
                + ", ".join(iset_names)
            )
        elif imagesets["Count"] == 0:
            return {}
        else:
            return imagesets["Data"][0]["image_set"]

    def get_imageset_by_id(self, id: int):
        imageset = self.get(f"{EDGE_API_IMAGESETS}/{id}")
        return imageset["Data"]

    def get_group_hosts(self, id: int):
        group_hosts = self.get(f"{EDGE_API_GROUPS}/{id}")
        return group_hosts["Devices"]
