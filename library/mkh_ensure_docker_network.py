#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json

def network_exists(name):
    result = subprocess.run(['docker', 'network', 'ls', '--format', '{{.Name}}'], capture_output=True, text=True)
    networks = result.stdout.splitlines()
    return name in networks

def create_network(name, driver, subnet, gateway, ip_range, aux_address, options):
    cmd = ['docker', 'network', 'create']
    if driver:
        cmd.extend(['--driver', driver])
    if subnet:
        cmd.extend(['--subnet', subnet])
    if gateway:
        cmd.extend(['--gateway', gateway])
    if ip_range:
        cmd.extend(['--ip-range', ip_range])
    if aux_address:
        for key, value in aux_address.items():
            cmd.extend(['--aux-address', f'{key}={value}'])
    if options:
        for key, value in options.items():
            cmd.extend(['-o', f'{key}={value}'])
    cmd.append(name)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def main():
    module_args = dict(
        networks=dict(type='list', elements='dict', options=dict(
            name=dict(type='str', required=True),
            driver=dict(type='str', required=False, default=None),
            subnet=dict(type='str', required=False, default=None),
            gateway=dict(type='str', required=False, default=None),
            ip_range=dict(type='str', required=False, default=None),
            aux_address=dict(type='dict', required=False, default=None),
            options=dict(type='dict', required=False, default=None)
        ))
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    networks = module.params['networks']
    results = []

    for net in networks:
        name = net['name']
        driver = net.get('driver')
        subnet = net.get('subnet')
        gateway = net.get('gateway')
        ip_range = net.get('ip_range')
        aux_address = net.get('aux_address')
        options = net.get('options')

        if network_exists(name):
            results.append({
                'name': name,
                'changed': False,
                'msg': f'Network {name} already exists'
            })
        else:
            success, stdout, stderr = create_network(name, driver, subnet, gateway, ip_range, aux_address, options)
            if success:
                results.append({
                    'name': name,
                    'changed': True,
                    'msg': f'Network {name} created successfully',
                    'stdout': stdout,
                    'stderr': stderr
                })
            else:
                module.fail_json(msg=f'Failed to create network {name}', stdout=stdout, stderr=stderr)

    module.exit_json(changed=any(result['changed'] for result in results), results=results)

if __name__ == '__main__':
    main()
