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
version_added: 2.16.0
short_description: Create (present state) or remove (absent state) an Infinibox registration on an Infinimetrics.
description:
    - Create (present state) or remove (absent state) an Infinibox registration on an Infinimetrics.
author: David Ohlemacher (@ohlemacher)
options:
  infinimetrics_system:
    description:
      - Infinimetrics hostname or IPv4 Address.
    type: str
    required: true
  state:
    description:
      - Registers the Infinibox with Infinimetrics, when using state present.
      - For state absent, the Infinibox is deregistered from Infinimetrics.
    type: str
    required: false
    default: present
    choices: [ "present", "absent" ]
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

- name: Deregister IBOX from Infinimetrics
  infini_infinimetrics:
    infinimetrics_system: infinimetrics
    state: absent
    user: admin
    password: secret
    system: ibox001
"""

# RETURN = r''' # '''

import requests
import re

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


def imx_login_get(module, imx_session):
    """ Log into an IMX (GET) using credentials. Return csrfmiddlewaretoken or None. """
    path = f"https://{module.params.get('imx_system')}/auth/login/"
    payload = {
            'username': module.params.get('imx_user', None),
            'password': module.params.get('imx_password', None),
            }
    headers = None
    files = None
    response = imx_session.get(path, headers=headers, data=payload, files=files, verify=False)

    # Find the csrfmiddleware token
    token = None
    for line_bytes in response.iter_lines():
        line = str(line_bytes)
        # Example of line searched for:
        # <input type="hidden" name="csrfmiddlewaretoken" value="VUe6...m5Nl7y">'
        result = re.search(r'"csrfmiddlewaretoken" value="(\w+)"', line)
        if result:
            token = result.group(1)
            break
    return token


def imx_login_post(module, imx_session, token):
    """ Log into an IMX (POST) using credentials. Provide csrfmiddlewaretoken. """
    path = f"https://{module.params.get('imx_system')}/auth/login/"
    data = {
            'csrfmiddlewaretoken': token,
            'password': module.params.get('imx_password', None),
            'username': module.params.get('imx_user', None),
            }
    headers = {
            'referer': f'https://{module.params.get("imx_system")}',
            }
    response = imx_session.post(path, headers=headers, data=data, verify=False)


def imx_system_edit(module, imx_session, token):
    imx_system = module.params.get('imx_system')
    serial = module.params.get('ibox_serial')
    path = f"https://{imx_system}/system/{serial}/edit/"
    response = imx_session.get(path, verify=False)
    token = None
    for line_bytes in response.iter_lines():
        line = str(line_bytes)
        # Example of line searched for:
        # <input type="hidden" name="csrfmiddlewaretoken" value="Y2cPY4DLeQqrlY5UosApVDZq24qS8BPhYgpJkaLQCm3HTp8OWTijibaTUT4IoqSF">
        result = re.search(r'"csrfmiddlewaretoken" value="(\w+)"', line)
        if result:
            token = result.group(1)
            break
    return token


def imx_system_add(module, imx_session, token):
    imx_system = module.params.get('imx_system')
    ibox_readonly_user = module.params.get('ibox_readonly_user')
    ibox_readonly_password = module.params.get('ibox_readonly_password')
    ibox_serial = module.params.get('ibox_serial')
    ibox_url = module.params.get('ibox_url')
    path = f"https://{imx_system}/system/add/"
    headers = {
            'referer': f'https://{imx_system}/',
            }
    data = {
            'csrfmiddlewaretoken': token,
            'api_url': ibox_url,
            'api_username': ibox_readonly_user,
            'api_password': ibox_readonly_password,
            }
    response = imx_session.post(path, headers=headers, data=data, verify=False)

    # Check that the IBOX was added or was previously added.
    # Search for one of:
    #   - 'The system is already monitored'
    #   - add_progress url
    if ("The system is already" not in response.text or "monitored" not in response.text) \
            and (f"/system/{ibox_serial}/add_progress" not in response.text):
        msg = f"Cannot remove Infinibox {ibox_url} from infinimetrics {imx_system}. Text returned: {response.text}"
        module.fail_json(msg=msg)

    if "add_progress" in response.text:
        return True
    return False  # Previously added


def imx_system_delete(module, imx_session, token):
    imx_system = module.params.get('imx_system')
    serial = module.params.get('ibox_serial')
    ibox_url = module.params.get('ibox_url')
    path = f"https://{imx_system}/system/{serial}/remove/"
    headers = {
            'X-CSRFToken': token,
            'referer': f'https://{imx_system}/',
            }
    response = imx_session.delete(path, headers=headers, verify=False)

    # Check that the IBOX was removed or was previously removed
    # In response.return_code, search for 200
    if response.status_code not in [200]:
        msg = f"Cannot remove Infinibox {ibox_url} from infinimetrics {imx_system}. Status code: {response.status_code}"
        module.fail_json(msg=msg)


def handle_present(module):
    """ Handle the present state parameter """
    imx_system = module.params.get('imx_system')
    ibox_url = module.params.get('ibox_url')

    imx_session = requests.session()
    csrfmiddlewaretoken = imx_login_get(module, imx_session)
    imx_login_post(module, imx_session, csrfmiddlewaretoken)
    csrfmiddlewaretoken = imx_system_edit(module, imx_session, csrfmiddlewaretoken)
    is_newly_added = imx_system_add(module, imx_session, csrfmiddlewaretoken)

    if is_newly_added:
        msg=f"Infinibox {ibox_url} added to Infinimetrics {imx_system}"
        changed = True
    else:
        msg=f"Infinibox {ibox_url} previously added to Infinimetrics {imx_system}"
        changed = False

    result = dict(
            changed=changed,
            msg = msg,
            )
    module.exit_json(**result)


def handle_absent(module):
    """ Handle the absent state parameter. """
    imx_system = module.params.get('imx_system')
    serial = module.params.get('ibox_serial')

    imx_session = requests.session()
    csrfmiddlewaretoken = imx_login_get(module, imx_session)
    imx_login_post(module, imx_session, csrfmiddlewaretoken)
    csrfmiddlewaretoken = imx_system_edit(module, imx_session, csrfmiddlewaretoken)
    imx_system_delete(module, imx_session, csrfmiddlewaretoken)
    result = dict(
        changed=True,
        msg=f"Infinibox serial {serial} removed from Infinimetrics {imx_system}"
    )
    module.exit_json(**result)


def execute_state(module):
    """Handle states"""
    state = module.params["state"]
    try:
        if state == "present":
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
            ibox_serial=dict(required=True),
            ibox_url=dict(required=False),
            ibox_readonly_user=dict(required=False),
            ibox_readonly_password=dict(required=False, no_log=True),
            imx_system=dict(required=True),
            imx_user=dict(required=True),
            imx_password=dict(required=True, no_log=True),
            state=dict(default="present", choices=["present", "absent"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg=missing_required_lib("infinisdk"))

    execute_state(module)


if __name__ == "__main__":
    main()
