#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import requests

def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_id=dict(type='str', required=True),
            api_token=dict(type='str', required=True, no_log=True),
            tunnel_name=dict(type='str', required=True),
            private_service=dict(type='str', required=True),
            public_hostname=dict(type='str', required=True),
        )
    )

    account_id = module.params['account_id']
    api_token = module.params['api_token']
    tunnel_name = module.params['tunnel_name']
    private_service = module.params['private_service']
    public_hostname = module.params['public_hostname']

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        module.log("Fetching Cloudflare tunnels...")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel"
        method = "GET"
        module.log("REQUEST:")
        module.log(f"{method} {url}")
        response = requests.get(
            url,
            headers=headers
        )
        response.raise_for_status()
        module.log("\nRESPONSE:")
        module.log(f"Response: {response.text}")
        tunnels = response.json()
        module.log(f"Retrieved tunnels: {tunnels}")
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to fetch tunnels: {str(e)}")

    try:
        module.log(f"Searching for tunnel named {tunnel_name}...")
        target_tunnel = next((item for item in tunnels['result'] if item['name'] == tunnel_name), None)
        module.log(f"Target tunnel: {target_tunnel}")
    except Exception as e:
        module.fail_json(msg=f"Failed to find tunnel: {str(e)}")

    if not target_tunnel:
        try:
            module.log(f"Tunnel {tunnel_name} not found, creating new tunnel...")
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel",
            method = "POST"
            module.log("REQUEST:")
            body={
                    "name": tunnel_name,
                    "config_src": "local"
                }
            module.log(f"{method} {url}")
            module.log(body)
            create_tunnel_response = requests.post(
                url,
                headers=headers,
                json=body
            )
            create_tunnel_response.raise_for_status()
            module.log("\nRESPONSE:")
            module.log(f"Response: {response.text}")
            target_tunnel = create_tunnel_response.json()['result']
            module.log(f"Created new tunnel: {target_tunnel}")
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to create tunnel: {str(e)}")

    tunnel_id = target_tunnel['id']
    module.log(f"Tunnel ID: {tunnel_id}")

    try:
        module.log("Fetching tunnel configuration...")
        tunnel_config_response = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",
            headers=headers
        )
        tunnel_config_response.raise_for_status()
        tunnel_config = tunnel_config_response.json()
        module.log(f"Tunnel configuration: {tunnel_config}")
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to fetch tunnel configuration: {str(e)}")

    try:
        module.log("Checking if ingress exists...")
        ingress_exists = next((item for item in tunnel_config['result']['config']['ingress'] if item['service'] == private_service and item['hostname'] == public_hostname), None)
        module.log(f"Ingress exists: {ingress_exists}")
    except Exception as e:
        module.fail_json(msg=f"Failed to check ingress: {str(e)}")

    if not ingress_exists:
        try:
            module.log("Ingress does not exist, adding ingress configuration...")
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
            module.log(f"Added ingress configuration: {ingress_body}")
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to add ingress configuration: {str(e)}")

    module.exit_json(changed=True, tunnel_id=tunnel_id)


if __name__ == '__main__':
    main()
