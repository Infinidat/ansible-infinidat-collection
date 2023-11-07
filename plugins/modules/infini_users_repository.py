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
  ad_domain_name:
    required: false
    default: None
  bind_password:
    description:
      - The bind user password
    required: true
  bind_username:
    description:
      - The bind username
    required: true
  ldap_servers:
    description:
      - A list of LDAP servers. For an empty list, use [].
    required: false
    type: list
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
  schema_group_memberof_attribute:
    description:
      - Schema group memberof attribute
    required: false
    default: memberof
  schema_group_name_attribute:
    description:
      - Schema group name attribute
    required: false
    default: cn
  schema_groups_basedn:
    description:
      - Schema groups base DN
    required: false
    default: None
  schema_group_class:
    description:
      - Schema group class
    required: false
    default: groupOfNames
  schema_users_basedn:
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
      - When getting the stats for a users repository, the module will test
        connectivity to the repository and report the result in 'test_ok' as true or false.
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


@api_wrapper
def get_users_repository(module, disable_fail=False):
    """
    Find and return users repository information
    Use disable_fail when we are looking for an user repository
    and it may or may not exist and neither case is an error.
    """
    system = get_system(module)
    name = module.params["name"]

    path = f"config/ldap?name={name}"
    repo = system.api.get(path=path)

    if repo:
        result = repo.get_result()
        if not disable_fail and not result:
            msg = f"Users repository {name} not found. Cannot stat."
            module.fail_json(msg=msg)
        return result
    elif disable_fail:
        return None

    msg = f"Users repository {name} not found. Cannot stat."
    module.fail_json(msg=msg)


@api_wrapper
def test_users_repository(module, repository_id, disable_fail=False):
    """
    Find and return users repository information
    Use disable_fail when we are looking for an user repository
    and it may or may not exist and neither case is an error.
    """
    system = get_system(module)
    name = module.params["name"]

    path = f"config/ldap/{repository_id}/test"
    result = system.api.post(path=path)
    if result.response.status_code in [200]:
        return True
    return False


@api_wrapper
def post_users_repository(module):
    """
    Create or update users LDAP or AD repo. The changed variable is found elsewhere.
    Variable 'changed' not returned by design
    """
    system = get_system(module)
    name = module.params["name"]
    repo_type = module.params["repository_type"]
    schema_definition = {
        "group_class":               module.params["schema_group_class"],
        "group_memberof_attribute":  module.params["schema_group_memberof_attribute"],
        "group_name_attribute":      module.params["schema_group_name_attribute"],
        "groups_basedn":             module.params["schema_groups_basedn"],
        "user_class":                module.params["schema_user_class"],
        "username_attribute":        module.params["schema_username_attribute"],
        "users_basedn":              module.params["schema_users_basedn"],
    }

    # Create json data
    data = {
        "bind_password": module.params["bind_password"],
        "bind_username": module.params["bind_username"],
        "name": name,
        "schema_definition": schema_definition,
    }

    # Add type specific fields to data dict
    if repo_type == "ActiveDirectory":
        data["domain_name"] =  module.params["ad_domain_name"]
    else:  # LDAP
        data["servers"] = module.params["ldap_servers"]

    # Put
    path = "config/ldap"
    system.api.post(path=path, data=data)

    """Return users repository or None"""
    system = get_system(module)
    try:
        try:
            repo = system.volumes.get(name=module.params['name'])
        except KeyError:
            try:
                volume = system.volumes.get(name=module.params['volume'])
            except KeyError:
                volume = system.volumes.get(name=module.params['object_name']) # Used by metadata module
        return volume
    except Exception:
        return None


@api_wrapper
def delete_users_repository(module, name):
    """Delete repo."""
    system = get_system(module)
    changed = False
    if not module.check_mode:
        repo = get_users_repository(module, disable_fail=True)
        if repo and len(repo) == 1:
            path = f"config/ldap/{repo[0]['id']}"
            try:
                system.api.delete(path=path)
                changed = True
            except APICommandFailed as err:
                if err.status_code != 404:
                    raise
    return changed


def handle_stat(module):
    """Return users repository stat"""
    name = module.params['name']
    repos = get_users_repository(module)
    try:
        assert len(repos) == 1
    except AssertionError:
        msg = f"Users repository {name} not found in repository list {repos}. Cannot stat."
        module.fail_json(msg=msg)

    result = repos[0]
    repository_id = result.pop("id")
    result["msg"] = f"Stats for user repository {name}"
    result["repository_id"] = repository_id  # Rename id to repository_id
    result["test_ok"] = test_users_repository(module, repository_id=repository_id, disable_fail=True)
    result["changed"] = False
    module.exit_json(**result)


