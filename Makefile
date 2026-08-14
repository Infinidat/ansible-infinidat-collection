# Copyright: (c) 2022, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# vim: set foldmethod=indent foldnestmax=1 foldcolumn=1:

# A Makefile for creating, running and testing Infinidat's Ansible collection.

### Dependencies ###
# - jq: https://stedolan.github.io/jq/
# - spruce: https://github.com/geofffranks/spruce
# - ansible: git@github.com:ansible/ansible.git

### environment ###
# Include an env file with secrets.  This exposes the secrets
# as envvars only for the life of make.  It does not
# pollute the environment persistently.
# Format:
# GALAXY_API_KEY=someAnsibleGalaxyApiKey
# The key only needs to be valid to use target galaxy-collection-publish.
# Getting a token:
# https://galaxy.ansible.com/ui/token/
#

_env = ~/.ssh/ansible-galaxy.sh
include $(_env)
export $(shell sed 's/=.*//' $(_env))

# Use color in Makefiles.
_use_color = true

include Makefile-help

### Vars ###
_version            	= $(shell spruce json galaxy.yml | jq '.version'   | sed 's?"??g')
_namespace          	= $(shell spruce json galaxy.yml | jq '.namespace' | sed 's?"??g')
_name               	= $(shell spruce json galaxy.yml | jq '.name'      | sed 's?"??g')
_install_path       	= ~/.ansible/collections
_install_path_local 	= $$HOME/.ansible/collections
_requirements-file  	= requirements.txt
_requirements-dev-file  = requirements-dev.txt
_user               	= psus-gitlab-cicd
_password_file      	= vault_password.txt
_password           	= $$(cat vault_password.txt)
_ibox_url              ?= ibox2503
_extra_vars            ?= ibox_vars/iboxCICD.yaml
_verbosity             ?= -vv
_infinishell_creds  	= --user $(_user) --password $(_password) $(_ibox_url)
SHELL               	= /bin/bash
_ansible_clone      	= /home/$$USER/workspace/ansible
_network_space_ips  	= 172.31.32.145 172.31.32.146 172.31.32.147 172.31.32.148 172.31.32.149 172.31.32.150
_modules                = "infini_cluster.py" "infini_export.py" "infini_host.py" "infini_network_space.py" "infini_port.py" "infini_vol.py" "infini_export_client.py" "infini_fs.py" "infini_map.py" "infini_pool.py" "infini_user.py"

# CI image: built on dev box, transferred to the runner host as a tarball,
# loaded into the gitlab-runner user's rootless podman image store.
_ci_image_name          = psusdev/gitlab-cicd
_ci_image_tag           = v0.16
_ci_image_ref           = $(_ci_image_name):$(_ci_image_tag)
_ci_image_dockerfile    = ci/Dockerfile
_ci_image_context       = ci
_ci_image_tar           = /tmp/psusdev-gitlab-cicd-$(_ci_image_tag).tar.gz
_ci_runner_host         = psus-ansible-runner
_ci_runner_user         = psus-eng

# Include, but do not fail if not found. Ignored by git. Use to temporarily set vars.
-include Makefile-vars
include Makefile-git

##@ General
setup: _test-venv _test-ubuntu  ## Setup Python requirements.
	@# Install pbr early to prevent errors with flux and gossip install.
	@# e.g. distutils.errors.DistutilsError: Could not find suitable distribution for Requirement.parse('pbr>=3.0')
	$(_python) -m ensurepip && \
	$(_python) -m pip install --upgrade pip && \
	$(_python) -m pip install --upgrade ansible ansible-lint pbr pdbpp && \
	$(_python) -m pip install --upgrade --requirement $(_requirements-file) && \
	$(_python) -m pip install --upgrade --requirement $(_requirements-dev-file) && \
	curl -s https://repo.infinidat.com/setup/main-stable | sudo sh - && \
	sudo apt install -y infinishell && \
	which ansible || (echo "Ansible not found. May need $$HOME/.local/bin in PATH"; exit 1)

_check-vars:
ifeq ($(strip $(GALAXY_API_KEY)),)
	@echo "GALAXY_API_KEY variable is unset" && false
endif

env-show: _check-vars
	@echo "GALAXY_API_KEY=[ set but redacted ]"

version: _check-vars  ## Show versions.
	@echo -e $(_begin)
	ansible --version
	@echo
	ansible-galaxy collection list
	@echo -e $(_finish)

