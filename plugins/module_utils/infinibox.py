# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Infinidat <info@infinidat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import raise_from
try:
    import ansible.module_utils.errors
except (ImportError, ModuleNotFoundError):
    import errors  # Used during "make dev-hack-module-[present, stat, absent]"

try:
    from infinisdk import InfiniBox, core
    from infinisdk.core.exceptions import ObjectNotFound
except ImportError as imp_exc:
    HAS_INFINISDK = False
    INFINISDK_IMPORT_ERROR = imp_exc
else:
    HAS_INFINISDK = True
    INFINISDK_IMPORT_ERROR = None

HAS_ARROW = True
try:
    import arrow
except ImportError:
    HAS_ARROW = False
except Exception:
    HAS_INFINISDK = False

from functools import wraps
from os import environ
from os import path
from datetime import datetime
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


system = None


def unixMillisecondsToDate(unix_ms):
    return (datetime.utcfromtimestamp(unix_ms / 1000.), 'UTC')


def api_wrapper(func):
    """ Catch API Errors Decorator"""
    @wraps(func)
    def __wrapper(*args, **kwargs):
        module = args[0]
        try:
            return func(*args, **kwargs)
        except core.exceptions.APICommandException as e:
            module.fail_json(msg=e.message)
        except core.exceptions.SystemNotFoundException as e:
            module.fail_json(msg=e.message)
        except Exception:
            raise
    return __wrapper


def infinibox_argument_spec():
    """Return standard base dictionary used for the argument_spec argument in AnsibleModule"""
    return dict(
        system=dict(required=True),
        user=dict(required=True),
        password=dict(required=True, no_log=True),
    )


def infinibox_required_together():
    """Return the default list used for the required_together argument to AnsibleModule"""
    return [['user', 'password']]


def merge_two_dicts(dict1, dict2):
    """
    Merge two dicts into one and return.
    result = {**dict1, **dict2} only works in py3.5+.
    """
    result = dict1.copy()
    result.update(dict2)
    return result


@api_wrapper
def get_system(module):
    """
    Return System Object if it does not exist or Fail.
    Use a global system Infinibox object so that there will only be one
    system session used for this module instance.
    Enables execute_state() to log out of the only session properly.
    """
    global system

    if not system:
        # Create system and login
        box = module.params['system']
        user = module.params.get('user', None)
        password = module.params.get('password', None)
        if user and password:
            system = InfiniBox(box, auth=(user, password), use_ssl=True)
        elif environ.get('INFINIBOX_USER') and environ.get('INFINIBOX_PASSWORD'):
            system = InfiniBox(box,
                            auth=(environ.get('INFINIBOX_USER'),
                                    environ.get('INFINIBOX_PASSWORD')),
                            use_ssl=True)
        elif path.isfile(path.expanduser('~') + '/.infinidat/infinisdk.ini'):
            system = InfiniBox(box, use_ssl=True)
        else:
            module.fail_json(msg="You must set INFINIBOX_USER and INFINIBOX_PASSWORD environment variables or set username/password module arguments")

        try:
            system.login()
        except Exception:
            module.fail_json(msg="Infinibox authentication failed. Check your credentials")

    return system


@api_wrapper
def get_pool(module, system):
    """
    Return Pool. Try key look up using 'pool', or if that fails, 'name'.
    If the pool is not found, return None.
    """
    try:
        try:
            name = module.params['pool']
        except KeyError:
            try:
                name = module.params['name']
            except KeyError:
                name = module.params['object_name']  # For metadata
        return system.pools.get(name=name)
    except Exception:
        return None


@api_wrapper
def get_filesystem(module, system):
    """Return Filesystem or None"""
    try:
        try:
            filesystem = system.filesystems.get(name=module.params['filesystem'])
        except KeyError:
            try:
                filesystem = system.filesystems.get(name=module.params['name'])
            except KeyError:
                filesystem = system.filesystems.get(name=module.params['object_name'])
        return filesystem
    except Exception:
        return None


@api_wrapper
def get_export(module, system):
    """Return export if found or None if not found"""
    try:
        try:
            export_name = module.params['export']
        except KeyError:
            export_name = module.params['name']

        export = system.exports.get(export_path=export_name)
    except ObjectNotFound as err:
        return None

    return export


@api_wrapper
def get_volume(module, system):
    """Return Volume or None"""
    try:
        try:
            volume = system.volumes.get(name=module.params['name'])
        except KeyError:
            try:
                volume = system.volumes.get(name=module.params['volume'])
            except KeyError:
                volume = system.volumes.get(name=module.params['object_name']) # Used by metadata module
        return volume
    except Exception:
        return None


