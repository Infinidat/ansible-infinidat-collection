#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module creates, deletes or modifies repositories of users that can log on to an Infinibox."""

# Copyright: (c) 2023, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_users_repository
version_added: '2.13.12'
short_description:  Create, Delete or Modify respositories of users that can log on to an Infinibox
description:
    - This module creates, deletes or modifies respositories of users that can log on to an Infinibox.
author: David Ohlemacher (@ohlemacher)
options:
  bind_username:
    description:
      - The bind username
    required: true
  bind_password:
    description:
      - The bind user password
    required: true
  name:
    description:
      - Name of repository
    required: true
  port:
    description:
      - LDAP or AD port to use
    required: false
    default: 636
  repository_type:
    description:
      - The type of repository
    choices: ["AD", "LDAP"]
    required: true
  schema_group_attribute:
    description:
      - Schema group attributes
    required: false
    default: cn
  schema_group_basedn:
    description:
      - Schema group base DN
    required: false
    default: None
  schema_group_class:
    description:
      - Schema group class
    required: false
    default: groupOfNames
  schema_member_attribute:
    description:
      - Schema member attributes
    required: false
    default: memberof
  schema_user_basedn:
    description:
      - Schema user base DN
    required: false
    default: None
  schema_user_class:
    description:
      - Schema user class
    required: false
    default: posixAccount
  schema_username_attribute:
    description:
      - Schema username attribute
    required: false
    default: uid
  state:
    description:
      - Creates/Modifies users repositories when present or removes when absent.
    required: false
    default: present
    choices: [ "stat", "present", "absent" ]
  use_ldaps:
    description:
      - Use SSL (LDAPS)
    choices: ["true", "false"]
    default: true

extends_documentation_fragment:
    - infinibox
"""

EXAMPLES = r"""
- name: Create new metadata key foo with value bar
  infini_users_repository:
    name: ldap.example.com
    state: present
    # TODO
    user: admin
    password: secret
    system: ibox001
- name: Stat metadata key named foo
  infini_users_repository
    name: ldap.example.com
    state: stat
    # TODO
    user: admin
    password: secret
    system: ibox001
- name: Remove metadata keyn named foo
  infini_users_repository
    name: ldap.example.com
    state: absent
    # TODO
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
    HAS_INFINISDK,
    api_wrapper,
    get_cluster,
    get_filesystem,
    get_host,
    get_pool,
    get_system,
    get_volume,
    infinibox_argument_spec,
)
from infinisdk.core.exceptions import APICommandFailed

HAS_ARROW = True
try:
    import arrow
except ImportError:
    HAS_ARROW = False

HAS_CAPACITY = False


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
    bind_username = module.params["bind_username"]
    bind_password = module.params["bind_password"]
    name = module.params["name"]
    port = module.params["port"]
    repository_type = module.params["repository_type"]
    schema_group_attribute = module.params["schema_group_attribute"]
    schema_group_basedn = module.params["schema_group_basedn"]
    schema_member_attribute = module.params["schema_member_attribute"]
    schema_user_basedn = module.params["schema_user_basedn"]
    schema_user_class = module.params["schema_user_class"]
    schema_username_attribute = module.params["schema_username_attribute"]
    state = module.params["state"]

    if state == "stat":
        pass
    elif state == "present":
        pass
    elif state == "absent":
        pass
    else:
        module.fail_json(f"Invalid state '{state}' provided")


def main():
    """Main module function"""
    argument_spec = infinibox_argument_spec()

    argument_spec.update(
        {
            "bind_password": {"required": True, "default": None},
            "bind_username": {"required": True},
            "name": {"required": True},
            "port": {"required": False, "type": int, "default": 636},
            "repository_type": {"required": True, "choices": [True, False]},
            "schema_group_attribute": {"required": False, "default": "cn"},
            "schema_group_basedn": {"required": False, "default": None},
            "schema_member_attribute": {"required": False, "default": "memberof"},
            "schema_group_class": {"required": False, "default": "groupOfNames"},
            "schema_user_basedn": {"required": False, "default": None},
            "schema_user_class": {"required": False, "default": "posixAccount"},
            "schema_username_attribute": {"required": False, "default": "uid"},
            "state": {"default": "present", "choices": ["stat", "present", "absent"]},
            "use_ldaps": {"required": False, "choices": [True, False], "default": True},
        }
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib("infinisdk"))

    if not HAS_ARROW:
        module.fail_json(msg=missing_required_lib("arrow"))

    check_options(module)
    execute_state(module)


if __name__ == "__main__":
    main()
