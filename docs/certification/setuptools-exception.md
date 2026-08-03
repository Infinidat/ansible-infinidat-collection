# Certification exception: `setuptools<81` in requirements.txt

**Status:** ✅ **RESOLVED — cap removed 2026-08-03.** `infi.dtypes.wwn` 0.2.0
(without the `pkg_resources` namespace declaration) was published to PyPI, so the
`setuptools<81` line has been dropped from `requirements.txt`. This document is
retained as the historical record of the exception. See "Resolution" below.
**Date raised:** 2026-06-24
**Date resolved:** 2026-08-03
**Affected file:** `requirements.txt` (collection runtime dependencies)

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

`pkg_resources` was **removed in setuptools 81**. Therefore any environment
that resolves setuptools >= 81 cannot import a package that uses
`pkg_resources`, and every module in the collection fails before performing
any work.

When this exception was first raised (2026-06-24), the blocker was `infinisdk`
itself: 289.1.3 imported `pkg_resources` in `core/utils/environment.py` and
`entry_point.py`. **infinisdk 289.1.4 (released 2026-07-12) fixed this** — both
call sites now go through a new `core/utils/packaging_metadata.py` shim built
on `importlib.metadata`, and the published wheel contains no `pkg_resources`
references.

The pin is still required, however, because infinisdk's mandatory transitive
dependency **`infi.dtypes.wwn` imports `pkg_resources` at import time**:

- `infi/dtypes/wwn/__init__.py:1` —
  `__import__("pkg_resources").declare_namespace(__name__)`
  (imported via `infinisdk/core/translators_and_types.py`, which is on the
  `from infinisdk import InfiniBox` import path)

This cannot be resolved by upgrading: **0.1.1 is the latest `infi.dtypes.wwn`
on PyPI** (released 2015; the upstream repo has had no commits since 2016).

The rest of the dependency tree was audited (2026-07-16) and is clean:
`infi.dtypes.iqn`/`infi.dtypes.nqn` do not use `pkg_resources`, `flux` only
uses it on Python < 3.8, and `storage_interfaces` references it only in a
`__version__.py` module that is never imported at runtime.

## Reproduction

```console
# With setuptools < 81 (currently pinned) — works:
$ pip install 'setuptools<81' 'infinisdk==289.1.4'
$ python -c "from infinisdk import InfiniBox; print('OK')"
OK

# With setuptools >= 81 (what an uncapped EE build would resolve) — fails,
# even on infinisdk 289.1.4:
$ pip install 'setuptools==83.0.0' 'infinisdk==289.1.4'
$ python -c "from infinisdk import InfiniBox"
Traceback (most recent call last):
  ...
  File ".../infi/dtypes/wwn/__init__.py", line 1, in <module>
    __import__("pkg_resources").declare_namespace(__name__)
ModuleNotFoundError: No module named 'pkg_resources'
```

setuptools' own deprecation warning explicitly advises *"pin to Setuptools<81"*
until consumers migrate off `pkg_resources`.

## Resolution

The blocker was cleared upstream and the cap removed. What happened, in order:

1. ~~Raise the `importlib.metadata` migration with the `infinisdk`
   maintainers.~~ **Done** — fixed in infinisdk 289.1.4.
2. ~~Raise the `declare_namespace` removal with the `infi.dtypes.wwn`
   maintainers and get a fixed release published to PyPI.~~ **Done** —
   `infi.dtypes.wwn` **0.2.0** was published to PyPI on 2026-08-03, dropping the
   legacy `declare_namespace` call (its `__init__.py` no longer touches
   `pkg_resources`). Tracked as
   [infi.dtypes.wwn#2](https://github.com/Infinidat/infi.dtypes.wwn/issues/2),
   [PYSDK-242](https://jira.infinidat.com/browse/PYSDK-242), and
   [INFRADEV-17660](https://jira.infinidat.com/browse/INFRADEV-17660) (the PyPI
   release-access hurdle — one of three maintainer accounts under Infinidat
   control, gated behind a device-confirmation email — which was ultimately
   resolved).
3. ~~Bump the `infinisdk` floor to `>=289.1.4`, floor `infi.dtypes.wwn` to
   `>=0.2.0`, remove the `setuptools<81` line, and add the new infinisdk 289.1.4
   transitive deps.~~ **Done (2026-08-03)** — `requirements.txt` now floors
   `infinisdk>=289.1.4` and `infi.dtypes.wwn>=0.2.0`, carries no setuptools cap,
   and adds `infi.dtypes.nqn`, `click`, `colorama`, and `responses` to the
   explicit transitive list.
4. ~~Verify the collection imports with setuptools >= 81.~~ **Done** — in a
   clean virtualenv with **setuptools 83.0.0** (which ships no `pkg_resources`)
   plus `infinisdk==289.1.4` and `infi.dtypes.wwn==0.2.0`,
   `from infinisdk import InfiniBox` imports successfully:

   ```console
   $ python -c "import importlib.util as u; print(u.find_spec('pkg_resources'))"
   None
   $ pip install 'setuptools>=81' 'infinisdk>=289.1.4' 'infi.dtypes.wwn>=0.2.0'
   $ python -c "from infinisdk import InfiniBox; print('OK')"
   OK
   ```

The remaining recommended follow-up is to confirm the same import in a real
`ansible-builder` execution-environment build (not just a venv) the next time
the EE is rebuilt.

Tracked publicly as
[GitHub issue #25](https://github.com/Infinidat/ansible-infinidat-collection/issues/25)
and internally as
[PSDEV-1448](https://jira.infinidat.com/browse/PSDEV-1448).

## Related

- `requirements.txt` — the comment above the `infinisdk>=289.1.4` floor records
  why no setuptools cap is needed (the `setuptools<81` line has been removed).
