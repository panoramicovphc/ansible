# MK-House Ansible Playbooks

This repository contains Ansible playbooks for setting up and managing the infrastructure of a homelab environment. The project is part of a broader Infrastructure as Code (IaC) initiative aimed at automating the deployment and management of various services and applications.

## Overview

The playbooks in this repository are designed to:

- Set up the Ansible runtime environment.
- Install necessary dependencies for Ansible.
- Propagate the Ansible project to remote nodes.

## Playbooks

### setup_ansible_runtime.yml

This playbook sets up the Ansible runtime environment by:

- Ensuring the setup script is executable.
- Removing old log files.
- Executing the setup script.
- Printing the output and error logs.

### setup_ansible_dependencies.yml

This playbook installs necessary dependencies for Ansible on both Debian-based and Red Hat-based systems.

### propagate_ansible_project.yml

This playbook propagates the Ansible project to remote nodes by:

- Creating backups of the current project.
- Cleaning the destination directory.
- Copying the project files to the remote nodes.
- Setting appropriate permissions.

## Inventory

The `inventory/hosts.ini.template` file contains the inventory configuration for the Ansible playbooks. It uses environment variables for sensitive information.

### Indicating Structural Solutions

In the inventory file, you can specify which structural solutions (like RabbitMQ and Redis) will be served by each host using the `labels` attribute. This allows multiple solutions to share the same instance on a host. For example:

```ini
[prd]
tankian.mkh    ansible_user=${MKADMIN_LOGIN}   ansible_password=${MKADMIN_PASSWORD}   CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN_TANKIAN}    labels='[ "rabbitmq" ]'
trujillo.mkh   ansible_user=${MKADMIN_LOGIN}   ansible_password=${MKADMIN_PASSWORD}   CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN_TRUJILLO}   labels='[]'
chuck.mkh      ansible_user=${MKADMIN_LOGIN}   ansible_password=${MKADMIN_PASSWORD}   CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN_CHUCK}      labels='[]'
```

## GitHub Actions Workflow

The `.github/workflows/main.yml` file contains a GitHub Actions workflow for automating the deployment of the Ansible project. It includes steps for setting up the runtime environments, installing dependencies, and propagating the project.

## Usage

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/mk-house.git
    cd mk-house/ansible
    ```

2. Customize the `inventory/hosts.ini.template` file with your environment variables.

3. Run the playbooks using Ansible:

    ```bash
    ansible-playbook -i inventory/hosts.ini playbooks/setup_ansible_runtime.yml
    ansible-playbook -i inventory/hosts.ini playbooks/setup_ansible_dependencies.yml
    ansible-playbook -i inventory/hosts.ini playbooks/propagate_ansible_project.yml
    ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
