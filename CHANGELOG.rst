==========
Change Log
==========

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
