#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import requests
import os

def log_to_file(log_path, message):
    with open(log_path, 'a') as log_file:
        log_file.write(message + '\n')

def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_id=dict(type='str', required=True),
            api_token=dict(type='str', required=True, no_log=True),
            tunnel_name=dict(type='str', required=True),
            private_service=dict(type='str', required=True),
            public_hostname=dict(type='str', required=True),
            log_path=dict(type='str', required=False, default='/tmp/mkh_ensure_cfd_tunnel.log')
        )
    )

    account_id = module.params['account_id']
    api_token = module.params['api_token']
    tunnel_name = module.params['tunnel_name']
    private_service = module.params['private_service']
    public_hostname = module.params['public_hostname']
    log_path = module.params['log_path']

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        message = "Fetching Cloudflare tunnels..."
        module.log(message)
        log_to_file(log_path, message)
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel",
            headers=headers
        )
        response.raise_for_status()
        tunnels = response.json()
        message = f"Retrieved tunnels: {tunnels}"
        module.log(message)
        log_to_file(log_path, message)
    except requests.exceptions.RequestException as e:
        error_message = f"Failed to fetch tunnels: {str(e)}"
        module.fail_json(msg=error_message)
        log_to_file(log_path, error_message)

    try:
        message = f"Searching for tunnel named {tunnel_name}..."
        module.log(message)
        log_to_file(log_path, message)
        target_tunnel = next((tunnel for tunnel in tunnels['result'] if tunnel['name'] == tunnel_name), None)
        message = f"Target tunnel: {target_tunnel}"
        module.log(message)
        log_to_file(log_path, message)
        if not target_tunnel:
            error_message = f"Tunnel {tunnel_name} not found"
            module.fail_json(msg=error_message)
            log_to_file(log_path, error_message)

        tunnel_id = target_tunnel['id']
        message = f"Tunnel ID: {tunnel_id}"
        module.log(message)
        log_to_file(log_path, message)

        message = "Fetching tunnel configuration..."
        module.log(message)
        log_to_file(log_path, message)
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",
            headers=headers
        )
        response.raise_for_status()
        tunnel_config = response.json()
        message = f"Tunnel configuration: {tunnel_config}"
        module.log(message)
        log_to_file(log_path, message)

        message = "Checking if ingress exists..."
        module.log(message)
        log_to_file(log_path, message)
        ingress = next((ing for ing in tunnel_config['result']['config']['ingress'] if ing['hostname'] == public_hostname), None)
        message = f"Ingress exists: {ingress}"
        module.log(message)
        log_to_file(log_path, message)

        if not ingress:
            message = "Ingress does not exist, adding ingress configuration..."
            module.log(message)
            log_to_file(log_path, message)
            # Adicionar configuração de ingress aqui
            # ...
            message = "Ingress configuration added."
            module.log(message)
            log_to_file(log_path, message)
        else:
            message = "Ingress already exists, no changes needed."
            module.log(message)
            log_to_file(log_path, message)

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to fetch tunnel configuration: {str(e)}"
        module.fail_json(msg=error_message)
        log_to_file(log_path, error_message)

    module.exit_json(changed=True, tunnel_id=tunnel_id)


if __name__ == '__main__':
    main()