_test-venv:
	@# Test that a venv is activated
ifndef VIRTUAL_ENV
	@echo "Error: Virtual environment not set"
	exit 1
endif

pylint:
	@echo -e $(_begin)
	cd plugins/modules && \
		pylint "$(_module_under_test).py"
	cd -
	@echo -e $(_finish)

pyfind:  ## Search project python files using: f='search term' make pyfind
	find . -name "*.py" | xargs grep -n "$$f" | egrep -v 'eggs|parts|\.git|external-projects|build'

##@ Galaxy

setup-galaxy: _test-venv
	@wget --quiet https://github.com/geofffranks/spruce/releases/download/v1.31.0/spruce-linux-amd64 && \
		mv spruce-linux-amd64 spruce && \
		chmod +x spruce && \
		sudo mv spruce /usr/local/bin && \
	wget --quiet https://github.com/jqlang/jq/releases/download/jq-1.7/jq-linux-amd64 && \
		mv jq-linux-amd64 jq && \
		chmod +x jq && \
		sudo mv jq /usr/local/bin && \
	echo "jq and spruce are installed"

_test-ubuntu:
	@if [ 'Ubuntu' = "$$(lsb_release -is)" ]; then \
		:; \
	else \
		echo "Error: Not running Ubuntu"; \
		exit 1; \
	fi

galaxy-collection-build: _test-venv  ## Build the collection. Use for local dev; publish enforces releasable separately.
	@echo -e $(_begin)
	rm -rf collections/
	ansible-galaxy collection build
	@echo -e $(_finish)

galaxy-collection-build-force: _test-venv  ## Force build the collection. Overwrite an existing collection file.
	@echo -e $(_begin)
	ansible-galaxy collection build --force
	@echo -e $(_finish)

galaxy-collection-build-release: _test-venv  ## Build the collection from a clean export of the release tag. No working-tree files can leak into the artifact.
	@echo -e $(_begin)
	@TMP=$$(mktemp -d) && \
	git archive v$(_version) | tar -x -C "$$TMP" && \
	( cd "$$TMP" && ansible-galaxy collection build --output-path "$(CURDIR)" --force ) && \
	rm -rf "$$TMP"
	@echo -e $(_finish)

_test-artifact-no-symlinks:
	@# Guard: the artifact must not contain symlinks. Gitignored paths (e.g. the
	@# infinidat/infinibox dev symlink) are invisible to git but are packed by
	@# ansible-galaxy collection build unless listed in galaxy.yml build_ignore.
	@# Releases 1.8.1-1.8.4 shipped a recursive symlink this way (PSDEV-1452,
	@# GitHub issue #26). First line of defense is galaxy-collection-build-release
	@# (clean-checkout build); this gate still catches tracked symlinks, which
	@# survive a git archive export.
	@echo -e $(_begin)
	@ART="./$(_namespace)-$(_name)-$(_version).tar.gz"; \
	test -f "$$ART" || { echo "Error: artifact $$ART not found"; exit 1; }; \
	if tar -tvf "$$ART" | grep -E '^l'; then \
		echo "Error: artifact $$ART contains symlinks (see above)"; \
		exit 1; \
	fi
	@echo -e $(_finish)

_test-artifact-files-tracked:
	@# Gate: every file in the artifact must be tracked in git at the release tag
	@# (MANIFEST.json and FILES.json are generated by ansible-galaxy build).
	@# Allowlist semantics: an untracked file in the artifact fails the publish,
	@# no matter how it got there. Tracked-but-excluded (build_ignore) is fine.
	@echo -e $(_begin)
	@ART="./$(_namespace)-$(_name)-$(_version).tar.gz"; \
	test -f "$$ART" || { echo "Error: artifact $$ART not found"; exit 1; }; \
	EXTRA=$$(comm -23 \
		<(tar -tf "$$ART" | grep -v '/$$' | grep -vE '^(MANIFEST|FILES)\.json$$' | sort -u) \
		<(git ls-tree -r --name-only v$(_version) | sort -u)); \
	if [ -n "$$EXTRA" ]; then \
		echo "Error: artifact $$ART contains files not tracked at tag v$(_version):"; \
		echo "$$EXTRA"; \
		exit 1; \
	fi
	@echo -e $(_finish)

