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
    - Deleting metadata by object, without specifying a key, is not implemented for any object_type (e.g. DELETE api/rest/metadata/system). This would delete all metadata belonging to the object. Instead delete each key explicitely using its key name.
author: David Ohlemacher (@ohlemacher)
options:
  object_type:
    description:
      - Type of object
    required: true
    choices: ["cluster", "fs", "fs-snap", "host", "pool", "system", "vol", "vol-snap"]
  object_name:
    description:
      - Name of the object. Not used if object_type is system
    required = false
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
    get_filesystem,
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
def get_metadata_vol(module, disable_fail):
    system = get_system(module)
    object_type = module.params["object_type"]
    object_name = module.params["object_name"]
    key = module.params["key"]
    metadata = None

    vol = get_volume(module, system)
    if vol:
        path = f"metadata/{vol.id}/{key}"
        try:
            metadata = system.api.get(path=path)
        except APICommandFailed as err:
            if not disable_fail:
                module.fail_json(
                    f"Cannot find {object_type} metadata key. "
                    f"Volume {object_name} key {key} not found"
                )
    elif not disable_fail:
        msg = f"Volume with object name {object_name} not found. Cannot stat its metadata."
        module.fail_json(msg=msg)

    return metadata

@api_wrapper
def get_metadata_fs(module, disable_fail):
    system = get_system(module)
    object_type = module.params["object_type"]
    object_name = module.params["object_name"]
    key = module.params["key"]
    metadata = None

    # Function get_filesystem() expects the filesystem name's key to be 'filesystem', not 'object_name'.
    module.params['filesystem'] = object_name
    fs = get_filesystem(module, system)
    if fs:
        path = f"metadata/{fs.id}/{key}"
        try:
            metadata = system.api.get(path=path)
        except APICommandFailed as err:
            if not disable_fail:
                module.fail_json(
                    f"Cannot find {object_type} metadata key. "
                    f"File system {object_name} key {key} not found"
                )
    elif not disable_fail:
        msg = f"File system named {object_name} not found. Cannot stat its metadata."
        module.fail_json(msg=msg)

    return metadata


@api_wrapper
def get_metadata(module, disable_fail=False):
    """Find and return metadata"""
    system = get_system(module)
    object_type = module.params["object_type"]
    object_name = module.params["object_name"]
    key = module.params["key"]

    if object_type == "system":
        path = f"metadata/{object_type}?key={key}"
        metadata = system.api.get(path=path)
    elif object_type == "fs":
        metadata = get_metadata_fs(module, disable_fail)
    elif object_type == "vol":
        metadata = get_metadata_vol(module, disable_fail)
    else:
        msg = f"Metadata for {object_type} not supported. Cannot stat."
        module.fail_json(msg=msg)

    if metadata:
        result = metadata.get_result()
        if not disable_fail and not result:
            msg = f"Metadata for {object_type} with key {key} not found. Cannot stat."
            module.fail_json(msg=msg)
        return result
    else:
        return None


@api_wrapper
def put_metadata(module):
    """Create metadata key with a value.  The changed variable is found elsewhere."""
    system = get_system(module)

    object_type = module.params["object_type"]
    key = module.params["key"]
    value = module.params["value"]

    # TODO check metadata value size < 32k

    if object_type == "system":
        path = "metadata/system"
    elif object_type == "vol":
        vol = get_volume(module, system)
        if not vol:
            object_name = module.params["object_name"]
            msg = f"Volume {object_name} not found. Cannot add metadata key {key}."
            module.fail_json(msg=msg)
        path = f"metadata/{vol.id}"

    # Create json data
    data = {
        key: value
    }

    # Put
    system.api.put(path=path, data=data)
    # changed not returned by design


@api_wrapper
def delete_metadata(module):
    """
    Remove metadata key.
    Not implemented by design: Deleting all of the system’s metadata
    using 'DELETE api/rest/metadata/system'.
    """
    system = get_system(module)
    changed = False
    object_type = module.params["object_type"]
    key = module.params["key"]
    if object_type == "system":
        path = f"metadata/system/{key}"
    elif object_type == "vol":
        vol = get_volume(module, system)
        if not vol:
            changed = False
            return changed  # No vol therefore no metadata to delete
        path = f"metadata/{vol.id}/{key}"
    else:
        module.fail_json( f"TODO: Implement for object_type {object_type}")

    try:
        system.api.delete(path=path)
        changed = True
    except APICommandFailed as err:
        if err.status_code != 404:
            raise
    return changed


def handle_stat(module):
    """Return metadata stat"""
    object_type = module.params["object_type"]
    key = module.params["key"]
    metadata = get_metadata(module)
    if object_type == "system":
        metadata_id = metadata[0]["id"]
        object_id = metadata[0]["object_id"]
        value = metadata[0]["value"]
    else:
        metadata_id = metadata["id"]
        object_id = metadata["object_id"]
        value = metadata["value"]

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
    changed = False
    msg = "Metadata unchanged"
    if not module.check_mode:
        old_metadata = get_metadata(module, disable_fail=True)
        put_metadata(module)
        new_metadata = get_metadata(module)
        changed = new_metadata != old_metadata
        if changed:
            msg = "Metadata changed"
        else:
            msg = "Metadata unchanged since the value is the same as the existing metadata"
    module.exit_json(changed=changed, msg=msg)


def handle_absent(module):
    """Make metadata absent"""
    msg = "Metadata unchanged"
    if not module.check_mode:
        changed = delete_metadata(module)
        if changed:
            msg = "Metadata removed"
        else:
            msg = "Metadata did not exist so no removal was necessary"
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
        "vol-snap",
    ]
    if object_type not in object_types:
        module.fail_json(
            f"Cannot create {object_type} metadata. Object type must be one of {object_types}"
        )

    # Check object_name
    if object_type == "system":
        if object_name:
            module.fail_json("An object_name for object_type system must not be provided.")
    else:
        if not object_name:
            module.fail_json(
                f"The name of the {object_type} must be provided as object_name."
            )

    key = module.params["key"]
    if not key:
        module.fail_json(f"Cannot create a {object_type} metadata key without providing a key name")

    if state == "stat":
        pass
    elif state == "present":
        # Check value
        key = module.params["key"]
        value = module.params["value"]
        if not value:
            module.fail_json(
                f"Cannot create a {object_type} metadata key {key} without providing a value"
            )
        # Check system object_type
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
    else:
        module.fail_json(f"Invalid state '{state}' provided")


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
