#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from infi.dtypes.iqn import make_iscsi_name


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: infini_network_space
version_added: 2.12.4
short_description: Create, Delete and Modify network spaces on Infinibox
description:
    - This module creates, deletes or modifies network spaces on Infinibox.
author: David Ohlemacher (@ohlemacher)
options:
  name:
    description:
      - Network space name
    required: true
  state:
    description:
      - Creates/Modifies network spaces when present. Removes when absent. Shows status when stat.
    required: false
    default: present
    choices: [ "stat", "present", "absent" ]
  service:
    description:
      - Choose a service.
    required: false
    default: "replication"
    choices: ["replication", "NAS", "iSCSI"]
  mtu:
    description:
      - Set an MTU.
    required: false
    type: int
    default: 1500
  network:
    description:
      - Starting IP address.
    required: false
    default: None
    type: string
  netmask:
    description:
      - Network mask.
    required: false
    default: None
    type: int
  ip_list:
    description:
      - List of IPs.
    required: false
    default: []
    type: list(int)
extends_documentation_fragment:
    - infinibox
'''

EXAMPLES = r'''
- name: Create new network space
  infini_network_space:
    name: iSCSI
    TBD
    user: admin
    password: secret
    system: ibox001
'''

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    # Import from collection (recommended)
    from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import \
        HAS_INFINISDK, api_wrapper, infinibox_argument_spec, \
        get_system, unixMillisecondsToDate, merge_two_dicts, \
        get_net_space
except ModuleNotFoundError:
    # Import from ansible clone (hacking only)
    from ansible.module_utils.infinibox import \
        HAS_INFINISDK, api_wrapper, infinibox_argument_spec, \
        get_system, unixMillisecondsToDate, merge_two_dicts, \
        get_net_space

from infinisdk.core.exceptions import ObjectNotFound

@api_wrapper
def create_network_space(module, system):
    changed = True
    if not module.check_mode:
        #breakpoint()
        network_space = system.network_spaces.create(
            name=module.params['name'],
            interfaces=module.params['interfaces'],
            service=module.params['service'],
            mtu=module.params['mtu'],
            network_config={
                "netmask": module.params['netmask'],
                "network": module.params['network'],
                "default_gateway": module.params['default_gateway'],
            }
        )
    return changed

@api_wrapper
def update_network_space(module, network_space):
    changed = False
    new_ips = module.params["ips"]
    current_ips = get_network_space_fields(module, network_space)["ips"]
    module.fail_json(msg=f"current_ips: {current_ips}")
    if new_ips != current_ips:
        network_space.update_field("ips", new_ips)
        changed = True
    return changed

@api_wrapper
def delete_network_space(module, network_space):
    changed = True
    if not module.check_mode:
        # May raise APICommandFailed
        network_space.delete()
    return changed


def get_network_space_fields(module, network_space):
    fields = network_space.get_fields(from_cache=True, raw_value=True)

    field_dict = dict(
        name=fields["name"],
        network_space_id=fields["id"],
        netmask=fields["network_config"]["netmask"],
        network=fields["network_config"]["network"],
        default_gateway=fields["network_config"]["default_gateway"],
        interface_ids=fields["interfaces"],
        service=fields["service"],
        ips=fields["ips"],
        properties=fields["properties"],
        automatic_ip_failback=fields["automatic_ip_failback"],
        mtu=fields["mtu"],
        rate_limit=fields["rate_limit"],
    )
    # module.fail_json(msg=f"fields: {fields}, ===================== field_dict: {field_dict}")
    return field_dict


def handle_stat(module):
    network_space_name = module.params["name"]
    system = get_system(module)
    net_space = get_net_space(module, system)

    if not net_space:
        module.fail_json(msg='Network space {0} not found'.format(network_space_name))

    field_dict = get_network_space_fields(module, net_space)
    result = dict(
        changed=False,
        msg='Network space {0} stat found'.format(network_space_name)
    )
    result = merge_two_dicts(result, field_dict)
    module.exit_json(**result)


def handle_present(module):
    network_space_name = module.params["name"]
    system = get_system(module)
    net_space = get_net_space(module, system)
    if net_space:
        changed = update_network_space(module, net_space)
        msg='Host {0} updated'.format(network_space_name)
    else:
        changed = create_network_space(module, system)
        msg='Network space {0} created'.format(network_space_name)
    module.exit_json(changed=changed, msg=msg)


def handle_absent(module):
    system, host = get_sys_host(module)
    host_name = module.params["name"]
    if not host:
        msg="Host {0} already absent".format(host_name)
        module.exit_json(changed=False, msg=msg)
    else:
        changed = delete_host(module, host)
        msg="Host {0} removed".format(host_name)
        module.exit_json(changed=changed, msg=msg)


def execute_state(module):
    state = module.params['state']
    try:
        if state == 'stat':
            handle_stat(module)
        elif state == 'present':
            handle_present(module)
        elif state == 'absent':
            handle_absent(module)
        else:
            module.fail_json(msg='Internal handler error. Invalid state: {0}'.format(state))
    finally:
        system = get_system(module)
        system.logout()


def main():
    #breakpoint()
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            state=dict(default='present', required=False, choices=['stat', 'present', 'absent']),
            service=dict(default='replication', required=False, choices=['replication', 'NAS_SERVICE', 'ISCSI_SERVICE']),
            mtu=dict(default=1500, required=False, type=int),
            network=dict(default=None, required=False),
            netmask=dict(default=None, required=False, type=int),
            default_gateway=dict(default=None, required=False),
            interfaces=dict(default=list(), required=False, type=list), # aliases=['ips'])
            network_config=dict(default=dict(), required=False, type=dict),
        )
        # required_one_of = [["var_1", "var_2"]]
        # mutually_exclusive = [["var_3", "var_4"]]
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib('infinisdk'))

    execute_state(module)


if __name__ == '__main__':
    main()
