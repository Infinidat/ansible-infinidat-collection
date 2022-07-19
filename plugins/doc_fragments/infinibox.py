# -*- coding: utf-8 -*-
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright: (c) 2022, Infinidat <info@infinidat.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class ModuleDocFragment(object):

    # Standard Infinibox documentation fragment
    DOCUMENTATION = r'''
options:
  system:
    description:
      - Infinibox Hostname or IPv4 Address.
    type: str
    required: true
  user:
    description:
      - Infinibox User username with sufficient priveledges ( see notes ).
    type: str
    required: true
  password:
    description:
      - Infinibox User password.
    type: str
    required: true
notes:
  - This module requires infinisdk python library
  - You must set INFINIBOX_USER and INFINIBOX_PASSWORD environment variables
    if user and password arguments are not passed to the module directly
  - Ansible uses the infinisdk configuration file C(~/.infinidat/infinisdk.ini) if no credentials are provided.
    See U(http://infinisdk.readthedocs.io/en/latest/getting_started.html)
  - All Infinidat modules support check mode (--check). However, a dryrun that creates
    resources may fail if the resource dependencies are not met for a task.
    For example, consider a task that creates a volume in a pool.
    If the pool does not exist, the volume creation task will fail.
    It will fail even if there was a previous task in the playbook that would have created the pool but
    did not because the pool creation was also part of the dry run.
requirements:
  - python2 >= 2.7 or python3 >= 3.6
  - infinisdk (https://infinisdk.readthedocs.io/en/latest/)
'''
