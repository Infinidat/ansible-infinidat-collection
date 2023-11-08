#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module creates, deletes or modifies metadata on Infinibox."""

# Copyright: (c) 2023, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_config
version_added: '2.13.12'
short_description:  Modify config on Infinibox
description:
    - This module modifies system config on Infinibox.
author: Wei Wang
options:
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
def get_rule(module, disable_fail=False):
    """
    Find and return config setting value
    Use disable_fail when we are looking for config
    and it may or may not exist and neither case is an error.
    """
    pass

def handle_stat(module):
    """Return config stat"""

    pass

    # config_group = module.params["config_group"]
    # key = module.params["key"]
    # value = get_config(module)

    # result = {
    #     "changed": False,
    #     "object_type": config_group,
    #     "key": key,
    #     "value": value,
    # }
    # module.exit_json(**result)


@api_wrapper
def create_rule(module, disable_fail=False):
    """
    Create a new notifition rule
    """
    system = get_system(module)
    name = module.params["name"]
    target_id = module.params["target_id"]
    event_level = module.params["event_level"]
    include_events = module.params["include_events"]
    exclude_events = module.params["exclude_events"]
    target_parameters = module.params["target_parameters"]


    path = f"notifications/rules"

    json_data = {
        "name": name,
        "target_id": target_id,
        "event_level": event_level,
        "include_events": include_events,
        "exclude_events": exclude_events,
        "target_parameters": target_parameters
    }


    system.api.post(path=path, data=json_data)



def handle_present(module):
    """Make config present"""
    changed = False
    msg = "Config unchanged"
    if not module.check_mode:
        #old_config = get_rule(module, disable_fail=True)
        #set_config(module)
        create_rule(module)
        #new_config = get_rule(module)
        #changed = new_config != old_config

        # if changed:
        #     msg = "Config changed"
        # else:
        #     msg = "Config unchanged since the value is the same as the existing config"

    module.exit_json(changed=changed, msg=msg)




def handle_absent(module):
    pass


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
            "name": {"required": True},
            "target_id": {"required": True, "default": None, "type": int},
            "event_level": {"required": False, "default": {}, "type": list},
            "include_events": {"required": False, "default": {}, "type": list},
            "exclude_events": {"required": False, "default": {}, "type": list},
            "target_parameters": {"required": False, "default": None, "type": dict},
            "state": {"default": "present", "choices": ["stat", "present"]},
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
