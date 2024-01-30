#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infini_sso
version_added: '2.16.2'
short_description: Configures or queries SSO on Infinibox
description:
    - This module configures (present state) or gets information about (absent state) SSO on Infinibox
author: David Ohlemacher (@ohlemacher)
options:
  name:
    description:
      - Sets a name to reference the SSO by.
    required: true
  issuer:
    description:
      - URI of the SSO issuer.
    required: false
  sign_on_url:
    description:
      - URL for sign on.
    required: false
  enabled:
    description:
      - Determines if the SSO is enabled.
    required:  false
    default: true
    type: bool
  state:
    description:
      - Creates/Modifies the SSO, when using state present.
      - For state absent, the SSO is removed.
      - State stat shows the existing SSO's details.
    required: false
    default: present
    choices: [ "stat", "present", "absent" ]
extends_documentation_fragment:
    - infinibox
"""

EXAMPLES = r"""
- name: Configure SSO
  infini_sso:
    name: OKTA
    enabled: true
    issuer: "http://www.okta.com/eykRra384o32rrTs"
    sign_on_url: "https://infinidat.okta.com/app/infinidat_psus/exkra32oyyU6KCUCk2p7/sso/saml"
    state: present
    user: admin
    password: secret
    system: ibox001

- name: Stat SSO
  infini_sso:
    name: OKTA
    state: stat
    user: admin
    password: secret
    system: ibox001

- name: Clear SSO configuration
  infini_sso:
    state: absent
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

import traceback

from ansible_collections.infinidat.infinibox.plugins.module_utils.infinibox import (
    HAS_INFINISDK,
    ObjectNotFound,
    api_wrapper,
    merge_two_dicts,
    get_system,
    infinibox_argument_spec,
)

try:
    from infinisdk.core.exceptions import APICommandFailed
    from infinisdk.core.exceptions import ObjectNotFound
    from infi.dtypes.iqn import make_iscsi_name
except ImportError:
    pass  # Handled by HAS_INFINISDK from module_utils


def find_sso(module, name):
    path = f"config/sso/idps?name={name}"

    try:
        system = get_system(module)
        sso_result = system.api.get(path=path).get_result()
    except APICommandFailed as err:
        msg = f"Cannot stat SSO identity provider {name}: {err}"
        module.fail_json(msg=msg)

    return sso_result


def handle_stat(module):
    name = module.params["name"]
    #breakpoint()
    sso_result = find_sso(module, name)
    if not sso_result:
        msg = f"SSO identity provider {name} not found. Cannot stat."
        module.fail_json(msg=msg)

    result = dict(
        changed=False,
        msg=f"SSO identity provider {name} stat found"
    )

    result = merge_two_dicts(result, sso_result[0])
    result['signing_certificate'] = "redacted"
    module.exit_json(**result)


def handle_present(module):
    enabled = module.params['enabled']
    issuer = module.params['issuer']
    sign_on_url = module.params['sign_on_url']
    signed_assertion = module.params['signed_assertion']
    signed_response = module.params['signed_response']
    signing_certificate = module.params['signing_certificate']
    name = module.params['name']

    path = f"config/sso/idps"
    data = {
        "enabled": enabled,
        "issuer": issuer,
        "name": name,
        "sign_on_url": sign_on_url,
        "signed_assertion": signed_assertion,
        "signed_response": signed_response,
        "signing_certificate": signing_certificate,
    }

    try:
        system = get_system(module)
        sso_result = system.api.post(path=path, data=data).get_result()
    except APICommandFailed as err:
        msg = f"Cannot configure SSO {name}: {err}"
        module.fail_json(msg=msg)

    result = dict(
        changed=True,
        msg=f"SSO identity provider named {name} successfully configured"
    )
    result = merge_two_dicts(result, sso_result)
    result['signing_certificate'] = "redacted"

    module.exit_json(**result)


def handle_absent(module):
    name = module.params["name"]
    found_sso = find_sso(module, name)
    if not found_sso:
        result = dict(
            changed=False,
            msg=f"SSO {name} already not found"
        )
        module.exit_json(**result)

    sso_id = found_sso[0]['id']
    path = f"config/sso/idps/{sso_id}"

    try:
        system = get_system(module)
        sso_result = system.api.delete(path=path).get_result()
    except APICommandFailed as err:
        msg = f"Cannot delete SSO identity provider {name}: {err}"
        module.fail_json(msg=msg)

    if not sso_result:
        msg = f"SSO identity provider named {name} with ID {sso_id} not found. Cannot delete."
        module.fail_json(msg=msg)

    result = dict(
        changed=True,
        msg=f"SSO identity provider named {name} deleted"
    )

    result = merge_two_dicts(result, sso_result)
    result['signing_certificate'] = "redacted"
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


def check_options(module):
    """Verify module options are sane"""
    signing_certificate = module.params["signing_certificate"]
    sign_on_url = module.params["sign_on_url"]
    state = module.params["state"]
    is_failed = False
    msg = ""
    if state in ["present"]:
        if not sign_on_url:
            msg += "A sign_on_url parameter must be provided. "
            is_failed = True
        if not signing_certificate:
            msg += "A signing_certificate parameter must be provided. "
            is_failed = True
    if is_failed:
        module.fail_json(msg=msg)


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            enabled=dict(required=False, type=bool, default=True),
            issuer=dict(required=False, default=None),
            name=dict(required=True),
            sign_on_url=dict(required=False, default=None),
            signed_assertion=dict(required=False, type=bool, default=False),
            signed_response=dict(required=False, type=bool, default=False),
            signing_certificate=dict(required=False, default=None, no_log=True),
            state=dict(default="present", choices=["stat", "present", "absent"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    check_options(module)
    execute_state(module)


if __name__ == "__main__":
    main()

