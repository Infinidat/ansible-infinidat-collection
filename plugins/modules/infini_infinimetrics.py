#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=invalid-name,use-dict-literal,line-too-long,wrong-import-position

# Copyright: (c) 2024, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""This module creates or modifies Infinibox registrations on Infinimetrics."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_infinimetrics
version_added: '2.16.2'
short_description:  Create (present state) or remove (absent state) an Infinibox registration on an Infinimetrics.
description:
    - Create (present state) or remove (absent state) an Infinibox registration on an Infinimetrics.
author: David Ohlemacher (@ohlemacher)
options:
  infinimetrics_system:
    description:
      - Infinimetrics hostname or IPv4 Address.
    required: true
  state:
    description:
      - Registers the Infinibox with Infinimetrics, when using state present.
      - For state absent, the Infinibox is deregistered from Infinimetrics.
      - State stat shows the registration status of the Infinibox with Infinimetrics.
    required: false
    default: present
    choices: [ "stat", "present", "absent" ]
extends_documentation_fragment:
    - infinibox
"""

EXAMPLES = r"""
- name: Register IBOX with Infinimetrics
  infini_infinimetrics:
    infinimetrics_system: infinimetrics
    state: present
    user: admin
    password: secret
    system: ibox001

- name: Show registration status of IBOX with Infinimetrics
  infini_infinimetrics:
    infinimetrics_system: infinimetrics
    state: present
    user: admin
    password: secret
    system: ibox001

- name: Deregister IBOX from Infinimetrics
  infini_infinimetrics:
    infinimetrics_system: infinimetrics
    state: present
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
    merge_two_dicts,
    get_system,
    infinibox_argument_spec,
)

HAS_INFINISDK = True
try:
    from infinisdk.core.exceptions import APICommandFailed
except ImportError:
    HAS_INFINISDK = False


def handle_stat(module):
    """ Handle the stat state parameter """
    infinimetrics_system = module.params['infinimetrics_system']
    infinibox_system = module.params['system']
    path = "system/certificates"
    system = get_system(module)
    try:
        cert_result = system.api.get(path=path).get_result()[0]
    except APICommandFailed:
        msg = f"Cannot stat infinimetrics {infinimetrics_system} registered Infinibox {infinibox_system}"
        module.fail_json(msg=msg)
    result = dict(
        changed=False,
        msg="Infinimetrics {infinimetrics_system} registered Infinibox {infinibox_system} found"
    )
    result = merge_two_dicts(result, cert_result)
    module.exit_json(**result)


def handle_present(module):
    """ Handle the present state parameter """
    certificate_file_name = module.params['certificate_file_name']
    path = "system/certificates"
    system = get_system(module)

    with open(certificate_file_name, 'rb') as cert_file:
        try:
            try:
                files = {'file': cert_file}
            except FileNotFoundError:
                module.fail_json(msg=f"Cannot find SSL certificate file named {certificate_file_name}")
            except Exception as err:  # pylint: disable=broad-exception-caught
                module.fail_json(msg=f"Cannot open SSL certificate file named {certificate_file_name}: {err}")
            cert_result = system.api.post(path=path, files=files).get_result()
        except APICommandFailed as err:
            msg = f"Cannot upload cert: {err}"
            module.fail_json(msg=msg)

    cert_serial = cert_result['certificate']['serial_number']
    cert_issued_by_cn = cert_result['certificate']['issued_by']['CN']
    cert_issued_to_cn = cert_result['certificate']['issued_to']['CN']
    result = dict(
        changed=True,
        msg="System SSL certificate uploaded successfully. "
        f"Certificate S/N {cert_serial} issued by CN {cert_issued_by_cn} to CN {cert_issued_to_cn}"
    )
    result = merge_two_dicts(result, cert_result)
    module.exit_json(**result)


def handle_absent(module):
    """ Handle the absent state parameter. """
    path = "system/certificates/generate_self_signed?approved=true"
    system = get_system(module)
    try:
        cert_result = system.api.post(path=path).get_result()
    except APICommandFailed as err:
        msg = f"Cannot clear SSL certificate: {err}"
        module.fail_json(msg=msg)
    result = dict(
        changed=True,
        msg="System SSL certificate cleared and a self signed certificate was installed successfully"
    )
    result = merge_two_dicts(result, cert_result)
    module.exit_json(**result)


def execute_state(module):
    """Handle states"""
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


def main():
    """ Main """
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            infinimetrics_system=dict(required=True),
            state=dict(default="present", choices=["stat", "present", "absent"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib("infinisdk"))

    execute_state(module)


if __name__ == "__main__":
    main()