galaxy-collection-publish: _test-venv _check-vars releasable galaxy-collection-build-release _test-artifact-no-symlinks _test-artifact-files-tracked  ## Publish the collection to https://galaxy.ansible.com/ using the API key provided.
	@echo -e $(_begin)
	@# Suppress recipe echo with @ so the --api-key value doesn't appear in stdout
	@# or make's recipe-echo. (ANSIBLE_GALAXY_TOKEN is not a documented ansible-galaxy
	@# env var; --api-key is the documented interface.)
	@ART="./$(_namespace)-$(_name)-$(_version).tar.gz"; \
	echo "Publishing: $$ART"; \
	ansible-galaxy collection publish "$$ART" --api-key "$(GALAXY_API_KEY)" -vv
	@echo "On Github:"
	@echo "    git push upstream-github develop"
	@echo "    git push upstream-github --tags develop"
	@echo -e $(_finish)

galaxy-collection-install: _test-venv  ## Download and install from galaxy.ansible.com. This will wipe $(_install_path).
	@echo -e $(_begin)
	ansible-galaxy collection install $(_namespace).$(_name) --collections-path $(_install_path) --force
	@echo -e $(_finish)

galaxy-collection-install-locally: _test-venv  ## Download and install from local tar file.
	@echo -e $(_begin)
	ansible-galaxy collection install --force $(_namespace)-$(_name)-$(_version).tar.gz --collections-path $(_install_path_local)
	@echo -e $(_finish)

##@ Playbook Testing
_test-playbook: _test-venv
	@# Run a playbook specified by an envvar.
	@# See README-DEV.md
	cd playbooks && \
		if [ ! -e "../vault_password.txt" ]; then \
			echo "Please add your vault password to vault_password.txt"; \
			exit 1; \
		fi; \
		echo "Installing collection..."; \
		ansible-galaxy collection install --force "$${PWD}/.."; \
		echo "Running playbook..."; \
		ansible-playbook \
			$$ask_become_pass \
			$(_verbosity) \
			--inventory "inventory" \
			--extra-vars "@../$(_extra_vars)" \
			--vault-password-file ../vault_password.txt \
			"$$playbook_name"; \
	cd -

test-create-resources:  ## Run full creation test suite as run by Gitlab CICD.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=test_create_resources.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-resources:  ## Run full removal test suite as run by Gitlab CICD.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=test_remove_resources.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-create-resources-demo:  ## Run stripped down version of creation test suite. Use for demos.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=test_create_resources_demo.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-resources-demo:  ## Run stripped down version of removal test suite. Use for demos.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=test_remove_resources_demo.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-create-snapshots:  ## Test creating immutable snapshots.
	@echo -e $(_begin)
	playbook_name=test_create_snapshots.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-snapshots:  ## Test removing immutable snapshots (teardown).
	@echo -e $(_begin)
	playbook_name=test_remove_snapshots.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-create-net-spaces: dev-install-modules-to-local-collection  ## Test creating network spaces.
	@echo -e $(_begin)
	playbook_name=test_create_network_spaces.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-net-spaces:  ## Test removing net spaces (teardown).
	@echo -e $(_begin)
	playbook_name=test_remove_network_spaces.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-create-map-cluster:  ## Run full creation test suite as run by Gitlab CICD.
	@echo -e $(_begin)
	playbook_name=test_create_map_cluster.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-map-cluster:  ## Run full removal  test suite as run by Gitlab CICD.
	@echo -e $(_begin)
	playbook_name=test_remove_map_cluster.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-create-volumes:  ## Run volume creation tests.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=test_create_volumes.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-volumes:  ## Run volume removal tests.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=test_remove_volumes.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-create-metadata:  ## Run metadata creation tests.
	@echo -e $(_begin)
	ansible-galaxy collection install --force "$${PWD}"
	ask_become_pass="" playbook_name=test_create_metadata.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-remove-metadata:  ## Run metadata removal tests.
	@echo -e $(_begin)
	ask_become_pass="" playbook_name=test_remove_metadata.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-search-metadata:  ## Run metadata search tests.
	@echo -e $(_begin)
	ask_become_pass="" playbook_name=test_search_metadata.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-config:  ## Run config tests
	@echo -e $(_begin)
	ansible-galaxy collection install --force "$${PWD}"
	ask_become_pass="" playbook_name=test_config_sample.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-notification-rules:  ## Run notification rule tests
	@echo -e $(_begin)
	ansible-galaxy collection install --force "$${PWD}"
	ask_become_pass="" playbook_name=test_notification_rules_sample.yml $(_make) _test-playbook
	@echo -e $(_finish)

