#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import os
import utils
import logging

from struct import Struct
try:
    from ndb import model
except ImportError: # pragma: no cover
    from google.appengine.ext.ndb import model

_i   = Struct(str('=i'))     # int(4) = means native endian
_q   = Struct(str('=q'))     # int(8) = means native endian
_i8sc= Struct(str('=i8sc'))  # int(4).str(8).ch = means native endian
_i16s= Struct(str('=i16s'))  # int(4).str(16) = means native endian

_iB  = Struct(str('=iB'))   # int(4).uint(1) = means native endian
_iBq = Struct(str('=iBq'))  # int(4).uint(1).int(8)

NewKeysDELAY = 30       #todo: pass delay from a config setting 

# Todo: ndb docs not clear - check that put() is updating cache so that get_by_id() uses same synced cache 
# and therefore minimising datastore reads
#otherwise implement memcache calls

class W (model.Model):
    data = model.BlobProperty (repeated=True, indexed=False)
    ID = 'xxx'
    list = []
    TSLen = 4
    KLen = 16
    ItemLen = TSLen + KLen
    
    @staticmethod
    def _newkeys(delay=0): 
        ts = utils.sNow()
        if delay:
            ts += delay # new keys come into effect after delay seconds
        return ts , os.urandom (W.KLen)

    @staticmethod
    def _put():
        d = [_i16s.pack (i[0], i[1]) for i in W.list]
        #logging.info('type (d) is %s', type (d))
        #logging.info('type (d[0]) is %s', type (d[0]))
        assert type (d)    is list
        assert type (d[0]) is str
        W(id=W.ID, data=d).put()

    @staticmethod
    def _get():
        d = W.get_by_id (W.ID)
        if d:
            W.list = [_i16s.unpack(i) for i in d.data]
        else:    
            W.list = [W._newkeys()]
            W._put()
        assert all (len(i[1]) == W.KLen for i in W.list)
        assert W.list == sorted(W.list)
        
        #Todo: test only - delete in prod code!
        # logging.info('################################################')
        # for i in W.list:
            # logging.info('key %d: %r', i[0], i[1])
        # logging.info('################################################')

    # @staticmethod
    # def keysNow():
        # return W.keys (utils.sNow())
        
    @staticmethod
    def keys (ts):
        W._get()
        if len(W.list) == 1:
            return W.list[0][1]
        r = next(i for i in W.list if i[0] <= ts)
        # raises StopIteration if ts precedes all timestamps - ie keys not found for this ts              
        return r[1] 

    @staticmethod
    def addNewKeys(): 
        W._get()
        W.list.insert (0, W._newkeys(NewKeysDELAY))  
        W._put()
        logging.info('################################################')
        for i in W.list:
            logging.info('key %d: %r', i[0], i[1])
        logging.info('################################################')

      
    @staticmethod
    def purge (maxAge):
        '''remove all items older than maxAge'''
        W._get()
        t = utils.sNow() - maxAge
        W.list = [i for i in W.list if i[0] >= t]
        W._put()
      