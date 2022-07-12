#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Matthew Sandoval (matovalcode@gmail.com)
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function
import json
import validators
from ansible_collections.consoledot.edgemanagement.plugins.module_utils.edgemanagement import (
    ConsoleDotRequest,
)
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: custom_repositories
short_description: Create and remove custom repositories
description:
  - This module will create and remove custom repositories, adding a custom repository allows you to add packages from outside Red Hat to your image
version_added: "0.1.0"
options:
  name:
    description:
      - Custom repository name that will be created
    required: true
    type: str
  base_url:
    description:
      - Url where the custom package list is hosted
    required: false
    type: str
  state:
    description:
      - Should the custom repository exist or not
    required  true
    type: str
    choices: ['present', 'absent']

author: Matthew Sandoval @matoval
"""

EXAMPLES = """
- name: Create a custom repositories
  consoledot.edgemanagement.custom_repositories
    name: 'AnsibleRepo123'
    base_url: 'http://repolocation.com/customrepo/repo'
    state: 'present'
"""


def main():

    EDGE_API_REPOS = '/api/edge/v1/thirdpartyrepo'

    argspec = dict(
        name=dict(required=True, type='str'),
        base_url=dict(required=False, type='str'),
        state=dict(required=True, type='str', choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)

    crc_request = ConsoleDotRequest(module)

    create_repo_data = {
        "name": module.params["name"],
        "url": module.params["base_url"]
    }

    def validate_base_url(base_url):
        return validators.url(base_url)

    def find_repo(repo_data):
        if repo_data['data'] == None:
            return []
        return [
            repository for repository in repo_data['data'] if repository['Name'] == module.params['name']
        ]

    def get_repos():
        return crc_request.get(f'{EDGE_API_REPOS}?name={module.params["name"]}')

    def post_repo():
        return crc_request.post(f'{EDGE_API_REPOS}', data=json.dumps(create_repo_data))

    def remove_repo(repo):
        repo_id = repo[0]['ID']
        return crc_request.delete(f'{EDGE_API_REPOS}/{repo_id}')

    try:
        if module.params['state'] == 'present':
            if module.params['base_url'] == None:
                module.fail_json(msg="Base url is required when state equals present")

            is_base_url_valid = validate_base_url(module.params['base_url'])
            if not is_base_url_valid:
                module.fail_json(msg="Base url is not a valid url")

            repo_data = get_repos()
            repo_match = find_repo(repo_data)

            if len(repo_match) == 1:
                module.exit_json(
                    msg="Nothing changed",
                    changed=False,
                    postdata=create_repo_data
                )

            response = post_repo()

            repo_data = get_repos()

            repo_match = find_repo(repo_data)
            if len(repo_match) == 0:
                module.fail_json(msg='Failure to create custom repository',
                                 postdata=repo_data)
            else:
                module.exit_json(
                    msg='Custom repository created successfully',
                    changed=True,
                    postdata=create_repo_data
                )

        if module.params['state'] == 'absent':
            repo_data = get_repos()

            repo_match = find_repo(repo_data)
            if len(repo_match) == 0:
                module.exit_json(msg='Nothing changed',
                                 changed=False, postdata=repo_data)

            response = remove_repo(repo_match)

            repo_data = get_repos()
            repo_match = find_repo(repo_data)

            if len(repo_match) == 0:
                module.exit_json(msg='Custom repository removed successfully',
                                 changed=True, postdata=repo_data)
            else:
                module.fail_json(msg=response, postdata=create_repo_data)

    except Exception as e:
        module.fail_json(msg=to_text(e), postdata=create_repo_data)


if __name__ == "__main__":
    main()