test-persist_api_session:  ## Run tasks that use IBOX API session data that is persisted to disk.
	@echo -e $(_begin)
	ansible-galaxy collection install --force "$${PWD}"
	ask_become_pass="" playbook_name=test_persist_api_session.yml $(_make) _test-playbook
	@echo -e $(_finish)

##@ Solution Examples
configure-array:  ## Configure an Infinibox.
	@echo -e $(_begin)
	ansible-galaxy collection install --force "$${PWD}"
	_extra_vars="ibox_vars/vibox.yaml" ask_become_pass="" playbook_name="configure_array.yml" $(_make) _test-playbook
	@echo -e $(_finish)

# deconfigure-array:  ## Remove some Infinibox configurations set by the configure-array recipe.
# 	@echo -e $(_begin)
# 	ansible-galaxy collection install --force "$${PWD}"
# 	ask_become_pass="" playbook_name=deconfigure_array.yml $(_make) _test-playbook
# 	@echo -e $(_finish)

##@ Infinisafe Demo

infinisafe-demo-setup:  ## Setup infinisafe demo.
	@echo -e $(_begin)
	playbook_name=infinisafe_demo_setup.yml $(_make) _test-playbook
	@echo -e $(_finish)

infinisafe-demo-runtest:  ## Run tests on infinisafe demo snapshot on forensics host.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=infinisafe_demo_runtest.yml $(_make) _test-playbook
	@echo -e $(_finish)

infinisafe-demo-teardown:  ## Teardown infinisafe demo.
	@echo -e $(_begin)
	ask_become_pass="-K" playbook_name=infinisafe_demo_teardown.yml $(_make) _test-playbook
	@echo -e $(_finish)

##@ Hacking
# _module_under_test = infini_certificate
# _module_under_test = infini_cluster
# _module_under_test = infini_config
# _module_under_test = infini_event
# _module_under_test = infini_fibre_channel_switch
# _module_under_test = infini_fs
# _module_under_test = infini_host
_module_under_test = infini_infinimetrics
# _module_under_test = infini_map
# _module_under_test = infini_metadata
# _module_under_test = infini_network_space
# _module_under_test = infini_notification_rule
# _module_under_test = infini_notification_target
# _module_under_test = infini_pool
# _module_under_test = infini_sso
# _module_under_test = infini_user
# _module_under_test = infini_users_repository
# _module_under_test = infini_vol

dev-hack-create-links:  ## Create soft links inside an Ansible clone to allow module hacking.
	@echo "HACK - Creating hacking module links"
	@if [ ! -d "$(_ansible_clone)" ]; then \
		echo "Ansible clone not found"; \
		exit 1; \
	fi
	@mkdir -p "$(_ansible_clone)/lib/ansible/modules/infi"
	@for m in $(_modules); do \
		ln --force --symbolic $$(pwd)/plugins/modules/$$m $(_ansible_clone)/lib/ansible/modules/infi/$$m; \
	done
	@echo "HACK - Creating hacking module_utils links $(_module_utilities)"
	@ln --force --symbolic "$$(pwd)/plugins/module_utils/infinibox.py" "$(_ansible_clone)/lib/ansible/module_utils/infinibox.py" && \
	echo ln --force --symbolic "$$(pwd)/plugins/module_utils/infinibox.py" "$${HOME}/.local/lib/$(_python)/site-packages/ansible_collections/infinidat/infinibox/plugins/module_utils/infinibox.py" && \
	echo "HACK - Linking module_utils to ansible site-packages to allow changes to be used for dev" && \
	echo "HACK - Site packages: $$HOME/.local/lib/$(_python)/site-packages/ansible_collections/infinidat" && \
	echo utils_path="$$HOME/.local/lib/$(_python)/site-packages/ansible_collections/infinidat/infinibox/plugins/module_utils" && \
	echo mv "$$utils_path/infinibox.py" "$$utils_path/infinibox_orig.py" && \
	echo ln --force --symbolic "$$(pwd)/plugins/module_utils/infinibox.py" "$$utils_path/infinibox.py"

