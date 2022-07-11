# Red Hat Edge Manager Ansible Collection

## Tech Preview

This is the [Ansible
Collection](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
provided by the Ansible Edge Automation
Team for automating actions in [Red Hat Edge Manager](https://console.redhat.com/edge/fleet-management)


This Collection is meant for distribution through
[Ansible Galaxy](https://galaxy.ansible.com/) as is available for all
[Ansible](https://github.com/ansible/ansible) users to utilize, contribute to,
and provide feedback about.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.11**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

## Collection Content
<!--start collection content-->
<!--end collection content-->

## Installing this collection

You can install the IBM qradar collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install maxamillion.fleetmanager

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: maxamillion.fleetmanager
```

## Using the Red Hat Edge Manager Collection

An example for using this collection to manage a log source with [Red Hat Edge Manager](https://console.redhat.com/edge/fleet-management) is as follows.

### Password Auth
For password-based auth, `inventory.ini` (Note the password should be managed by a [Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html) for a production environment).

```
[CRC]
console.redhat.com

[CRC:vars]
ansible_network_os=maxamillion.fleetmanager.consoledot
ansible_connection=ansible.netcommon.httpapi
ansible_user=foobar@example.com
ansible_httpapi_pass=SuperSekretPassword
ansible_httpapi_use_ssl=yes
ansible_httpapi_validate_certs=yes
```

### Token Auth

You can obtain a Red Hat API Offline Token by following the documentation [here](https://access.redhat.com/articles/3626371), and then provide that in the `ansible_httpapi_consoledot_offline_token` inventory var as follows (Note the password should be managed by a [Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html) for a production environment).

```
[CRC]
console.redhat.com

[CRC:vars]
ansible_connection=ansible.netcommon.httpapi
ansible_network_os=maxamillion.fleetmanager.consoledot
ansible_httpapi_use_ssl=yes
ansible_httpapi_validate_certs=yes
ansible_httpapi_consoledot_offline_token="MY_RED_HAT_API_OFFLINE_TOKEN_HERE"
```


### Using the modules with Fully Qualified Collection Name (FQCN)

With [Ansible
Collections](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
there are various ways to utilize them either by calling specific Content from
the Collection, such as a module, by its Fully Qualified Collection Name (FQCN)
as we'll show in this example or by defining a Collection Search Path as the
examples below will display.

```
---
- name: Get a list of Edge Images
  hosts: CRC
  gather_facts: false
  tasks:
    - name: get image info
      maxamillion.fleetmanager.images_info:
			register: images_info_out
		- debug: var=images_info_out
```

### Directory Structure

* `docs/`: local documentation for the collection
* `license.txt`: optional copy of license(s) for this collection
* `galaxy.yml`: source data for the MANIFEST.json that will be part of the collection package
* `playbooks/`: playbooks reside here
  * `tasks/`: this holds 'task list files' for `include_tasks`/`import_tasks` usage
* `plugins/`: all ansible plugins and modules go here, each in its own subdir
  * `modules/`: ansible modules
  * `lookups/`: lookup plugins
  * `filters/`: Jinja2 filter plugins
  * ... rest of plugins
* `README.md`: information file (this file)
* `roles/`: directory for ansible roles
* `tests/`: tests for the collection's content

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Red Hat Edge Manager collection repository](https://github.com/maxamillion/maxamillion.fleetmanager/issues). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.


See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.

### Code of Conduct
This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Changelogs
<!--Add a link to a changelog.md file or an external docsite to cover this information. -->

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

MIT

See [LICENSE](https://mit-license.org/) to see the full text.

## Dependencies

This collection relies on the [`ansible.netcommon`](https://github.com/ansible-collections/ansible.netcommon) collection, so if you're using [`ansible-core`](https://github.com/ansible/ansible) and not [`ansible`](https://pypi.org/project/ansible/) then you will need to run the following command:

     $ ansible-galaxy install -r requirements.yml

## Hacking

To use this while developing, run the following commands from within your local checkout to this git repo in order to symlink this git repo to the appropriate Ansible Collection path

		$ mkdir -p ~/.ansible/collections/ansible_collections/maxamillion
		$ ln -s $(pwd) ~/.ansible/collections/ansible_collections/maxamillion/fleetmanager


Make sure to set the proxy vars on the command line or in your shell environment if needed:

		$ HTTP_PROXY=http://proxy.foo.com:3128 HTTPS_PROXY=http://proxy.foo.com:3128 ansible-playbook myplaybook.yml -i myinventory.ini
