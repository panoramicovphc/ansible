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
        target_tunnel = next((item for item in tunnels['result'] if item['name'] == tunnel_name), None)
        message = f"Target tunnel: {target_tunnel}"
        module.log(message)
        log_to_file(log_path, message)
    except Exception as e:
        error_message = f"Failed to find tunnel: {str(e)}"
        module.fail_json(msg=error_message)
        log_to_file(log_path, error_message)

    if not target_tunnel:
        try:
            message = f"Tunnel {tunnel_name} not found, creating new tunnel..."
            module.log(message)
            log_to_file(log_path, message)
            create_tunnel_response = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel",
                headers=headers,
                json={
                    "name": tunnel_name,
                    "config_src": "local"
                }
            )
            create_tunnel_response.raise_for_status()
            target_tunnel = create_tunnel_response.json()['result']
            message = f"Created new tunnel: {target_tunnel}"
            module.log(message)
            log_to_file(log_path, message)
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to create tunnel: {str(e)}"
            module.fail_json(msg=error_message)
            log_to_file(log_path, error_message)

    tunnel_id = target_tunnel['id']
    message = f"Tunnel ID: {tunnel_id}"
    module.log(message)
    log_to_file(log_path, message)

    try:
        message = "Fetching tunnel configuration..."
        module.log(message)
        log_to_file(log_path, message)
        tunnel_config_response = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",
            headers=headers
        )
        tunnel_config_response.raise_for_status()
        tunnel_config = tunnel_config_response.json()
        message = f"Tunnel configuration: {tunnel_config}"
        module.log(message)
        log_to_file(log_path, message)
    except requests.exceptions.RequestException as e:
        error_message = f"Failed to fetch tunnel configuration: {str(e)}"
        module.fail_json(msg=error_message)
        log_to_file(log_path, error_message)

    try:
        message = "Checking if ingress exists..."
        module.log(message)
        log_to_file(log_path, message)
        ingress_exists = next((item for item in tunnel_config['result']['config']['ingress'] if item['service'] == private_service and item['hostname'] == public_hostname), None)
        message = f"Ingress exists: {ingress_exists}"
        module.log(message)
        log_to_file(log_path, message)
    except Exception as e:
        error_message = f"Failed to check ingress: {str(e)}"
        module.fail_json(msg=error_message)
        log_to_file(log_path, error_message)

    if not ingress_exists:
        try:
            message = "Ingress does not exist, adding ingress configuration..."
            module.log(message)
            log_to_file(log_path, message)
            ingress_body = {
                "config": {
                    "ingress": tunnel_config['result']['config']['ingress'] + [
                        {
                            "service": private_service,
                            "hostname": public_hostname
                        },
                        {
                            "service": "http_status:404"
                        }
                    ]
                }
            }

            add_ingress_response = requests.put(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",
                headers=headers,
                json=ingress_body
            )
            add_ingress_response.raise_for_status()
            message = f"Added ingress configuration: {ingress_body}"
            module.log(message)
            log_to_file(log_path, message)
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to add ingress configuration: {str(e)}"
            module.fail_json(msg=error_message)
            log_to_file(log_path, error_message)

    module.exit_json(changed=True, tunnel_id=tunnel_id)


if __name__ == '__main__':
    main()
