#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This module creates, deletes or modifies metadata on Infinibox."""

# Copyright: (c) 2023, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_metadata
version_added: '2.13.12'
short_description:  Create, Delete or Modify metadata on Infinibox
description:
    - This module creates, deletes or modifies metadata on Infinibox.
author: David Ohlemacher (@ohlemacher)
options:
  key:
    description:
      - Name of the metadata key
    required: true
  value:
    description:
      - Value of the metadata key
    required: false
  state:
    description:
      - Creates/Modifies metadata when present or removes when absent.
    required: false
    default: present
    choices: [ "stat", "present", "absent" ]

extends_documentation_fragment:
    - infinibox
requirements:
    - capacity
"""

EXAMPLES = r"""
- name: Create new metadata key foo with value bar
  infini_metadata:
    name: foo
    key: bar
    state: present
    user: admin
    password: secret
    system: ibox001
- name: Stat metadata key named foo
  infini_metadata:
    name: foo
    state: stat
    user: admin
    password: secret
    system: ibox001
- name: Remove metadata keyn named foo
  infini_vol:
    name: foo_snap
    state: absent
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
    HAS_INFINISDK,
    api_wrapper,
    infinibox_argument_spec,
    get_system,
)

HAS_ARROW = True
try:
    import arrow
except ImportError:
    HAS_ARROW = False

HAS_CAPACITY = False


@api_wrapper
def get_metadata(module, disable_fail=False):
    """Find and return metadata"""
    system = get_system(module)
    object_type = module.params["object_type"]
    key = module.params["key"]
    url = f"metadata/{object_type}?key={key}"
    metadata = system.api.get(path=url)
    result = metadata.get_result()
    if not disable_fail and not result:
        msg = f"Metadata for {object_type} with key {key} not found. Cannot stat."
        module.fail_json(msg=msg)
    return result


@api_wrapper
def put_metadata(module):
    """Create metadata key with a value.  The changed variable is found elsewhere."""
    system = get_system(module)

    if not module.check_mode:
        object_type = module.params["object_type"]
        object_name = module.params["object_name"]
        key = module.params["key"]
        path = f"metadata/{object_type}"
        value = module.params["value"]

        # TODO check value size > 32k

        # Create json data
        data = {key: value}
        if object_name:
            assert (
                object_type != "system"
            )  # object_type system cannot have an object_name
            data["object"] = object_name

        # Put
        system.api.put(path=path, data=data)
    # changed not returned by design


@api_wrapper
def delete_metadata(module):
    """Remove metadata key"""
    system = get_system(module)
    changed = False
    if not module.check_mode:
        object_type = module.params["object_type"]
        key = module.params["key"]
        path = f"metadata/{object_type}/{key}"
        system.api.delete(path=path)
        changed = True
    return changed


def handle_stat(module):
    """Return metadata stat"""
    metadata = get_metadata(module)
    object_type = module.params["object_type"]
    key = module.params["key"]
    metadata_id = metadata[0]["id"]
    object_id = metadata[0]["object_id"]
    value = metadata[0]["value"]

    result = {
        "changed": False,
        "object_type": object_type,
        "key": key,
        "id": metadata_id,
        "object_id": object_id,
        "value": value,
    }
    module.exit_json(**result)


def handle_present(module):
    """Make metadata present"""
    old_metadata = get_metadata(module, disable_fail=True)
    put_metadata(module)
    new_metadata = get_metadata(module)
    changed = False
    msg = "Metadata unchanged"
    if not module.check_mode:
        changed = new_metadata != old_metadata
        if changed:
            msg = "Metadata changed"
    module.exit_json(changed=changed, msg=msg)


def handle_absent(module):
    """Make metadata absent"""
    changed = delete_metadata(module)
    module.exit_json(changed=changed, msg="Metadata removed")


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
    state = module.params["state"]
    object_type = module.params["object_type"]
    object_name = module.params["object_name"]

    # Check object_type
    object_types = [
        "cluster",
        "fs",
        "fs-snap",
        "host",
        "pool",
        "system",
        "vol",
        " vol-snap",
    ]
    if object_type not in object_types:
        module.fail_json(
            f"Cannot create {object_type} metadata. Object type must be one of {object_types}"
        )

    # Check object_name
    if object_type == "system" and object_name is not None:
        module.fail_json(
            f"Cannot specify an object name, i.e. {object_name}, "
            f"if creating metadata key for object type system"
        )

    if state == "present":
        # Check value
        key = module.params["key"]
        value = module.params["value"]
        if not value:
            module.fail_json(
                f"Cannot create a {object_type} metadata key without providing a value"
            )
        # Check system key
        if object_type == "system":
            if key == "ui-dataset-default-provisioning":
                values = ["THICK", "THIN"]
                if value not in values:
                    module.fail_json(
                        f"Cannot create {object_type} metadata for key {key}. "
                        f"Value must be one of {values}. Invalid value: {value}."
                    )
            if key in [
                "ui-dataset-base2-units",
                "ui-feedback-dialog",
                "ui-feedback-form",
            ]:
                if not isinstance(value, int):
                    module.fail_json(
                        f"Cannot create {object_type} metadata for key {key}. "
                        f"Value must be of type bool. Invalid value: {value}."
                    )
            if key in ["ui-bulk-volume-zero-padding", "ui-table-export-limit"]:
                if not isinstance(value, int):
                    module.fail_json(
                        f"Cannot create {object_type} metadata for key {key}. "
                        f"Value must be of type integer. Invalid value: {value}."
                    )

    elif state == "absent":
        pass


def main():
    """Main module function"""
    argument_spec = infinibox_argument_spec()

    argument_spec.update(
        {
            "object_type": {"required": True},
            "object_name": {"required": False, "default": None},
            "key": {"required": True},
            "value": {"required": False, "default": None},
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


if __name__ == "__main__":
    main()
