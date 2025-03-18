#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import requests
import os

def write_log(log_file, module, message):
    with open(log_file, 'a') as f:
        f.write(message + '\n')
    module.log(message)

def main():
    module_args = dict(
        account_id=dict(type='str', required=True),
        api_token=dict(type='str', required=True, no_log=True),
        tunnel_name=dict(type='str', required=True),
        private_service=dict(type='str', required=True),
        public_hostname=dict(type='str', required=True),
        zone_id=dict(type='str', required=True),
        log_file=dict(type='str', required=False, default='/tmp/mkh_ensure_fcd_tunnel.log')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    account_id = module.params['account_id']
    api_token = module.params['api_token']
    tunnel_name = module.params['tunnel_name']
    private_service = module.params['private_service']
    public_hostname = module.params['public_hostname']
    zone_id = module.params['zone_id']
    log_file = module.params['log_file']

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        write_log(log_file, module, "Fetching Cloudflare tunnels...")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel"
        method = "GET"
        write_log(log_file, module, "REQUEST:")
        write_log(log_file, module, f"{method} {url}")
        response = requests.get(
            url,
            headers=headers
        )
        response.raise_for_status()
        write_log(log_file, module, "\nRESPONSE:")
        write_log(log_file, module, response.text)
        tunnels = response.json()
        write_log(log_file, module, f"Retrieved tunnels: {tunnels}")
    except requests.exceptions.RequestException as e:
        write_log(log_file, module, "\nRESPONSE:")
        write_log(log_file, module, str(e.response))
        module.fail_json(msg=f"Failed to fetch tunnels: {str(e)}")

    try:
        write_log(log_file, module, f"Searching for tunnel named {tunnel_name}...")
        target_tunnel = next((item for item in tunnels['result'] if item['name'] == tunnel_name), None)
        write_log(log_file, module, f"Target tunnel: {target_tunnel}")
    except Exception as e:
        module.fail_json(msg=f"Failed to find tunnel: {str(e)}")

    if not target_tunnel:
        try:
            write_log(log_file, module, f"Tunnel {tunnel_name} not found, creating new tunnel...")
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel"
            method = "POST"
            write_log(log_file, module, "REQUEST:")
            body = {
                "name": tunnel_name,
                "config_src": "local"
            }
            write_log(log_file, module, f"{method} {url}")
            write_log(log_file, module, str(body))
            create_tunnel_response = requests.post(
                url,
                headers=headers,
                json=body
            )
            create_tunnel_response.raise_for_status()
            write_log(log_file, module, "\nRESPONSE:")
            write_log(log_file, module, f"Response: {create_tunnel_response.text}")
            target_tunnel = create_tunnel_response.json()['result']
            write_log(log_file, module, f"Created new tunnel: {str(target_tunnel)}")
        except requests.exceptions.RequestException as e:
            write_log(log_file, module, "\nRESPONSE:")
            write_log(log_file, module, str(e.response))
            module.fail_json(msg=f"Failed to create tunnel: {str(e)}")

    tunnel_id = target_tunnel['id']
    dns_argotunnel = f"{tunnel_id}.cfargotunnel.com"
    write_log(log_file, module, f"Tunnel ID: {tunnel_id}")

    try:
        write_log(log_file, module, "Fetching tunnel configuration...")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations"
        method = "GET"
        write_log(log_file, module, "REQUEST:")
        write_log(log_file, module, f"{method} {url}")
        tunnel_config_response = requests.get(
            url,
            headers=headers
        )
        tunnel_config_response.raise_for_status()
        write_log(log_file, module, "\nRESPONSE:")
        write_log(log_file, module, f"Response: {tunnel_config_response.text}")
        tunnel_config = tunnel_config_response.json()
        write_log(log_file, module, f"Tunnel configuration: {str(tunnel_config)}")
    except requests.exceptions.RequestException as e:
        write_log(log_file, module, "\nRESPONSE:")
        write_log(log_file, module, str(e.response))
        module.fail_json(msg=f"Failed to fetch tunnel configuration: {str(e)}")

    try:
        write_log(log_file, module, "Checking if ingress exists...")
        if 'result' in tunnel_config and tunnel_config['result'] is not None and \
           'config' in tunnel_config['result'] and tunnel_config['result']['config'] is not None and \
           'ingress' in tunnel_config['result']['config']:
            ingress_exists = next((item for item in tunnel_config['result']['config']['ingress'] if item['service'] == private_service and item['hostname'] == public_hostname), None)
            write_log(log_file, module, f"Ingress exists: {str(ingress_exists)}")
        else:
            ingress_exists = None
            write_log(log_file, module, "Ingress configuration not found in tunnel configuration.")
    except Exception as e:
        module.fail_json(msg=f"Failed to check ingress: {str(e)}")

    if not ingress_exists:
        try:
            write_log(log_file, module, "Ingress does not exist, adding ingress configuration...")
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations"
            method = "PUT"
            write_log(log_file, module, "REQUEST:")
            write_log(log_file, module, f"{method} {url}")
            ingress_body = {
                "config": {
                    "ingress": [
                        item for item in tunnel_config['result']['config']['ingress']
                        if item['service'] != 'http_status:404'
                    ] + [
                        {
                            "service": private_service,
                            "hostname": public_hostname,
                            "originRequest": {}
                        },
                        {
                            "service": "http_status:404"
                        }
                    ]
                }
            }
            write_log(log_file, module, str(ingress_body))

            add_ingress_response = requests.put(
                url,
                headers=headers,
                json=ingress_body
            )
            add_ingress_response.raise_for_status()
            write_log(log_file, module, "\nRESPONSE:")
            write_log(log_file, module, f"Response: {add_ingress_response.text}")
            write_log(log_file, module, f"Added ingress configuration: {str(ingress_body)}")
        except requests.exceptions.RequestException as e:
            write_log(log_file, module, "\nRESPONSE:")
            write_log(log_file, module, str(e.response))
            module.fail_json(msg=f"Failed to add ingress configuration: {str(e)}")

    try:
        write_log(log_file, module, "Fetching DNS records...")
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        method = "GET"
        write_log(log_file, module, "REQUEST:")
        write_log(log_file, module, f"{method} {url}")
        dns_response = requests.get(
            url,
            headers=headers
        )
        dns_response.raise_for_status()
        write_log(log_file, module, "\nRESPONSE:")
        write_log(log_file, module, f"Response: {dns_response.text}")
        dns_records = dns_response.json()
        write_log(log_file, module, f"Retrieved DNS records: {dns_records}")
    except requests.exceptions.RequestException as e:
        write_log(log_file, module, "\nRESPONSE:")
        write_log(log_file, module, str(e.response))
        module.fail_json(msg=f"Failed to fetch DNS records: {str(e)}")

    try:
        write_log(log_file, module, f"Searching for DNS record named {public_hostname}...")
        target_dns_record = next((item for item in dns_records['result'] if item['name'] == public_hostname), None)
        write_log(log_file, module, f"Target DNS record: {target_dns_record}")
    except Exception as e:
        module.fail_json(msg=f"Failed to find DNS record: {str(e)}")

    if target_dns_record:
        dns_record_id = target_dns_record['id']
        write_log(log_file, module, f"DNS Record ID: {dns_record_id}")
        if target_dns_record['type'] != 'CNAME' or target_dns_record['content'] != dns_argotunnel:
            try:
                write_log(log_file, module, f"DNS record is not a CNAME pointing to {tunnel_id}.cfargotunnel.com, deleting DNS record...")
                url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
                method = "DELETE"
                write_log(log_file, module, "REQUEST:")
                write_log(log_file, module, f"{method} {url}")
                delete_dns_response = requests.delete(
                    url,
                    headers=headers
                )
                delete_dns_response.raise_for_status()
                write_log(log_file, module, "\nRESPONSE:")
                write_log(log_file, module, f"Response: {delete_dns_response.text}")
                write_log(log_file, module, f"Deleted DNS record: {dns_record_id}")
            except requests.exceptions.RequestException as e:
                write_log(log_file, module, "\nRESPONSE:")
                write_log(log_file, module, str(e.response))
                module.fail_json(msg=f"Failed to delete DNS record: {str(e)}")

    if not target_dns_record or (target_dns_record and (target_dns_record['type'] != 'CNAME' or target_dns_record['content'] != dns_argotunnel)):
        try:
            write_log(log_file, module, f"Creating DNS record for {public_hostname}...")
            url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            method = "POST"
            write_log(log_file, module, "REQUEST:")
            dns_body = {
                'type': 'CNAME',
                'name': public_hostname,
                'content': dns_argotunnel,
                'ttl': 1,
                'proxied': True
            }
            write_log(log_file, module, f"{method} {url}")
            write_log(log_file, module, str(dns_body))
            create_dns_response = requests.post(
                url,
                headers=headers,
                json=dns_body
            )
            create_dns_response.raise_for_status()
            write_log(log_file, module, "\nRESPONSE:")
            write_log(log_file, module, f"Response: {create_dns_response.text}")
            write_log(log_file, module, f"Created DNS record: {str(dns_body)}")
        except requests.exceptions.RequestException as e:
            write_log(log_file, module, "\nRESPONSE:")
            write_log(log_file, module, str(e.response))
            module.fail_json(msg=f"Failed to create DNS record: {str(e)}")

    module.exit_json(changed=True, tunnel_id=tunnel_id)


if __name__ == '__main__':
    main()
