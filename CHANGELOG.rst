==========
Change Log
==========

-------------------
v1.8.5 (2026-08-13)
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* psdev-1452: Exclude the gitignored ``infinidat/`` developer-convenience directory from collection builds via ``build_ignore`` in galaxy.yml. Releases 1.8.1 through 1.8.4 shipped a recursive symlink ``infinidat/infinibox -> ..`` in the Galaxy artifact (GitHub issue #26); the ansible-14.3.0 metapackage sdist dereferenced it and nested the collection inside itself 41 levels deep (ansible-community/ansible-build-data#720). Fix contributed by Daniel Brennand (@dbrennand) in GitHub PR #28.
* psdev-1452: Add a release guard to the publish target that fails if the built artifact contains any symlink, preventing this class of packaging defect from shipping again.

-------------------
v1.8.4 (2026-08-04)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1446: Remove the load-bearing ``setuptools<81`` upper-bound cap from requirements.txt, clearing the last capped specifier flagged during Red Hat Automation Hub certification. This is now safe because ``infi.dtypes.wwn`` 0.2.0 (published to PyPI) dropped the legacy ``pkg_resources`` namespace declaration. Also floors ``infinisdk>=289.1.4`` and ``infi.dtypes.wwn>=0.2.0`` and adds the ``infi.dtypes.nqn``, ``click``, ``colorama``, and ``responses`` transitive dependencies that infinisdk 289.1.4 introduced. Verified that ``from infinisdk import InfiniBox`` imports under setuptools 83. See docs/certification/setuptools-exception.md.
* psdev-1446: Fix README links for Automation Hub rendering: make the Changelog link an absolute GitHub URL (relative links do not resolve on Automation Hub) and convert the bare "using Ansible collections" URL to markdown link syntax.
* psdev-1446: Drop ``resolvelib`` from requirements.txt. It is not used by the collection modules; it is a transitive dependency of ansible-core, which already pins it to ``<1.1.0``. The unbounded entry could resolve to ``resolvelib>=1.1.0``, which ansible-galaxy rejects (``ansible-galaxy requires resolvelib<1.1.0,>=0.5.3``), breaking collection installs in a fresh venv or execution-environment build.

-------------------
v1.8.2 (2026-06-25)
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* psdev-1446: Resolve ansible-test sanity errors flagged during Red Hat Automation Hub certification: replace an ``assert`` with an explicit raise (no-assert), drop unused ``global`` declarations and an unused import (pylint), initialize variables before use in infini_map handle_stat (pylint), and fix pep8 spacing/comment issues.

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1446: Remove the resolvelib upper-bound version cap from requirements.txt to avoid execution-environment dependency conflicts.
* psdev-1446: Add bindep.txt declaring the system packages (libffi, openssl) needed to build the crypto stack in execution environments.
* psdev-1446: Clean up ansible-lint findings in playbooks/configure_array.yml (Jinja spacing, YAML comma spacing) and module documentation.
* psdev-1446: README updates for Automation Hub: markdown-formatted links, a Changelog section, a Support section, and removal of the internal GitLab link.
* psdev-1446: Document the load-bearing ``setuptools<81`` pin and its certification exception in docs/certification/setuptools-exception.md.

-------------------
v1.8.1
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* psdev-1441: infini_vol now creates a volume at the requested size in a single InfiniBox operation instead of creating then resizing.

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1443: infini_vol state present now returns the volume's details (serial, size, volume_id, etc.) under a 'volume' key, so a follow-up stat task is no longer needed to read them back.

-------------------
v1.8.0 (2026-05-28)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1438: Raise minimum ansible-core to 2.18; controller now requires Python 3.11 or newer.
* psdev-1438: Repin requirements-dev.txt to ansible-core>=2.18,<2.19 and ansible>=11,<12 to match the new floor.

-------------------
v1.7.1 (2026-05-28)
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* psdev-1437: Fix infini_metadata DOCUMENTATION YAML indent that broke Galaxy's ansible-doc import on v1.7.0.

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1437: Bake ansible-doc parse check into Makefile (test-docs-locally) so DOCUMENTATION YAML errors surface before publish.

-------------------
v1.7.0 (2026-05-06)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1437: Raise minimum ansible-core to 2.16; controller now requires Python 3.10 or newer.
* psdev-1437: Pin ansible-core (>=2.16,<2.17), ansible (>=9,<10), and infinisdk (>=225.1.1) so CI runs deterministically across pip resolves.
* psdev-1437: Add ci/Dockerfile for psusdev/gitlab-cicd:v0.15 (Ubuntu 22.04 / Python 3.10) and Makefile recipes (ci-image-build / -save / -deploy-hints) to build, archive, and deploy the CI image.
* psdev-1437: Migrate Gitlab CI to a Jammy runner host using rootless podman; jobs route via the jammy-podman tag.

-------------------
v1.6.0 (2024-09-04)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1352: Add state search_iboxes to infini_infinimetrics module. Allows one to find the Infiniboxes registered with an Infinimetrics.

-------------------
v1.5.0 (2024-07-10)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1330: Support serializing session data to disk to reduce log in/out events and to improve performance. Credentials will be saved to a file named '/tmp/infinibox_pickle_<IBOX>'. The collection uses the Python pickle module to save the API session data to file. The next Infinidat module executed is then able to load the session data. An optional parameter name 'stay_logged_in' has been added.  It defaults to False.  If True, session pickle files will be loaded if available when modules starts. When modules complete, session data will be persisted to this file and the module will not log out from the Infinibox. If False, modules will not use persistent sessions.
* psdev-1341: Add API pagination support to metadata search (GET).

-------------------
v1.4.6 (2024-04-26)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* Add test_create_resources_demo and test_remove_resources_demo playbooks.

-------------------
v1.4.5 (2024-04-11)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* Update CHANGELOG.

-------------------
v1.4.4 (2024-04-09)
-------------------

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1178: Add infini_infinimetrics module. Allows adding an Infinibox to Infinimetrics.
* psdev-1108: Extend configure_array example playbook to further demonstrate extensive customization of an Infinibox using Ansible.
* psdev-1222: Add pool threshold alarm setting support to infini_pool.

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* psdev-1221: Fix infini_notification_rule. Find the correct target ID when using a recipient. The ID cannot be assumed to be 3.

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1188: Refactor CICD to use Infinibox 2503.

-------------------
v1.4.3 (2024-02-13)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1150: Update galaxy.yml for publication on Automation Hub.

-------------------
v1.4.2 (2024-02-12)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1150: Update galaxy.yml for publication on Automation Hub.

-------------------
v1.4.1 (2024-02-06)
-------------------

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* Require Ansible >= 2.14.0

-------------------
v1.4.0 (2024-02-05)
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* The default for the write_protected parameter when creating a master volume or master file system has changed from true to false. For snapshots, the default is true.
* psdev-1147: Fix an issue network space module where when removing a space the management interface was not removed last. This is required.

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* psdev-1138: Add infini_sso module. Allow SSO configuration.
* psdev-1151: Add infini_fibre_channel_switch module. Allow renaming of FC switches.
* psdev-1148: Add infini_certificate module. Allow uploading SSL certificates.
* psdev-1045: Add infini_event module. Allow posting of custom events.
* Add infini_config module.
* Add infini_notification_rule module.
* Add infini_notification_target module.
* psdev-1108: Provide configure_array.yml playbook. This is an example playbook demonstrating detailed configuration of Infiniboxes. It is idempotent so may be run against new or existing Infiniboxes repeatedly.
* psdev-1147: Implement network space module present state to handle updating parameters in an existing network space. Add support for is_async option.
* psdev-1108: Add state "login" to infini_user module. This tests credentials. Added to support Active Directory testing.
* Add syslog_server script to allow testing of syslog notifications.
* Add new infini_users_repository module. Use this module to configure Active Directory and LDAP resournces on an Infinibox.
* Add new infini_metadata module. This module will set, get and remove metadata (keys and values) to and from objects of these types: ["cluster", "fs", "fs-snap", "host", "pool", "system", "vol", "vol-snap"].
* Add snapshot support to the infini_fs module. File system snapshot locks, regular and immutable are supported.

-------------------
v1.3.12 (2022-12-04)
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* Fix infini_vol's write_protected field handling.

-------------------
v1.3.11 (2022-12-03)
-------------------

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* Fix module sanity errors not flagged when run locally, but flagged when uploaded to the automation hub for certification.

--------------------
v1.3.10 (2022-12-03)
--------------------

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* Add documentation for the delta-time filter. The delta-time filter is used in test_create_resources.yml playbook.

-------------------
v1.3.9 (2022-12-02)
-------------------

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* Fix module sanity errors not flagged when run locally, but flagged when uploaded to the automation hub for certification.

-------------------
v1.3.8 (2022-12-01)
-------------------

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* Support thin and thick provisioning in infini_fs.
* Refactor module imports.
* In the test_create_resources.yml and test_remove_resources.yml example playbooks, run rescan-scsi-bus.sh on host.

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* Fix infini_vol stat state. Return the provisioning type (thin or thick) properly.

-------------------
v1.3.7 (2022-10-03)
-------------------

^^^^^^^^^^^^^^^^^^^^
Project Enhancements
^^^^^^^^^^^^^^^^^^^^
* Execute and pass `Ansible Sanity Tests <https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_testing.html#testing-tools>`_. This is in preparation for Ansible Automation Hub (AAH) certification.
* No longer pin module versions in requirements.txt. Record module versions used while testing within CICD using pip freeze.

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
* Add volume restore to infini_vol.

^^^^^^^^^^^
New Modules
^^^^^^^^^^^
* infini_cluster: Create, delete and modify host clusters on an Infinibox.
* infini_network_space: Create, delete and modify network spaces on an Infinibox.

^^^^^^^^^^^^^
New Playbooks
^^^^^^^^^^^^^
* infinisafe_demo_runtest.yml
* infinisafe_demo_setup.yml
* infinisafe_demo_teardown.yml

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* Fix collection path to module_utils when importing utility modules.
