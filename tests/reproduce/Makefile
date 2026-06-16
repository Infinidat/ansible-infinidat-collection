# Helper Makefile for tests/reproduce -- run the infini_vol functional tests.
#
# Authentication uses the module's native INFINIBOX_USER / INFINIBOX_PASSWORD
# environment variables, so the password is never placed on a command line or
# written to a file. Export INFINIBOX_PASSWORD beforehand, or you'll be prompted
# (input hidden).
#
#   make test-1443                                  # prompts for password
#   make test-1443 SYSTEM=ibox2503 POOL=mypool      # override targets
#   INFINIBOX_PASSWORD=secret make test-1443        # non-interactive
#
SHELL := /bin/bash

REPO_ROOT := $(abspath ../..)
VENV      := $(REPO_ROOT)/venv/bin

SYSTEM         ?= ibox2503
POOL           ?= PSUS_ANSIBLE_pool
INFINIBOX_USER ?= psus-eng
VOLUME_SEED    ?=
export INFINIBOX_USER

.PHONY: help reinstall test-1443 demo-1443 repro repro-teardown

help:
	@echo "Targets:"
	@echo "  reinstall        Build + install the collection from the source tree"
	@echo "  test-1443        PSDEV-1443 return-details test (single volume, asserts criteria)"
	@echo "  demo-1443        PSDEV-1443 against the customer's looped-create pattern (no stat step)"
	@echo "  repro            Run repro_infini_vol.yml (looped create + stat) against the array"
	@echo "  repro-teardown   Remove repro volumes for a seed: make repro-teardown VOLUME_SEED=<seed>"
	@echo ""
	@echo "Vars (override on the command line): SYSTEM=$(SYSTEM) POOL=$(POOL) INFINIBOX_USER=$(INFINIBOX_USER)"
	@echo "Auth: export INFINIBOX_PASSWORD, or you will be prompted (hidden)."

# Reinstall so the test always runs against the current source tree (FQCN
# modules load from the installed collection, not plugins/).
reinstall:
	@$(VENV)/ansible-galaxy collection install --force "$(REPO_ROOT)" \
		--collections-path $$HOME/.ansible/collections >/dev/null
	@echo "Collection (re)installed from $(REPO_ROOT)"

test-1443: reinstall
	@if [[ -z "$$INFINIBOX_PASSWORD" ]]; then \
		read -rsp "InfiniBox password for $(INFINIBOX_USER)@$(SYSTEM): " INFINIBOX_PASSWORD; echo; \
		export INFINIBOX_PASSWORD; \
	fi; \
	$(VENV)/ansible-playbook test_return_details_1443.yml \
		-e system=$(SYSTEM) -e pool=$(POOL)

demo-1443: reinstall
	@if [[ -z "$$INFINIBOX_PASSWORD" ]]; then \
		read -rsp "InfiniBox password for $(INFINIBOX_USER)@$(SYSTEM): " INFINIBOX_PASSWORD; echo; \
		export INFINIBOX_PASSWORD; \
	fi; \
	$(VENV)/ansible-playbook demo_customer_loop_1443.yml \
		-e system=$(SYSTEM) -e pool=$(POOL)

repro: reinstall
	@if [[ -z "$$INFINIBOX_PASSWORD" ]]; then \
		read -rsp "InfiniBox password for $(INFINIBOX_USER)@$(SYSTEM): " INFINIBOX_PASSWORD; echo; \
		export INFINIBOX_PASSWORD; \
	fi; \
	$(VENV)/ansible-playbook repro_infini_vol.yml \
		-e system=$(SYSTEM) -e pool=$(POOL)

repro-teardown: reinstall
	@if [[ -z "$(VOLUME_SEED)" ]]; then echo "Set VOLUME_SEED=<seed>, e.g. make repro-teardown VOLUME_SEED=Fl2zgGU2"; exit 1; fi; \
	if [[ -z "$$INFINIBOX_PASSWORD" ]]; then \
		read -rsp "InfiniBox password for $(INFINIBOX_USER)@$(SYSTEM): " INFINIBOX_PASSWORD; echo; \
		export INFINIBOX_PASSWORD; \
	fi; \
	$(VENV)/ansible-playbook repro_infini_vol.yml --tags teardown \
		-e system=$(SYSTEM) -e pool=$(POOL) -e volume_seed=$(VOLUME_SEED)