_dev-hack-module: dev-hack-create-links  # Run module. PDB is available using breakpoint().
	@echo "_module_under_test: $(_module_under_test)"
	@echo "state: $$state"
	@echo
	JSON_IN="./tests/hacking/$(_module_under_test)_$${state}.json" && \
	if [[ ! -a "$$JSON_IN" ]]; then \
		>&2 echo "Error: $$JSON_IN not found"; \
		exit; \
	fi; \
	source $(_ansible_clone)/hacking/env-setup 1> /dev/null 2> /dev/null && \
	ANSIBLE_HOME=/home/$$USER/workspace/ansible \
	PYTHONPATH="$$PYTHONPATH:./plugins/modules" \
	PYTHONPATH="$$PYTHONPATH:./plugins/module_utils" \
	PYTHONPATH="$$PYTHONPATH:$$ANSIBLE_HOME/lib" \
	PYTHONPATH="$$PYTHONPATH:$$ANSIBLE_HOME/hacking/build_library/build_ansible" \
	"$(_python)" -m "$(_module_under_test)" "$$JSON_IN" 2>&1 | \
		grep -v 'Unverified HTTPS request'

_dev-hack-module-jq:  # If module is running to the point of returning json, use this to run it and prettyprint using jq.
	@$(_make) _dev-hack-module | egrep 'changed|failed' | jq '.'

dev-hack-module-stat:  ## Hack stat.
	@state=stat    $(_make) _dev-hack-module

dev-hack-module-stat-jq:  ## Hack stat with jq.
	@state=stat    $(_make) _dev-hack-module-jq

dev-hack-module-present:  ## Hack present.
	@state=present $(_make) _dev-hack-module

dev-hack-module-present-jq:  ## Hack present with jq.
	@state=present $(_make) _dev-hack-module-jq

dev-hack-module-search:  ## Hack search.
	@state=search $(_make) _dev-hack-module

dev-hack-module-search-jq:  ## Hack search with jq.
	@state=search $(_make) _dev-hack-module-jq

dev-hack-module-search-iboxes:  ## Hack search.
	@state=search_iboxes $(_make) _dev-hack-module

dev-hack-module-search-iboxes-jq:  ## Hack search with jq.
	@state=search_iboxes $(_make) _dev-hack-module-jq

dev-hack-module-absent:  ## Hack absent.
	@state=absent $(_make) _dev-hack-module

dev-hack-module-absent-jq:  ## Hack absent with jq.
	@state=absent $(_make) _dev-hack-module-jq

dev-hack-module-login:  ## Hack login for infini_user module.
	@state=login $(_make) _dev-hack-module

dev-hack-module-login-jq:  ## Hack login for infini_user module with jq.
	@state=login $(_make) _dev-hack-module-jq

dev-hack-module-rename:  ## Hack rename for infini_fibre_channel_switch module.
	@state=rename $(_make) _dev-hack-module

dev-hack-module-rename-jq:  ## Hack rename for infini_user module with jq.
	@state=rename $(_make) _dev-hack-module-jq

dev-hack-module-test-jq:  ## Hack testing with multiple recipes.
	@>&2 echo "Testing module $(_module_under_test)" && sleep 1
	$(_make) dev-hack-module-absent-jq
	$(_make) dev-hack-module-stat-jq
	$(_make) dev-hack-module-present-jq
	$(_make) dev-hack-module-present-jq
	$(_make) dev-hack-module-stat-jq
	$(_make) dev-hack-module-absent-jq
	$(_make) dev-hack-module-absent-jq
	$(_make) dev-hack-module-stat-jq

##@ Test Module
_module = infini_event.py

find-default-module-path:  ## Find module path.
	ansible-config list | spruce json | jq '.DEFAULT_MODULE_PATH.default' | sed 's?"??g'