def handle_present(module):
    """Make users repository present"""
    name = module.params['name']
    repo_type = module.params['repository_type']
    assert repo_type in ["LDAP", "ActiveDirectory"]
    changed = False
    msg = f"Users repository {name} unchanged"
    if not module.check_mode:
        old_users_repo_result = get_users_repository(module, disable_fail=True)
        assert not old_users_repo_result or len(old_users_repo_result) == 1
        if old_users_repo_result:
            old_users_repo = old_users_repo_result[0]
            old_users_repo_type = old_users_repo["repository_type"]
            if old_users_repo_type != repo_type:
                msg = f"Cannot create a new users repository named {name} of type {repo_type} " \
                    f"when a repository with that name already exists of type {old_users_repo_type}"
                module.fail_json(msg=msg)
        else:
            old_users_repo = None
            old_users_repo_type = None
        post_users_repository(module)

        new_users_repo = get_users_repository(module)
        changed = new_users_repo != old_users_repo
        if changed:
            if old_users_repo:
                msg = f"Users repository {name} updated"
            else:
                msg = f"Users repository {name} created"
        else:
            msg = f"Users repository {name} unchanged since the value is the same as the existing users repository"
    module.exit_json(changed=changed, msg=msg)


def handle_absent(module):
    """Make users repository absent"""
    name = module.params['name']
    msg = f"Users repository {name} unchanged"
    changed = False
    if not module.check_mode:
        changed = delete_users_repository(module, name)
        if changed:
            msg = f"Users repository {name} removed"
        else:
            msg = f"Users repository {name} did not exist so removal was unnecessary"
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
    ad_domain_name = module.params["ad_domain_name"]
    bind_password = module.params["bind_password"]
    bind_username = module.params["bind_username"]
    ad_domain_name = module.params["ad_domain_name"]
    ldap_servers = module.params["ldap_servers"]
    name = module.params["name"]
    port = module.params["port"]
    repository_type = module.params["repository_type"]
    schema_group_memberof_attribute = module.params["schema_group_memberof_attribute"]
    schema_group_name_attribute = module.params["schema_group_name_attribute"]
    schema_groups_basedn = module.params["schema_groups_basedn"]
    schema_user_class = module.params["schema_user_class"]
    schema_username_attribute = module.params["schema_username_attribute"]
    schema_users_basedn = module.params["schema_users_basedn"]
    state = module.params["state"]

    if state == "stat":
        pass
    elif state == "present":
        if repository_type:
            common_params = ["bind_password", "bind_username", "schema_group_class",
                             "schema_group_memberof_attribute", "schema_group_name_attribute",
                             "schema_user_class", "schema_username_attribute",]
            if repository_type == "LDAP":  # Creating an LDAP
                req_params = common_params
                missing_params = [param for param in req_params if not is_set_in_params(module, param)]
                if missing_params:
                    msg = f"Cannot create a new LDAP repository named {name} without providing required parameters: {missing_params}"
                    module.fail_json(msg=msg)

                disallowed_params = ["ad_domain_name", "ad_auto_discover_servers"]
                error_params = [param for param in disallowed_params if is_set_in_params(module, param)]
                if error_params:
                    msg = f"Cannot create a new LDAP repository named {name} when providing disallowed parameters: {error_params}"
                    module.fail_json(msg=msg)
            else: # Creating an AD
                assert repository_type == "ActiveDirectory"
                req_params = common_params
                missing_params = [param for param in req_params if not is_set_in_params(module, param)]
                if missing_params:
                    msg = f"Cannot create a new LDAP repository named {name} without providing required parameters: {missing_params}"
                    module.fail_json(msg=msg)

                disallowed_params = ["ldap_servers"]
                error_params = [param for param in disallowed_params if is_set_in_params(module, param)]
                if error_params:
                    msg = f"Cannot create a new LDAP repository named {name} when providing disallowed parameters: {error_params}"
                    module.fail_json(msg=msg)
        else:
            msg = f"Cannot create a new users repository without providing a repository_type"
            module.fail_json(msg=msg)
    elif state == "absent":
        pass
    else:
        module.fail_json(f"Invalid state '{state}' provided")


def is_set_in_params(module, key):
    """A utility function to test if a module param key is set to a truthy value.
    Useful in list comprehensions."""
    is_set = False
    try:
        if module.params[key]:
            is_set = True
    except KeyError:
        pass
    return is_set


def main():
    """Main module function"""
    argument_spec = infinibox_argument_spec()

    argument_spec.update(
        {
            "ad_auto_discover_servers": {"required": False, "choices": [True, False], "default": True},
            "ad_domain_name": {"required": False, "default": None},
            "bind_password": {"required": False, "default": None, "no_log": True},
            "bind_username": {"required": False, "default": None},
            "ldap_servers": {"required": False, "default": [], "type": "list", "elements": "str"},
            "name": {"required": True},
            "port": {"required": False, "type": int, "default": 636},
            "repository_type": {"required": False, "choices": ["LDAP", "ActiveDirectory"], "default": None},
            "schema_group_class": {"required": False, "default": None},
            "schema_group_memberof_attribute": {"required": False, "default": None},
            "schema_group_name_attribute": {"required": False, "default": None},
            "schema_groups_basedn": {"required": False, "default": None},
            "schema_user_class": {"required": False, "default": None},
            "schema_username_attribute": {"required": False, "default": None},
            "schema_users_basedn": {"required": False, "default": None},
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
