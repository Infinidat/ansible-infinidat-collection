#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type
from infi.dtypes.iqn import make_iscsi_name


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = r"""
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
      - Set an MTU. If not specified, defaults to 1500 bytes.
    required: false
    type: int
    default: None
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
  rate_limit:
    description:
      - Specify the throughput limit per node. The limit is specified in Mbps, megabits per second (not megabytes). Note the limit affects NFS, iSCSI and async-replication traffic. It does not affect sync-replication or active-active traffic.
    required: false
    type: int

extends_documentation_fragment:
    - infinibox
"""

EXAMPLES = r"""
- name: Create new network space
  infini_network_space:
    name: iSCSI
    TBD
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from infinisdk.core.exceptions import APICommandFailed

try:
    # Import from collection (recommended)
    from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
        HAS_INFINISDK,
        api_wrapper,
        infinibox_argument_spec,
        get_system,
        unixMillisecondsToDate,
        merge_two_dicts,
        get_net_space,
    )
except ModuleNotFoundError:
    # Import from ansible clone (hacking only)
    from ansible.module_utils.infinibox import (
        HAS_INFINISDK,
        api_wrapper,
        infinibox_argument_spec,
        get_system,
        unixMillisecondsToDate,
        merge_two_dicts,
        get_net_space,
    )

# try:
#     # Import from collection (recommended)
#     from ansible_collections.infinidat.infinibox.plugins.module_utils.iboxbase import \
#         Config
# except ModuleNotFoundError:
#     # Import from ansible clone (hacking only)
#     from ansible.module_utils.iboxbase import \
#       Config

from infinisdk.core.exceptions import ObjectNotFound

@api_wrapper
def create_empty_network_space(module, system):
    # Create network space
    network_space_name = module.params["name"]
    service = module.params["service"]
    rate_limit = module.params["rate_limit"]
    mtu = module.params["mtu"]
    network_config = {
        "netmask": module.params["netmask"],
        "network": module.params["network"],
        "default_gateway": module.params["default_gateway"],
    }
    interfaces = module.params["interfaces"]

    print(f"Creating network space {network_space_name}")
    product_id = system.api.get('system/product_id')
    print(f"api: {product_id.get_result()}")

    net_create_url = "network/spaces"
    net_create_data = {
        "name": network_space_name,
        "service": service,
        "network_config": network_config,
        "interfaces": interfaces,
    }
    if rate_limit:
        net_create_data["rate_limit"] = rate_limit
    if mtu:
        net_create_data["mtu"] = mtu

    net_create = system.api.post(
        path=net_create_url,
        data=net_create_data
    )
    print(f"net_create: {net_create}")

@api_wrapper
def find_network_space_id(module, system):
    """
    Find the ID of this network space
    """
    network_space_name = module.params["name"]
    net_id_url = "network/spaces?name={}&fields=id".format(network_space_name)
    net_id = system.api.get(
        path=net_id_url
    )
    result = net_id.get_json()['result'][0]
    space_id = result['id']
    print(f"Network space has ID {space_id}")
    return space_id

@api_wrapper
def add_ips_to_network_space(module, system, space_id):
    network_space_name = module.params["name"]
    print(f"Adding IPs to network space {network_space_name}")

    ips = module.params["ips"]
    for ip in ips:
        ip_url = "network/spaces/{}/ips".format(space_id)
        ip_data = ip
        ip_add = system.api.post(
            path=ip_url,
            data=ip_data
        )
        print(f"add_ips json: {ip_add.get_json()}")
        result = ip_add.get_json()['result']
        print(f"add ip result: {result}")

@api_wrapper
def create_network_space(module, system):
    if not module.check_mode:
        # Create space
        create_empty_network_space(module, system)
        # Find space's ID
        space_id = find_network_space_id(module, system)
        # Add IPs to space
        add_ips_to_network_space(module, system, space_id)

        changed = True
    else:
        changed = False

    return changed

def update_network_space(module, system):
    """
    Update network space.
    TODO - This is incomplete and will not update the space.
    It will instead return changed=False and a message.
    To implement this we will need to find the existing space.
    For each field that we support updating, we need to compare existing
    to new values and if different update.  We will need to iterate
    over the settings or we will receive:
        Status: 400
        Code: NOT_SUPPORTED_MULTIPLE_UPDATE
    """
    changed = False
    msg = "Update is not supported yet"
    module.exit_json(changed=changed, msg=msg)

    # TODO Everything below is incomplete
    # Update network space
    network_space_name = module.params["name"]
    service = module.params["service"]
    network_config = {
        "netmask": module.params["netmask"],
        "network": module.params["network"],
        "default_gateway": module.params["default_gateway"],
    }
    interfaces = module.params["interfaces"]

    print(f"Updating network space {network_space_name}")

    # Find space's ID
    space_id = find_network_space_id(module, system)

    net_url = "network/spaces/{}".format(space_id)
    net_data = {
        "name": network_space_name,
        "service": service,
        "network_config": network_config,
        "interfaces": interfaces,
    }

    # Find existing space
    net_existing = system.api.get(path=path)

    net_update = system.api.put(
        path=net_url,
        data=net_data
    )
    print(f"net_update: {net_update}")


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
    return field_dict


def handle_stat(module):
    network_space_name = module.params["name"]
    system = get_system(module)
    net_space = get_net_space(module, system)

    if not net_space:
        module.fail_json(msg="Network space {0} not found".format(network_space_name))

    field_dict = get_network_space_fields(module, net_space)
    result = dict(
        changed=False, msg="Network space {0} stat found".format(network_space_name)
    )
    result = merge_two_dicts(result, field_dict)
    module.exit_json(**result)


def handle_present(module):
    """
    If it does not already exist, create namespace. Otherwise, update namespace.
    """
    network_space_name = module.params["name"]
    system = get_system(module)
    net_space = get_net_space(module, system)
    if net_space:
        changed = update_network_space(module, net_space)
        msg = "Host {0} updated".format(network_space_name)
    else:
        changed = create_network_space(module, system)
        msg = "Network space {0} created".format(network_space_name)
    module.exit_json(changed=changed, msg=msg)


def handle_absent(module):
    """
    Remove a namespace. First, may disable and remove the namespace's IPs.
    """
    network_space_name = module.params["name"]
    system = get_system(module)
    network_space = get_net_space(module, system)
    if not network_space:
        changed = False
        msg = "Network space {0} already absent".format(network_space_name)
    else:
        # Find IPs from space
        ips = [ip for ip in network_space.get_ips()]

        # Disable and delete IPs from space
        if not module.check_mode:
            for ip in ips:
                addr = ip["ip_address"]

                print(f"Disabling IP {addr}")
                try:
                    network_space.disable_ip_address(addr)
                except APICommandFailed as err:
                    if err.error_code == "IP_ADDRESS_ALREADY_DISABLED":
                        print(f"Already disabled IP {addr}")
                    else:
                        print(f"Failed to disable IP {addr}")
                        network.fail_json(
                            msg="Disabling of network space {} IP {} failed".format(
                                network_space_name, addr
                            )
                        )

                print(f"Removing IP {addr}")
                try:
                    network_space.remove_ip_address(addr)
                except:
                    network.fail_json(
                        msg="Removal of network space {} IP {} failed".format(
                            network_space_name, addr
                        )
                    )

            # Delete space
            network_space.delete()
            changed = True
            msg = "Network space {0} removed".format(network_space_name)
        else:
            changed = False
            msg = "Network space {0} not altered due to checkmode".format(
                network_space_name
            )

    module.exit_json(changed=changed, msg=msg)


def execute_state(module):
    state = module.params["state"]
    try:
        if state == "stat":
            handle_stat(module)
        elif state == "present":
            handle_present(module)
        elif state == "absent":
            handle_absent(module)
        else:
            module.fail_json(
                msg="Internal handler error. Invalid state: {0}".format(state)
            )
    finally:
        system = get_system(module)
        system.logout()


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            state=dict(
                default="present", required=False, choices=["stat", "present", "absent"]
            ),
            service=dict(
                default="replication",
                required=False,
                choices=["replication", "NAS_SERVICE", "ISCSI_SERVICE"],
            ),
            mtu=dict(default=None, required=False, type=int),
            network=dict(default=None, required=False),
            netmask=dict(default=None, required=False, type=int),
            default_gateway=dict(default=None, required=False),
            interfaces=dict(default=list(), required=False, type=list),
            network_config=dict(default=dict(), required=False, type=dict),
            ips=dict(default=list(), required=False, type=list),
            rate_limit=dict(default=None, required=False, type=int),
        )
        # required_one_of = [["var_1", "var_2"]]
        # mutually_exclusive = [["var_3", "var_4"]]
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib("infinisdk"))

    execute_state(module)


if __name__ == "__main__":
    main()
