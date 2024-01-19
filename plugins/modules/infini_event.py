#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_vol
version_added: '2.16.2'
short_description:  Create custom events on Infinibox
description:
    - This module creates events on Infinibox.
author: David Ohlemacher (@ohlemacher)
options:
  description_template:
    description:
      - The content of the custom event
    required: true
  visibility:
    description:
      - The event's visibility
    required: false
    choices:
      - CUSTOMER
      - INFINIDAT
  level:
    description:
      - The level of the custom event
    required: true
    choices:
      - INFO
      - WARNING
      - ERROR
      - CRITICAL
  state:
    description:
      - Creates a custom event when present. Stat is not yet implemented. There is no way to remove events once posted, so abent is also not implemented.
    required: false
    default: present
    choices: [ "present" ]
"""

EXAMPLES = r"""
- name: Create custom info event
  infini_event:
    description_template: Message content
    level: INFO
    state: present
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

import traceback

from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
    HAS_INFINISDK,
    api_wrapper,
    infinibox_argument_spec,
    get_system,
    fail,
    success,
)


HAS_CAPACITY = True
try:
    from capacity import KiB, Capacity
except ImportError:
    HAS_CAPACITY = False

HAS_ARROW = False


def handle_stat(module):
    """Handle stat state"""
    msg = f"handle_stat() is not implemented"
    fail(module, msg=msg)


def handle_present(module):
    """Handle present state"""
    system = get_system(module)
    description_template = module.params["description_template"]
    level = module.params["level"]
    visibility = module.params["visibility"]

    path = "events/custom"
    json_data = {
        "description_template": description_template,
        "level": level,
        "visibility": visibility,
    }
    system.api.post(path=path, data=json_data)
    success(module=module, changed=True, msg="Event posted")


def execute_state(module):
    """Handle states"""
    state = module.params["state"]
    try:
        if state == "stat":
            handle_stat(module)
        elif state == "present":
            handle_present(module)
        else:
            fail(module, msg=f"Internal handler error. Invalid state: {state}")
    finally:
        system = get_system(module)
        system.logout()


def check_options(module):
    """Verify module options are sane, but there is little to check in this module"""


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            description_template=dict(required=True, type=str),
            level=dict(required=True, choices=["INFO", "WARNING", "ERROR", "CRITICAL"]),
            state=dict(required=False, default="present", choices=["present"]),
            visibility=dict(default="CUSTOMER", required=False, choices=["CUSTOMER", "INFINIDAT"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        fail(module, msg=missing_required_lib("infinisdk"))

    check_options(module)
    execute_state(module)


if __name__ == "__main__":
    main()