#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import os

def volume_exists(name):
    result = subprocess.run(['docker', 'volume', 'ls', '--format', '{{.Name}}'], capture_output=True, text=True)
    volumes = result.stdout.splitlines()
    return name in volumes

def get_volume_info(name):
    result = subprocess.run(['docker', 'volume', 'inspect', name], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)[0]

def create_volume(name, driver, driver_opts, labels):
    cmd = ['docker', 'volume', 'create']
    if driver:
        cmd.extend(['--driver', driver])
    if driver_opts:
        for key, value in driver_opts.items():
            cmd.extend(['--opt', f'{key}={value}'])
    if labels:
        for key, value in labels.items():
            cmd.extend(['--label', f'{key}={value}'])
    cmd.append(name)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def ensure_directory(path, permissions, puid, pgid):
    if not os.path.exists(path):
        os.makedirs(path)
    if permissions:
        os.chmod(path, int(permissions, 8))
    if puid and pgid:
        os.chown(path, int(puid), int(pgid))

def main():
    module_args = dict(
        volumes=dict(type='list', elements='dict', options=dict(
            name=dict(type='str', required=True),
            driver=dict(type='str', required=False, default='local'),
            driver_opts=dict(type='dict', required=False, default=None),
            labels=dict(type='dict', required=False, default=None),
            device=dict(type='dict', required=False, default=None)
        ))
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    volumes = module.params['volumes']
    results = []

    for vol in volumes:
        name = vol['name']
        driver = vol.get('driver')
        driver_opts = vol.get('driver_opts')
        labels = vol.get('labels')
        device = vol.get('device')

        if module.check_mode:
            results.append({'name': name, 'changed': False})
            continue

        if volume_exists(name):
            volume_info = get_volume_info(name)
            if volume_info:
                current_driver = volume_info['Driver']
                current_opts = volume_info['Options']
                current_labels = volume_info['Labels']

                if driver and driver != current_driver:
                    module.fail_json(msg=f"Volume {name} exists but driver differs")
                if driver_opts:
                    for key, value in driver_opts.items():
                        if key not in current_opts or current_opts[key] != value:
                            module.fail_json(msg=f"Volume {name} exists but driver option {key} differs")
                if labels:
                    for key, value in labels.items():
                        if key not in current_labels or current_labels[key] != value:
                            module.fail_json(msg=f"Volume {name} exists but label {key} differs")

                results.append({'name': name, 'changed': False, 'msg': f"Volume {name} already exists with the same configuration"})
                continue

        if device:
            path = device.get('path')
            permissions = device.get('permissions')
            puid = device.get('puid')
            pgid = device.get('pgid')
            if path:
                ensure_directory(path, permissions, puid, pgid)
                if driver_opts is None:
                    driver_opts = {}
                driver_opts['device'] = path
                driver_opts['o'] = 'bind'
                driver_opts['type'] = 'none'

        changed, stdout, stderr = create_volume(name, driver, driver_opts, labels)
        if changed:
            results.append({'name': name, 'changed': True, 'msg': f"Volume {name} created", 'stdout': stdout})
        else:
            module.fail_json(msg=f"Failed to create volume {name}", stderr=stderr)

    module.exit_json(changed=any(result['changed'] for result in results), results=results)

if __name__ == '__main__':
    main()
