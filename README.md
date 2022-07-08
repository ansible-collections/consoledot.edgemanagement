# Ansible Collection - maxamillion.fleetmanager

PoC Collection for the Red Hat Edge Fleet Manager

## Dependencies

This collection relies on the [`ansible.netcommon`](https://github.com/ansible-collections/ansible.netcommon) collection, so if you're using [`ansible-core`](https://github.com/ansible/ansible) and not [`ansible`](https://pypi.org/project/ansible/) then you will need to run the following command:

     $ ansible-galaxy install -r requirements.yml

## Hacking

To use this while developing, run the following commands from within your local checkout to this git repo in order to symlink this git repo to the appropriate Ansible Collection path

		$ mkdir -p ~/.ansible/collections/ansible_collections/maxamillion
		$ ln -s $(pwd) ~/.ansible/collections/ansible_collections/maxamillion/fleetmanager


Make sure to set the proxy vars on the command line if needed:

		$ HTTP_PROXY=http://proxy.foo.com:3128 HTTPS_PROXY=http://proxy.foo.com:3128 ansible-playbook myplaybook.yml -i myinventory.ini
