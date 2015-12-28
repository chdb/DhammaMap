#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import hashlib
import hmac
import os
import json
import utils
import widget as W
import logging

from base64 import urlsafe_b64encode\
                 , urlsafe_b64decode

class Base64Error (Exception):
    '''invalid Base64 character or incorrect padding'''

def decodeToken (token, cfg, expected=None):
    try:
        td = _decode (token)
        # if expected:
            # tt = _tokenType (expected)
        if td.valid (cfg, expected):
            td.data['_ts'] = td.timeStamp
            return td.data  
    except Base64Error:
        logging.warning ('invalid Base64 in Token: %r', token)
    except:
        logging.exception('unexpected exception on decoding token: %r', token)       
    return None
    
def encodeVerifyToken (data, tt):
   # tt = _tokenType (tt)
    assert tt in ['signUp'
                 ,'pw1'
                 ,'pw2'
                 ], 'invalid TokenType: %s' % tt
    return _encode (tt, data)    
    
def encodeSessionToken (ssn, user=None):
    data = dict(ssn)
    if user:
        uid = user['_id']
        data ['_u'] = dict(user)
        return _encode ('auth', data, uid)
    return _encode ('anon', data)

TokenTypes = ( 'anon'
             , 'auth'
             , 'signUp'
             , 'pw1'
             , 'pw2'
             )
def _tokenType (code):   return TokenTypes [code]
def _tokenTypeCode (tt): return TokenTypes.index(tt)
#.........................................
        
class _TokenData (object):

    def __init__ (_s, token, tt, obj, bM, ts, uid=None):
        _s.bMac  = bM  
        _s.tokenType = tt  
        _s.timeStamp = ts
        _s.token = token 
        _s.uid   = uid
        _s.data  = obj
                 
    def maxAge (_s, cfg): 
        if   _s.tokenType == 'anon'  : return cfg['maxIdleAnon']
        elif _s.tokenType == 'auth'  : return cfg['maxIdleAuth']
        elif _s.tokenType == 'signUp': return cfg['maxAgeSignUpTok']
        elif _s.tokenType == 'pw1'   : return cfg['maxAgePasswordTok']
        elif _s.tokenType == 'pw2'   : return cfg['maxAgePassword2Tok']
        else: raise RuntimeError ('invalid token type')
                
    def valid (_s, cfg, expected=None): 
        """Checks encryption validity and expiry: whether the token is younger than maxAge seconds.
        Use neutral evaluation pathways to beat timing attacks.
        NB: return only success or failure - log shows why it failed but user mustn't know ! 
        """
        btt = _s.tokenType == 'anon' \
           or _s.tokenType == 'auth'  \
              if expected is None else \
              _s.tokenType == expected 
        bData = _s.data is not None #  and (type(_s.data) == dict)
        bTS = utils.validTimeStamp (_s.timeStamp, _s.maxAge(cfg))
        
        # check booleans in order of their initialisation
        if   not _s.bMac: x = 'Invalid MAC'
        elif not btt    : x = 'Invalid token type:{} expected:{}'.format(_s.tokenType, expected)
        elif not bData  : x = 'Invalid data object'
        else:    
            return bTS  #no logging if merely expired

        logging.warning ('%s in Token: %r', x, _s.token)
        return False 
 #.........................................          
# Some global constants to hold the lengths of component substrings of the token         
CH  = 1
TS  = 4
UID = 8
MAC = 20
   
def _hash (msg, ts):
    """hmac output of sha1 is 20 bytes irrespective of msg length"""
    k = W.W.keys (ts)
    return hmac.new (k, msg, hashlib.sha1).digest()

def _serialize (data):
    '''Generic data is stored in the token. The data could be a dict or any other serialisable type.
    However the data size is limited because currently it all goes into one cookie and 
    there is a max cookie size for some browsers so we place a limit in session.save()
    '''
    # ToDo: replace json with binary protocol cpickle
    # ToDo compression of data thats too long to fit otherwise: 
    # data = json.encode (data)
    # if len(data) > data_max: # 4K minus the other fields
        # level = (len(data) - data_max) * K  # experiment! or use level = 9
        # data = zlib.compress( data, level) 
        # if len(data) > data_max: 
            # assert False, 'oh dear!' todo - save some? data in datastore
        # return data, True
    # return data, False    # todo: encode a boolean in kch to indicate whether compressed
    #logging.debug ('serializing data = %r', data)
    s = json.dumps (data, separators=(',',':'))
    #logging.debug('serialized data: %r', s)     
    return s.encode('utf-8') #byte str
    
def _deserialize (data):
    try: 
        obj = json.loads (data)
        return obj # byteify(obj)
    except Exception, e:
        logging.exception(e)
        return None

def _encode (tokentype, obj, uid=None):
    """ obj is serializable session data
        returns a token string of base64 chars with iv and encrypted tokentype, uid and data
    """
    assert bool(uid) == (tokentype == 'auth')
    tt = _tokenTypeCode (tokentype)
    now = utils.sNow()
    if uid:                     
        # docs say length of ndb.model.id is 64 bit so assume range is C signed int64 (not C unsigned int64)
        assert uid >= -(2**63) ,'uid less than: -(2**63)'
        assert uid <    2**63  ,'uid more than: (2**63)-1'
        data = W._iBq.pack (now, tt, uid)   # ts + tt + uid
    else:                                                
        data = W._iB.pack (now, tt)         # ts + tt    
    data  += _serialize (obj)               # ts + tt + [uid +] data
    h20 = _hash (data, now)                                    
    return urlsafe_b64encode (data + h20)   # ts + tt + [uid +] data + mac
                                                             
def _decode (token):                                         
    """inverse of encode: return _TokenData"""               
    try:                                                     
        bytes = urlsafe_b64decode (token)   # ts + tt + [uid +] data + mac
    except TypeError:
        logging.exception('Base64: ')
        raise Base64Error
    
    ts, tt, uid = W._iBq.unpack_from (bytes)     # uid is arbitrary unless tt == 0 (1st 8 bytes of the MAC(20 bytes)).
    ttype = _tokenType (tt)
    if ttype == 'auth': 
        preDataLen = TS+CH+UID
    else:  
        preDataLen = TS+CH
        uid = None      # if ttype =! 'auth' then there was no uid, so delete arbitrary uid value
    data = bytes[ :-MAC]
    mac1 = bytes [-MAC: ] 
    mac2 = _hash (data, ts)
    bMac = utils.sameStr (mac1, mac2)
    data = _deserialize (data [preDataLen: ])
    return _TokenData (token, ttype, data, bMac, ts)
    