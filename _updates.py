# File: _updates.py

# -*- coding: utf-8 -*-
"""
Dummy module to satisfy JexBoss dependencies.
The original functionality checked for updates, which now points to dead links.
This dummy module prevents the ModuleNotFoundError and allows the script to run.
"""

global gl_http_pool

def set_http_pool(pool):
    """
    Configure http pool. This function is required by sincan2.py.
    """
    global gl_http_pool
    gl_http_pool = pool

def check_updates():
    """
    Dummy function. Returns False to indicate no updates are available.
    """
    return False

def auto_update():
    """
    Dummy function. Returns False to indicate an update did not occur.
    """
    return False
