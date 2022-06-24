# Ansible Collection - maxamillion.fleetmanager

PoC Collection for the Red Hat Edge Fleet Manager

## Hacking

To use this while developing, run the following commands from within your local checkout to this git repo in order to symlink this git repo to the appropriate Ansible Collection path

		$ mkdir -p ~/.ansible/collections/ansible_collections/maxamillion
		$ ln -s $(pwd) ~/.ansible/collections/ansible_collections/maxamillion/fleetmanager


Make sure to set the proxy vars on the command line if needed:

		$ HTTP_PROXY=http://proxy.foo.com:3128 HTTPS_PROXY=http://proxy.foo.com:3128 ansible-playbook myplaybook.yml -i myinventory.ini
