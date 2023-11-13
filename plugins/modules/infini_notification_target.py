#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module creates, deletes or modifies metadata on Infinibox."""

# Copyright: (c) 2023, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_notification_target
version_added: '2.13.12'
short_description:  Config notification target
description:
    - This module config notification targets on Infinibox
author: Wei Wang
options:
  name:
    description:
      - Name of the target
    required: true
  event_level:
    description:
      - Event levels
    required: false
  include_events:
    description:
      - Included events
    required: false
  exclude_events:
    description:
      - Exclued events
    required: false
  target_parameters:
    description:
      -
    required: false
  recipients:
    description:
    required: true
  state: "present"
    description:
    required: true

  config_group:
    description:
      - Config group
    required: true
    choices: = [
        "core",
        "ip_config",
        "iscsi",
        "limits",
        "mgmt",
        "ndoe_interfaces",
        "overriders",
        "security",
        "ssh",
    ]
  key:
    description:
      - Name of the config
    required: true
  value:
    description:
      - Value of the metadata key
    required: false

  state:
    description:
      - Query or modifies config when.
    required: false
    default: present
    choices: [ "stat", "present" ]

extends_documentation_fragment:
    - infinibox
"""

EXAMPLES = r"""
- name: Create new metadata key foo with value bar
  infini_metadata:
    config_group: mgmt
    key: pool.compression_enabled_default
    state: present
    value: true
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

import json
import traceback

HAS_ARROW = True
try:
    import arrow
except ImportError:
    HAS_ARROW = False

from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
    HAS_INFINISDK,
    api_wrapper,
    infinibox_argument_spec,
    get_system,
    get_user,
    get_pool,
    unixMillisecondsToDate,
    merge_two_dicts,
)

try:
    from infi.dtypes.iqn import make_iscsi_name
except ImportError:
    pass  # Handled by HAS_INFINISDK from module_utils



@api_wrapper
def get_target(module, disable_fail=False):
    """
    Find and return config setting value
    Use disable_fail when we are looking for config
    and it may or may not exist and neither case is an error.
    """
    pass

def handle_stat(module):
    """Return config stat"""

    system = get_system(module)
    name = module.params["name"]
    changed = False
    if not module.check_mode:
        targets = get_targets(module,system)
        update_target(module)
        msg = "Targets recived".format(name)
    module.exit_json(changed=False, msg=msg)



@api_wrapper
def get_targets(module, disable_fail=False):
    """
    Get all targets
    """

    system = get_system(module)
    path = f"notifications/targets"
    targets = system.api.get(path=path)



@api_wrapper
def find_target_id(module, system):
    """
    Find the ID of the target by name
    """
    target_name = module.params["name"]
    path = "notifications/targets?name={0}&fields=id".format(target_name)
    api_result = system.api.get(
        path=path
    )
    if len(api_result.get_json()['result']) > 0:
        result = api_result.get_json()['result'][0]
        target_id = result['id']
    else:
        target_id=None
    return target_id


@api_wrapper
def delete_target(module, disable_fail=False):
    """
    Delete a notification target
    """

    system = get_system(module)
    name = module.params["name"]
    target_id = find_target_id(module,system)


    path = f"notifications/targets/{target_id}?approved=true"
    system.api.delete(path=path)


@api_wrapper
def create_target(module, disable_fail=False):
    """
    Create a new notifition target
    """

    system = get_system(module)
    name = module.params["name"]
    protocol = module.params["protocol"]
    host = module.params["host"]
    port = module.params["port"]
    facility = module.params["facility"]
    transport = module.params["transport"]
    post_test = module.params["post_test"]
    visibility = module.params["visibility"]


    path = f"notifications/targets"

    json_data = {
        "name": name,
        "protocol":  protocol,
        "host": host,
        "port": port,
        "facility": facility,
        "transport": transport,
        "visibility": visibility
    }

    system.api.post(path=path, data=json_data)

    if post_test:
        target_id = find_target_id(module, system)
        path = "notifications/targets/{}/test".format(target_id)
        json_data = {}
        system.api.post(path=path, data=json_data)


@api_wrapper
def update_target(module, disable_fail=False):
    """
    Update an existing target.
    Note: due to the target update api do not support more than one
          field at one time, deleting the existing target is too dangerous.
          we are not going to support this function
    """

    pass

    # system = get_system(module)
    # name = module.params["name"]
    # protocol = module.params["protocol"]
    # host = module.params["host"]
    # port = module.params["port"]
    # facility = module.params["facility"]
    # transport = module.params["transport"]
    # visibility = module.params["visibility"]
    # target_id = find_target_id(module,system)
    # path = f"notifications/targets/{target_id}"
    # json_data = {
    #     "name": name,
    #     "protocol":  protocol,
    #     "host": host,
    #     "port": port,
    #     "facility": facility,
    #     "transport": transport,
    #     "visibility": visibility
    # }
    # system.api.put(path=path, data=json_data)



def handle_present(module):
    """Make config present"""

    system = get_system(module)
    name = module.params["name"]
    changed = False
    if not module.check_mode:
        target_id = find_target_id(module,system)
        if not target_id:
            create_target(module)
            changed=True
            msg = "Target {} created".format(name)
            module.exit_json(changed=changed, msg=msg)
        else:
            msg = "Target {} already exist".format(name)
            module.fail_json(msg=msg)




def handle_absent(module):
    """Make config present"""
    changed = False
    name = module.params["name"]
    system = get_system(module)
    target_id = find_target_id(module,system)

    if not target_id:
        msg="Target of {0} does not exist, deletion operation skipped.".format(name)
        changed = False
    else:
        msg="Target {0} has been deleted".format(name)
        changed = True
        if not module.check_mode:
            delete_target(module)

    module.exit_json(changed=changed, msg=msg)


def execute_state(module):
    """Determine which state function to execute and do so"""
    state = module.params["state"]
    try:
        if state == "stat":
            handle_stat(module)
        elif state == "present":
            handle_present(module)
        elif state == "absent":
            handle_absent(module)
        else:
            module.fail_json(msg=f"Internal handler error. Invalid state: {state}")
    finally:
        system = get_system(module)
        system.logout()




def check_options(module):
    """Verify module options are sane"""
    pass


def main():
    """Main module function"""
    argument_spec = infinibox_argument_spec()

    argument_spec.update(
        {
            "name": {"required": False},
            "host": {"required": False, "type": str},
            "port": {"required": False, "type": int},
            "transport": {"required": False, "type": str},
            "protocol": {"required": False, "default": "SYSLOG", "type": str},
            "facility": {"required": False, "default": "LOCAL7", "type": str},
            "visibility": {"required": False, "default": "CUSTOMER", "type": str},
            "post_test": {"required": False, "default": True, "type": bool},
            "state": {"default": "present", "choices": ["stat", "present", "absent"]},
        }
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib("infinisdk"))

    if not HAS_ARROW:
        module.fail_json(msg=missing_required_lib("arrow"))

    check_options(module)
    execute_state(module)


if __name__ == '__main__':
     main()
