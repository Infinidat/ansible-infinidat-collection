#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module creates, deletes or modifies metadata on Infinibox."""

# Copyright: (c) 2023, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_notification_rule
version_added: '2.13.12'
short_description:  Config notification rules
description:
    - This module config notification rules on Infinibox
author: Wei Wang
options:
  name:
    description:
      - Name of the rule
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
def find_target_id(module, system):
    """
    Find the ID of the target by name
    """
    target = module.params["target"]
    path = "notifications/targets?name={0}&fields=id".format(target)
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
def get_rules(module, disable_fail=False):
    """
    Get all rules
    """

    system = get_system(module)
    path = f"notifications/rules"
    rules = system.api.get(path=path)



@api_wrapper
def find_rule_id(module, system):
    """
    Find the ID of the rule by name
    """
    rule_name = module.params["name"]
    path = "notifications/rules?name={0}&fields=id".format(rule_name)
    api_result = system.api.get(
        path=path
    )
    if len(api_result.get_json()['result']) > 0:
        result = api_result.get_json()['result'][0]
        rule_id = result['id']
    else:
        rule_id=None
    return rule_id


@api_wrapper
def delete_rule(module, disable_fail=False):
    """
    Delete a notification rule
    """

    system = get_system(module)
    name = module.params["name"]
    rule_id = find_rule_id(module,system)


    path = f"notifications/rules/{rule_id}?approved=true"
    system.api.delete(path=path)

@api_wrapper
def create_rule(module, disable_fail=False):
    """
    Create a new notifition rule
    """
    system = get_system(module)
    name = module.params["name"]
    event_level = module.params["event_level"]
    #target_id= module.params["target_id"] #if using email, target id is 3, if not find id by name, if
    include_events = module.params["include_events"]
    exclude_events = module.params["exclude_events"]
    recipients = module.params["recipients"]
    target = module.params["target"]


    path = f"notifications/rules"

    json_data = {
        "name": name,
        "event_level": event_level,
        "include_events": include_events,
        "exclude_events": exclude_events,
    }

    if not len(recipients)==0:
        target_parameters = {
            "recipients": recipients
        }
        target_id = 3
        json_data["target_parameters"] = target_parameters

    if target:
        target_id=find_target_id(module, system)
        #json_data["target"] = target

    json_data["target_id"] = target_id

    system.api.post(path=path, data=json_data)

@api_wrapper
def update_rule(module, disable_fail=False):
    """
    Update an existing rule.
    """
    system = get_system(module)
    name = module.params["name"]
    event_level = module.params["event_level"]
    include_events = module.params["include_events"]
    exclude_events = module.params["exclude_events"]
    recipients = module.params["recipients"]
    target = module.params["target"]


    json_data = {
        "name": name,
        "event_level": event_level,
        "include_events": include_events,
        "exclude_events": exclude_events,
    }

    if not len(recipients)==0:
        target_parameters = {
            "recipients": recipients
        }
        target_id = 3
        json_data["target_parameters"] = target_parameters

    if target:
        target_id=find_target_id(module, system)
        #json_data["target"] = target

    json_data["target_id"] = target_id

    rule_id = find_rule_id(module,system)

    path = f"notifications/rules/{rule_id}"


    system.api.put(path=path, data=json_data)



def handle_present(module):
    """Make config present"""

    system = get_system(module)
    name = module.params["name"]
    changed = False
    if not module.check_mode:
        rule_id = find_rule_id(module,system)
        if not rule_id:
            create_rule(module)
            changed=True
            msg = "Rule {} created".format(name)
        else:
            update_rule(module)
            msg = "Rule {} updated".format(name)
            changed=True

    module.exit_json(changed=changed, msg=msg)




def handle_absent(module):
    """Make config present"""
    changed = False
    name = module.params["name"]
    system = get_system(module)

    rule_id = find_rule_id(module,system)
    if not rule_id:
        msg="Rule of {0} does not exist, deletion operation skipped.".format(name)
        changed = False
    else:
        msg="Rule {0} has been deleted".format(name)
        changed = True
        if not module.check_mode:
            delete_rule(module)

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
            "name": {"required": True},
            "event_level": {"required": False, "default": {}, "type": list},
            "include_events": {"required": False, "default": {}, "type": list},
            "exclude_events": {"required": False, "default": {}, "type": list},
            "recipients": {"required": False, "default": {}, "type": list},
            "target": {"required": False, "type": str},
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
