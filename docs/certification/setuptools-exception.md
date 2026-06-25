# Certification exception: `setuptools<81` in requirements.txt

**Status:** Exception requested from Red Hat Automation Hub certification.
**Date raised:** 2026-06-24
**Affected file:** `requirements.txt` (collection runtime dependencies)
**Removal criteria:** Drop the pin once a released `infinisdk` no longer imports `pkg_resources` (see "Plan to remove" below).

## Context

During certification of `infinidat.infinibox` v1.8.1, the Automation Hub reviewer
flagged capped version specifiers in `requirements.txt` as a blocker, because
upper-bound caps can create unsatisfiable constraints when `ansible-builder`
resolves multiple collections together into an execution environment (EE).

Two caps were flagged:

- `resolvelib>=0.5.3,<1.1.0` — **removed.** `resolvelib` is a transitive
  dependency of `ansible-core`, which already constrains it; the cap was
  redundant and is gone.
- `setuptools<81` — **retained**, with this documented exception, because
  removing it breaks the collection at runtime.

## Why `setuptools<81` is load-bearing

The collection's required SDK, `infinisdk`, imports the `pkg_resources` module at
import time:

- `infinisdk/core/utils/environment.py:3` — `import pkg_resources`
  (imported transitively via `from infinisdk import InfiniBox`, through
  `infinisdk/core/api/api.py` and `infinisdk/infinibox/infinibox.py`)
- `infinisdk/entry_point.py:8` — `import pkg_resources`

`pkg_resources` was **removed in setuptools 81**. Therefore any environment that
resolves setuptools >= 81 cannot import the SDK, and every module in the
collection fails before performing any work.

This cannot be resolved by upgrading the dependency: **289.1.3 is the latest
`infinisdk` published on PyPI** (as of 2026-06-24), and it still imports
`pkg_resources`. `infinisdk` does not even declare `setuptools`/`pkg_resources`
in its own metadata — it assumes `pkg_resources` is present, as it historically
shipped with pip/setuptools.

## Reproduction

```console
# With setuptools < 81 (currently pinned) — works:
$ pip install 'setuptools<81' 'infinisdk==289.1.3'
$ python -c "from infinisdk import InfiniBox; print('OK')"
OK

# With setuptools >= 81 (what an uncapped EE build would resolve) — fails:
$ pip install 'setuptools==82.0.1'
$ python -c "from infinisdk import InfiniBox"
Traceback (most recent call last):
  ...
  File ".../infinisdk/core/utils/environment.py", line 3, in <module>
    import pkg_resources
ModuleNotFoundError: No module named 'pkg_resources'
```

setuptools' own deprecation warning explicitly advises *"pin to Setuptools<81"*
until consumers migrate off `pkg_resources`.

## Plan to remove

We agree with the reviewer's recommendation to migrate `infinisdk` off
`pkg_resources` to `importlib.metadata`. The action items are:

1. Raise the `importlib.metadata` migration with the `infinisdk` maintainers.
2. When a fixed `infinisdk` release is available, bump the floor in
   `requirements.txt` to that version and **remove the `setuptools<81` line**.
3. Verify in a clean EE build that the collection imports with setuptools >= 81.

Until then, the pin is the only thing keeping the certified collection
importable inside an execution environment.

## Related

- `requirements.txt` — inline comment on the `setuptools<81` line points here.
- `CLAUDE.md` — "Things that look weird but are intentional" notes the pin.
