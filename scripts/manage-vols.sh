#!/usr/bin/env bash

# Disable shellcheck: Check exit code directly with e.g. 'if mycmd;', not indirectly with $?.
# shellcheck disable=SC2181

# Create or delete many volumes and snapshots.
# Examples:
#   ./manage-vols.sh create_vols_and_snaps     1  5000
#   ./manage-vols.sh create_vols_and_snaps  5001 10000
#   ./manage-vols.sh create_vols_and_snaps 10001 15000
#   ./manage-vols.sh create_vols_and_snaps 15001 20000
#   ./manage-vols.sh create_vols_and_snaps 20001 25000
#   ./manage-vols.sh create_vols_and_snaps 25001 30000
#   ./manage-vols.sh create_vols_and_snaps 30001 35000
#   ./manage-vols.sh create_vols_and_snaps 35001 40000
#   ./manage-vols.sh create_vols_and_snaps 40001 45000

readonly TERM=xterm # tmux may set a different TERM confusing infinishell.
readonly ibox="ibox2503"
readonly user="psus_aadm"
readonly pass="123456"
readonly prefix="psus_aadm_"
readonly size="1GiB"
readonly pool="${prefix}pool"
readonly infinishell="infinishell --user $user --password $pass $ibox --no-paging"

readonly command="$1"
readonly vstart="$2"
readonly vend="$3"

function create_vol {
    # Create a volume
    local -r volume="$1"
    local -r cmd="vol.create name=$volume pool=$pool size=$size"
    echo "- Creating volume $volume"
    $infinishell --cmd="$cmd" 2>&1 | grep -E 'NAME_CONFLICT|created'
}

function create_snap {
    # Create a snapshot
    local -r volume="$1"
    local -r snap="$2"
    local -r cmd="vol.snap.create name=${snap} vol=${volume}"
    echo "- Creating snapshot $snap from volume $volume"
    $infinishell --cmd="$cmd" 2>&1 | grep -E 'NAME_CONFLICT|created'
}

function delete_vol {
    # Delete a volume or a snapshot
    local -r volume="$1"
    local -r cmd="vol.delete --yes vol=${volume}"
    echo "- Deleting volume $volume"
    $infinishell --cmd="$cmd" 2>&1 | grep -E 'No such volume|deleted'
}

function create_vols {
        for i in $(seq "$vstart" 1 "$vend"); do
        vol="${prefix}vol-${i}"
        until create_vol "$vol"; [ "$?" == 0 ]; do
            :
        done
    done
}

function create_snaps {
        for i in $(seq "$vstart" 1 "$vend"); do
        vol="${prefix}vol-${i}"
        snap="$vol-snap"
        until create_snap "$vol" "$snap"; [ "$?" == 0 ]; do
            :
        done
    done
}

function create_vols_and_snaps {
        for i in $(seq "$vstart" 1 "$vend"); do
        vol="${prefix}vol-${i}"
        snap="${prefix}vol-${i}-snap"
        until create_vol "$vol"; [ "$?" == 0 ]; do
            :
        done
        until create_snap "$vol" "$snap"; [ "$?" == 0 ]; do
            :
        done
    done
}

function delete_vols {
        for i in $(seq "$vstart" 1 "$vend"); do
        vol="${prefix}vol-${i}"
        until delete_vol "$vol"; [ "$?" == 0 ]; do
            :
        done
    done
}

function help {
    >&2 echo "Help me"
    exit 1
}

case "$command" in
    create_vols)
        create_vols
        ;;
    create_snaps)
        create_snaps
        ;;
    create_vols_and_snaps)
        create_vols_and_snaps
        ;;
    delete_vols)
        delete_vols
        ;;
    *)
        help
        ;;
esac


