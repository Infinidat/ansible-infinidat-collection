#!/usr/bin/env bash

# Find the data that modules were first created.

function find_git_file_dates {
    for f in $(ls -1 ../plugins/modules/*.py); do
        git log --follow --date=format:'%Y-%m-%d' --format=%ad -- $f | tail -1 | tr --delete '\n'
        printf " $f\n" | sed  's?../plugins/modules/??'
    done
}

find_git_file_dates | sort

