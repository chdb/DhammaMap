#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

# debug.py has test code that only runs in debug mode

from google.appengine.api import memcache
from webapp2 import get_app
import time


def save (mode, id, data):
    if get_app().debug:
        key = mode + id
        memcache.set(key, data)


def show (h, mode, id):
    if get_app().debug:
        key = mode + id
        tries = 3
        data = memcache.get(key)
        while tries:
            if data:
                memcache.delete(key)
                break
            tries -=1
            time.sleep(1)

        if data:
            h.flash('TEST: An email has been sent:<br>%s' % data)
        else:        
            h.flash('TEST: no data')
