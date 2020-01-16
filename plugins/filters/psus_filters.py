# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Infinidat <info@infinidat.com>
# Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)

from ansible.errors import AnsibleError
import datetime

def delta_time(dt, **kwargs):
    """
    Add to the time.
    Ref: https://docs.python.org/3.6/library/datetime.html#timedelta-objects
    """
    return dt + datetime.timedelta(**kwargs)

class FilterModule(object):
    """
    A filter look up class for custom filter plugins.
    Ref: https://www.dasblinkenlichten.com/creating-ansible-filter-plugins/
    """
    def filters(self):
        """
        Lookup the filter function by name and execute it.
        """
        return self.filter_map

    filter_map = {
        'delta_time': delta_time,
    }
