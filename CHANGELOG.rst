==========
Change Log
==========


-------------------
v1.4.0 (2023-11-01)
-------------------

^^^^^^^^^
Bug Fixes
^^^^^^^^^
* The default for the write_protected parameter when creating a master volume or master file system has changed from true to false. For snapshots, the default is true.

^^^^^^^^^^^^^^^^^^^^
Feature Enhancements
^^^^^^^^^^^^^^^^^^^^
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