@api_wrapper
def get_net_space(module, system):
    """Return network space or None"""
    try:
        net_space = system.network_spaces.get(name=module.params['name'])
    except (KeyError, ObjectNotFound):
        return None
    return net_space


@api_wrapper
def get_vol_by_sn(module, system):
    """Return volume that matches the serial or None"""
    try:
        volume = system.volumes.get(serial=module.params['serial'])
    except Exception:
        return None
    return volume


@api_wrapper
def get_fs_by_sn(module, system):
    """Return filesystem that matches the serial or None"""
    try:
        filesystem = system.filesystems.get(serial=module.params['serial'])
    except Exception:
        return None
    return filesystem


@api_wrapper
def get_host(module, system):
    """Find a host by the name specified in the module"""
    host = None

    for a_host in system.hosts.to_list():
        a_host_name = a_host.get_name()
        try:
            host_param = module.params['name']
        except KeyError:
            try:
                host_param = module.params['host']
            except KeyError:
                host_param = module.params['object_name']  # For metadata

        if a_host_name == host_param:
            host = a_host
            break
    return host


@api_wrapper
def get_cluster(module, system):
    """Find a cluster by the name specified in the module"""
    cluster = None
    # print("dir:", dir(system))

    for a_cluster in system.host_clusters.to_list():
        a_cluster_name = a_cluster.get_name()
        try:
            cluster_param = module.params['name']
        except KeyError:
            try:
                cluster_param = module.params['cluster']
            except KeyError:
                cluster_param = module.params['object_name']  # For metadata

        if a_cluster_name == cluster_param:
            cluster = a_cluster
            break
    return cluster


@api_wrapper
def get_user(module, system):
    """Find a user by the user_name specified in the module"""
    user = None
    user_name = module.params['user_name']
    try:
        user = system.users.get(name=user_name)
    except ObjectNotFound:
        pass
    return user

def check_snapshot_lock_options(module):
    """
    Check if specified options are feasible for a snapshot.

    Prevent very long lock times.
    max_delta_minutes limits locks to 30 days (43200 minutes).

    This functionality is broken out from manage_snapshot_locks() to allow
    it to be called by create_snapshot() before the snapshot is actually
    created.
    """
    snapshot_lock_expires_at = module.params["snapshot_lock_expires_at"]

    if snapshot_lock_expires_at:  # Then user has specified wish to lock snap
        lock_expires_at = arrow.get(snapshot_lock_expires_at)

        # Check for lock in the past
        now = arrow.utcnow()
        if lock_expires_at <= now:
            msg = "Cannot lock snapshot with a snapshot_lock_expires_at "
            msg += "of '{0}' from the past".format(snapshot_lock_expires_at)
            module.fail_json(msg=msg)

        # Check for lock later than max lock, i.e. too far in future.
        max_delta_minutes = 43200  # 30 days in minutes
        max_lock_expires_at = now.shift(minutes=max_delta_minutes)
        if lock_expires_at >= max_lock_expires_at:
            msg = "snapshot_lock_expires_at exceeds {0} days in the future".format(
                max_delta_minutes // 24 // 60
            )
            module.fail_json(msg=msg)

def manage_snapshot_locks(module, snapshot):
    """
    Manage the locking of a snapshot. Check for bad lock times.
    See check_snapshot_lock_options() which has additional checks.
    """
    name = module.params["name"]
    snapshot_lock_expires_at = module.params["snapshot_lock_expires_at"]
    snap_is_locked = snapshot.get_lock_state() == "LOCKED"
    current_lock_expires_at = snapshot.get_lock_expires_at()
    changed = False

    check_snapshot_lock_options(module)

    if snapshot_lock_expires_at:  # Then user has specified wish to lock snap
        lock_expires_at = arrow.get(snapshot_lock_expires_at)
        if snap_is_locked and lock_expires_at < current_lock_expires_at:
            # Lock earlier than current lock
            msg = "snapshot_lock_expires_at '{0}' preceeds the current lock time of '{1}'".format(
                lock_expires_at, current_lock_expires_at
            )
            module.fail_json(msg=msg)
        elif snap_is_locked and lock_expires_at == current_lock_expires_at:
            # Lock already set to correct time
            pass
        else:
            # Set lock
            if not module.check_mode:
                snapshot.update_lock_expires_at(lock_expires_at)
            changed = True
    return changed

