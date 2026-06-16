# infini_vol customer-reported reproductions

Reproductions for three customer observations against
`plugins/modules/infini_vol.py`. These are diagnostic artifacts, not part of the
`ansible-test sanity` suite.

The local `ansible.cfg` here points `library`/`module_utils`/etc. at the source
tree (`../../plugins/...`), mirroring `playbooks/ansible.cfg`, so the
`infinidat.infinibox.*` modules resolve without a galaxy install. Always run from
inside this directory.

| Issue | What the customer saw | Reproduced by | Needs iBox? |
|-------|-----------------------|---------------|-------------|
| 1 | Volume created with no size, then resized (two ops in the IB audit log) | `repro_infini_vol.yml` | Yes |
| 2 | No way to get created volume details (serial/id/size) without a follow-up `stat` | `repro_infini_vol.yml` | Yes |
| 3 | PLAY RECAP shows `changed=1`, expected `changed=4` | `repro_issue3_changed_counting.yml` | No |

## Issue 3 — recap counting (runs locally, no credentials)

```bash
cd tests/reproduce
ansible-playbook repro_issue3_changed_counting.yml
```

Observe:

- The create loop prints **four** per-item lines `changed: [localhost] => (item=1..4)`.
  These are per-iteration *display* callbacks, not the recap counter.
- The **PLAY RECAP** reports `ok=6 changed=1`. The recap counts **tasks**, not loop
  iterations, and `ok` includes the changed task. Six tasks → `ok=6`; one task (the
  create loop) changed → `changed=1`. If loops counted per item, `ok` would be 18.
- The real per-volume signal is `creation_output.results[*].changed` — printed by the
  `Show volume creation` task (`created: True` ×4).

Comment out the three tasks after the create loop to get the "creation only" variant:
the recap becomes `ok=3 changed=1`. In both cases `changed=1` — adding the stat block
only adds read-only tasks, raising `ok` while leaving `changed` untouched. **Not a
module defect.**

## Issues 1 & 2 — two-step create and missing return details (needs an iBox)

The CI vault file `ibox_vars/iboxCICD.yaml` is not in the repo, so supply credentials
explicitly:

```bash
cd tests/reproduce
ansible-playbook repro_infini_vol.yml \
    -e system=<ibox-fqdn> -e user=<user> -e password=<password> \
    -e pool=<pool-name> -e volume_prefix=repro -vvv
```

Re-run with `--tags teardown` to delete the volumes the run created (repeatable).

Observe:

- **Issue 1** — In the InfiniBox audit/events log, each volume shows a `VOLUME_CREATE`
  (default size) immediately followed by a `VOLUME_RESIZE` to the requested size. The
  source is `create_volume()` at `plugins/modules/infini_vol.py:179-185`, which calls
  `system.volumes.create()` with no `size` and then a separate `volume.update_size()`.
- **Issue 2** — The `Show volume creation` debug prints only `changed`/`failed`/`msg`;
  serial, id and size appear only in the later `STAT` output. The `present` path exits
  with just `changed` + `msg` (`infini_vol.py:406`), which is why the follow-up stat is
  currently required.
