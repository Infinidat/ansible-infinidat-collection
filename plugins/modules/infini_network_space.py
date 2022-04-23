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
from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import \
    HAS_INFINISDK, api_wrapper, infinibox_argument_spec, \
    get_system, unixMillisecondsToDate, merge_two_dicts, \
    get_net_space

@api_wrapper
def create_host(module, system):

    changed = True

    if not module.check_mode:
        host = system.hosts.create(name=module.params['name'])
    return changed

@api_wrapper
def update_host(module, host):
    changed = False
    return changed

@api_wrapper
def delete_host(module, host):
    changed = True
    if not module.check_mode:
        # May raise APICommandFailed if mapped, etc.
        host.delete()
    return changed


def get_net_space_fields(module, net_space):
    fields = net_space.get_fields(from_cache=True, raw_value=True)

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
    net_space_name = module.params["name"]
    system = get_system(module)
    net_space = get_net_space(module, system)

    if not net_space:
        module.fail_json(msg='Network space {0} not found'.format(net_space_name))

    field_dict = get_net_space_fields(module, net_space)
    result = dict(
        changed=False,
        msg='Network space {0} stat found'.format(net_space_name)
    )
    result = merge_two_dicts(result, field_dict)
    module.exit_json(**result)


def handle_present(module):
    system, host = get_sys_host(module)
    host_name = module.params["name"]
    if not host:
        changed = create_host(module, system)
        msg='Host {0} created'.format(host_name)
        module.exit_json(changed=changed, msg=msg)
    else:
        changed = update_host(module, host)
        msg='Host {0} updated'.format(host_name)
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
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            state=dict(default='present', required=False, choices=['stat', 'present', 'absent']),
            service=dict(default='replication', required=False, choices=['replication', 'NAS', 'iSCSI']),
            mtu=dict(default=1500, required=False, type=int),
            network=dict(default=None, required=False),
            netmask=dict(default=None, required=False),
            interfaces=dict(default=list(), required=False, type=list, aliases=['ips'])
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