_collection_local_path = ~/.ansible/collections/ansible_collections/infinidat/infinibox/plugins
dev-install-modules-to-local-collection:  ## Copy modules to local collection
	@echo -e $(_begin)
	@echo "local collection path: $(_collection_local_path)"
	@echo "Installing modules locally"
	@cp plugins/modules/*.py $(_collection_local_path)/modules
	@echo "Installing utilities locally"
	@cp plugins/module_utils/*.py $(_collection_local_path)/module_utils
	@echo "Installing filters locally"
	@cp plugins/filter/*.py $(_collection_local_path)/filter
	@echo -e $(_finish)

##@ ansible-test
test-sanity:  ## Run ansible sanity tests. Runs within its own container.
	@# in accordance with
	@# https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#testing-collections
	@# This runs on a collection installed from galaxy. This makes it
	@# somewhat useless for dev and debugging. Use target test-sanity-locally.
	@ansible-test sanity --docker default -v

_setup-sanity-locally: _test-venv galaxy-collection-build-force galaxy-collection-install-locally
	@# Setup a test env. Run from within an activated venv (enforced by _test-venv).
	cd $(_install_path_local)/ansible_collections/infinidat/infinibox && \
		$(_python) -m pip install --upgrade pip && \
		$(_python) -m pip install --upgrade --requirement $(_requirements-file)

test-sanity-locally: _setup-sanity-locally  ## Run ansible sanity tests locally.
	@# in accordance with
	@# https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#testing-collections
	@# This runs on a collection installed locally making it useful for dev and debugging.
	cd $(_install_path_local)/ansible_collections/infinidat/infinibox && \
		ansible-test sanity --docker default --requirements $(_requirements-file)

test-docs-locally: _setup-sanity-locally  ## Verify ansible-doc parses every module. Mirrors Galaxy's import-time check; catches DOCUMENTATION YAML errors that sanity does not.
	@echo -e $(_begin)
	@# Galaxy's importer runs `ansible-doc --type module --json <FQCNs>` after install.
	@# Doc-string YAML errors slip past `ansible-test sanity` but break Galaxy import,
	@# so run the same check locally before publish.
	@cd $(_install_path_local)/ansible_collections/$(_namespace)/$(_name) && \
		fqcns=$$(ls plugins/modules/infini_*.py | xargs -n1 basename | sed 's|\.py$$||; s|^|$(_namespace).$(_name).|') && \
		ansible-doc --type module --json $$fqcns > /dev/null && \
		echo "All module docs parsed successfully."
	@echo -e $(_finish)

test-sanity-locally-all: galaxy-collection-build-force galaxy-collection-install-locally test-sanity-locally test-docs-locally  ## Run all sanity tests locally.
	@# Run local build, install, sanity test, and doc parse check.
	@# Note that this will wipe $(_install_path_local).
	@echo "test-sanity-locally-all completed"

##@ CI Image
ci-image-build:  ## Build the gitlab-cicd container image locally with podman.
	@echo -e $(_begin)
	podman build --tag $(_ci_image_ref) --file $(_ci_image_dockerfile) $(_ci_image_context)
	@podman images $(_ci_image_name)
	@echo -e $(_finish)

ci-image-save: ci-image-build  ## Build and save the gitlab-cicd image to a gzipped tar.
	@echo -e $(_begin)
	podman save $(_ci_image_ref) | gzip > $(_ci_image_tar)
	@ls -lh $(_ci_image_tar)
	@echo -e $(_finish)

ci-image-deploy-hints: ci-image-save  ## Print steps to deploy the saved image to the runner host.
	@echo -e $(_begin)
	@echo
	@echo "Built image:    $(_ci_image_ref)"
	@echo "Saved tarball:  $(_ci_image_tar)"
	@echo
	@echo "1. Copy the tarball to the runner host:"
	@echo
	@echo "    scp $(_ci_image_tar) $(_ci_runner_user)@$(_ci_runner_host):/tmp/"
	@echo
	@echo "2. Load it into the gitlab-runner user's rootless podman storage:"
	@echo
	@echo "    ssh $(_ci_runner_user)@$(_ci_runner_host)"
	@echo "    sudo machinectl shell gitlab-runner@"
	@echo "    gunzip -c $(_ci_image_tar) | podman load"
	@echo "    podman images | grep $(_ci_image_name)"
	@echo "    exit"
	@echo
	@echo "3. Set pull_policy so the runner uses the local image. Add or update"
	@echo "   under [runners.docker] in /etc/gitlab-runner/config.toml:"
	@echo
	@echo "    pull_policy = \"if-not-present\""
	@echo
	@echo "   The runner auto-reloads config; no restart needed."
	@echo
	@echo "4. Bump .gitlab-ci.yml to image: $(_ci_image_ref) and add tags: [jammy-podman]."
	@echo -e $(_finish)

##@ IBox
infinishell:  ## Run infinishell.
	@# Infinishell will not work correctly within tmux if the TERM is not set.
	@echo "To watch events: event.watch username="$(_user)" exclude=USER_LOGGED_OUT,USER_LOGIN_SUCCESS,USER_LOGIN_FAILURE,REQUEST_AUTHENTICATION_FAILURE tail_length=20"
	@TERM=xterm infinishell $(_infinishell_creds) --json

infinishell-json:  # Run infinishell with JSON output.
	@TERM=xterm infinishell --json $(_infinishell_creds)

infinishell-events:  # Run infinishell with hint to watch events.
	@TERM=xterm echo "Command: event.watch username=$(_user) exclude=USER_LOGGED_OUT,USER_LOGIN_SUCCESS,USER_SESSION_EXPIRED,USER_LOGIN_FAILURE tail_length=35"
	@TERM=xterm infinishell $(_infinishell_creds)

infinishell-network-space-iscsi-create:  ## Create a network space using infinishell.
	@echo -e $(_begin)
	@TERM=xterm infinishell --cmd="config.net_space.create name=iSCSI service=iSCSI interface=PG1 network=172.31.32.0/19 -y" $(_infinishell_creds) 2>&1 \
		| egrep 'created|already exists' && \
	for ip in $(_network_space_ips); do \
		echo "Creating IP $$ip" && \
		TERM=xterm infinishell --cmd="config.net_space.ip.create net_space=iSCSI ip_address=$$ip -y" $(_infinishell_creds) 2>&1 \
			| egrep 'created|NET_SPACE_ADDRESS_CONFLICT' && \
		echo "Enabling IP $$ip"; \
	done
	@echo -e $(_finish)

infinishell-network-space-iscsi-delete:  ## Delete a network space using infinishell.
	@echo -e $(_begin)
	@for ip in $(_network_space_ips); do \
		echo "Disabling IP $$ip" && \
		TERM=xterm infinishell --cmd="config.net_space.ip.disable net_space=iSCSI ip_address=$$ip -y" $(_infinishell_creds) 2>&1 \
			| egrep 'disabled|IP_ADDRESS_ALREADY_DISABLED|no such IP address|No such network space' && \
		echo "Deleting IP $$ip" && \
		TERM=xterm infinishell --cmd="config.net_space.ip.delete  net_space=iSCSI ip_address=$$ip -y" $(_infinishell_creds) 2>&1 \
			| egrep '$$ip deleted|no such IP address|No such network space';  \
	done
	@echo
	@echo "Deleting network space iSCSI" && \
	TERM=xterm infinishell --cmd="config.net_space.delete net_space=iSCSI -y" $(_infinishell_creds) 2>&1 \
		| egrep 'deleted|No such network space';
	@echo -e $(_finish)

##@ Certificates and Credentials
create-cert:  ## Create a self signed SSL certificate for use with an Infinibox.
	@# Ref: https://wiki.infinidat.com/pages/viewpage.action?pageId=45624136
	@# Ref: https://support.infinidat.com/hc/en-us/articles/10106396511133-Communicating-with-InfiniBox-using-an-SSL-certificate
	@# Ref: https://www.digicert.com/kb/ssl-support/openssl-quick-reference-guide.htm
	@FQDN="vbox-ps-01.lab.gdc.il.infinidat.com" && \
	CERTIFICATE_SUBJECT_NAME="/C=US/ST=Massachusetts/OU=PSUS/O=Infinidat/CN=$$FQDN" && \
	CSR="ca.csr" && \
	KEY="private-key.pem" && \
	CERT="signed-certificate-no-pkey.pem" && \
	CONCAT="signed-certificate-with-pkey.pem" && \
	DAYS="18250" && \
	\
	echo "== Generating private key file $$KEY" && \
	openssl req -new -newkey rsa:2048 -subj "$$CERTIFICATE_SUBJECT_NAME" -nodes -out "$$CSR" -keyout "$$KEY" && \
	\
	echo "== Generating CSR file $$CSR" && \
	openssl req -new -subj "$$CERTIFICATE_SUBJECT_NAME" -key "$$KEY" -out "$$CSR" && \
	\
	echo "== Generating crt file $$CERT" && \
	openssl x509 -signkey "$$KEY" -days "$$DAYS" -req -in "$$CSR" -out "$$CERT" && \
	\
	echo "== Creating $$CONCAT containing both" && \
	cat "$$CERT" "$$KEY" > "$$CONCAT"

edit-extra-vars:  ## Edit the extra vars file using ansible vault. One must exit ansible-vault to write changes.
	@ansible-vault edit --vault-password-file "$(_password_file)" "$(_extra_vars)"
