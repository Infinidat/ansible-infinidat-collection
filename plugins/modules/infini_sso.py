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
    fail,
    success,
)

try:
    from infinisdk.core.exceptions import APICommandFailed
    from infinisdk.core.exceptions import ObjectNotFound
    from infi.dtypes.iqn import make_iscsi_name
except ImportError:
    pass  # Handled by HAS_INFINISDK from module_utils


def handle_stat(module):
    path = f"system/certificates"
    system = get_system(module)
    try:
        cert_result = system.api.get(path=path).get_result()[0]
    except APICommandFailed as err:
        msg = f"Cannot stat."
        fail(module, msg=msg)
    result = dict(
        changed=False,
        msg="Certficate stat found"
    )
    result = merge_two_dicts(result, cert_result)
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
    system = get_system(module)

    data = {
        "enabled": enabled,
        "issuer": issuer,
        "name": name,
        "sign_on_url": sign_on_url,
        "signed_assertion": signed_assertion,
        "signed_response": signed_response,
        "signing_certificate": signing_certificate,
    }

    cert_serial       = cert_result['certificate']['serial_number']
    cert_issued_by_cn = cert_result['certificate']['issued_by']['CN']
    cert_issued_to_cn = cert_result['certificate']['issued_to']['CN']
    result = dict(
        changed=True,
        msg="System certificate uploaded successfully. " + \
        f"Certificate S/N {cert_serial} issued by CN {cert_issued_by_cn} to CN {cert_issued_to_cn}"
    )
    result = merge_two_dicts(result, cert_result)
    module.exit_json(**result)


def handle_absent(module):
    fail(module, msg="Not implemented: handle_absent()")


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
            fail(module, msg=f"Internal handler error. Invalid state: {state}")
    finally:
        system = get_system(module)
        system.logout()


def check_options(module):
    """Verify module options are sane"""
    certificate_file_name = module.params["certificate_file_name"]
    state = module.params["state"]

    if state in ["present"]:
        if not sign_on_url:
            msg = "A sign_on_url parameter must be provided"
            fail(module, msg=msg)
        if not signing_certificate:
            msg = "A signing_certificate parameter must be provided"
            fail(module, msg=msg)

def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            enabled=dict(required=False, type=bool, default=True),
            issuer=dict(required=False, default=None),
            name=dict(required=True),
            sign_on_url=dict(required=False, default=None),
            signed_assertion=dict(required=False, default=False),
            signed_response=dict(required=False, default=False),
            signing_certificate=dict(required=False, default=None),
            state=dict(default="present", choices=["stat", "present", "absent"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    check_options(module)
    execute_state(module)


if __name__ == "__main__":
    main()



# {
#   "command": "config.sso.idps.query",
#   "result": [
#       {
#           "enabled": "yes",
#           "issuer": "http://www.okta.com/exkra32oyyU6KCUCk2p7",
#           "name": "OKTA",
#           "sign_on_url": "https://infinidat.okta.com/app/infinidat_walthamiboxtest_1/exkra32oyyU6KCUCk2p7/sso/saml",
#           "signed_assertion": "no",
#           "signed_response": "no",
#           "signing_certificate_expiry": "2020021204000",
#           "signing_certificate_serial": "1704402004578"
#       }
#   ],
#   "number_of_objects": 1
# }

