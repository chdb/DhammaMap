#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import hashlib
import hmac
import os
from base64 import urlsafe_b64encode\
                 , urlsafe_b64decode
#from Crypto import Random
from Crypto.Cipher import Blowfish
from google.appengine.api import memcache
#from webapp2_extras import json
import json
# try:
    # from ndb import model
# except ImportError: # pragma: no cover
    # from google.appengine.ext.ndb import model
#from UserModels import User
import utils
import widget as W
import logging

class Base64Error (Exception):
    '''invalid Base64 character or incorrect padding'''

#tokentype
AnonSession = 0 # 'n'
AuthSession = 1 # 'u'
VerifySignUp= 2 # 's'
ResetPWord1 = 3 # 'p'
ResetPWord2 = 4 # 'q'
#ttString = 'nuvp'

#Todo:  1) test if checkIV() is working - emit log if memcache fails
    #   2) IMPLEMENT param to encode(new) new==True at login
    #   4) decode(new) to compare IP when new==False and if different decode() fails u

def _tokenType (tt):
  # if tt == 'n':   return AnonSession
  # if tt == 'u':   return AuthSession
    if tt == 's':   return VerifySignUp
    if tt == 'p':   return ResetPWord1
    if tt == 'q':   return ResetPWord2
    assert False
     
def decodeToken (token, cfg, tt=None):
    try:
        td = _decode (token)
        if tt:
            tt = _tokenType (tt)
        if td.valid (cfg, tt):
            return td.data  
    except Base64Error:
        logging.warning ('invalid Base64 in Token: %r', token)
    except:
        logging.exception('unexpected exception on decoding token: %r', token)
    return None
    
def encodeVerifyToken (data, tt):
    tt = _tokenType (tt)
    return _encode (tt, data)    
    
def encodeSessionToken (sess): #, user=None
    data = dict(sess)
    # if user:
        # uid = user['_id']
        # data ['_u'] = dict(user)
        # return _encode (AuthSession, data, uid)
    return _encode (AnonSession, data)

#.........................................

# def _user_uid (obj):
    #dup = type(obj) != dict and len(obj) >= 2
    # user = obj.pop('_u', None) 
    # uid = user.get('_id') if user else 0 # todo: hide internals in session module
    # return user, uid
        
class _TokenData (object):

    def __init__ (_s, token, tt, obj, bM, ts, bIV): #, uid=None):
        _s.bIV   = bIV  
        _s.bMac  = bM  
        _s.tType = tt  
        _s.tStamp= ts
        _s.token = token 
       # _s.user  = obj.pop('_u', None)
        _s.data  = obj
                 
    def maxAge (_s, cfg): 
        if   _s.tType == AnonSession : return cfg['maxIdleAnon']
        elif _s.tType == AuthSession : return cfg['maxIdleAuth']
        elif _s.tType == VerifySignUp: return cfg['maxAgeSUTok']
        elif _s.tType == ResetPWord1 : return cfg['maxAgePW1Tok']
        elif _s.tType == ResetPWord2 : return cfg['maxAgePW2Tok']
        else: raise RuntimeError ('invalid token type')
        
    # def invalidUser (_s):
        ## hasUid = _hasUID (_s.tType)
        ## user, uid = _user_uid(_s.obj)
        # uid = 0
        # um = None
        # if _s.user:
            # uid =_s.user.get('_id')
            # if uid:
                # try: 
                    # um = User.get_by_id (uid) 
                # except Exception, e:
                    # logging.exception(e)  
                
        # if _s.tType == AuthSession:         
            # if _s.user is None: 
                # x = 'No user'    
            # elif uid == 0: 
                # x = 'Zero id for user'    
            # elif um is None: 
                # x = 'Invalid user id'  
            # else:
                # x = ''# ok  
       ## elif _s.user:
        ##    x = 'Unexpected user object'
        # else:
            # x = ''  # ok
        # return x, uid         
        
    def valid (_s, cfg, tt=None): 
        """Checks encryption validity and expiry: whether the token is younger than maxAge seconds.
        Use neutral evaluation pathways to beat timing attacks.
        NB: return only success or failure - log why it failed but user mustn't get to know the reason why ! 
        """
        btt = _s.tType==AnonSession or _s.tType==AuthSession \
              if tt is None else \
              _s.tType==tt 
        bData = _s.data is not None #  and (type(_s.data) == dict)
        # iu = _s.invalidUser()
        bTS = utils.validTimeStamp (_s.tStamp, _s.maxAge(cfg))
        # check booleans in order of their initialisation
        y = z = ''
        if   not _s.bMac : x = 'Invalid mac'
        elif not _s.bIV  : x = 'Invalid iv'
        elif not btt     : x = 'Invalid token type'; y = str(tt); z = str(_s.tType)
        elif not bData   : x = 'Invalid data object'
        # elif iu[0]       : x = iu[0]; y = iu[1]; z = repr(_s.user)
        else:    
            return bTS  #no logging if merely expired

        logging.warning ('%s: %s %s in Token: %r', x, y, z, _s.token)
        return False 
           
# Some global constants to hold the lengths of component substrings of the token         
CH  = 1
TS  = 4
#UID = 8
IV  = 8
MAC = 20
L = CH + TS + IV + MAC

class Keys (object):
    def __init__ (_s, ts):
        s = W.W.keys (ts)
        assert len(s) == 16, 'keys length should be 16'
        # Todo: xor with config key also 16 bytes
        _s. bfish = s[:8]
        _s. hmac  = s[8:]   
   #  _shuffleKey, \
   
def _blowfish (iv, k):
    return Blowfish.new (k, Blowfish.MODE_CBC, iv)

def _hash (msg, k):
    """hmac output of sha1 is always 20 bytes"""
    return hmac.new (k, msg, hashlib.sha1).digest()
    
def _iv_key (uid):
    # logging.warning('uid type = %r', type(uid))
    # logging.warning('uid = %r', uid)
    return W._q.pack(uid) + 'iv'
    
# def _pad8len (data):
    # n  = len(data) # + UID
    # return 8 - n % 8      # text length must be a multiple of block size which is 8 for Blowfish

# def _hasUID (ttype):
    # return ttype == AuthSession\
        # or ttype == ResetPWord
        
# #########################
# |80|40|20|10|08|04|02|01|
# |  p8    | ttype  |  p3 |
# #########################
def _encodeCh (data, ttype):
    assert ttype in range(2**3)
    n  = len(data) 
#    if _hasUID (ttype):
#        n += UID
    p8 = (-n) % 8      # text length must be a multiple of block size which is 8 for Blowfish
    n += p8 + L
    p3 = (-n) % 3
    n  = (p8 << 5) | p3
    n |= ttype << 2
    #n |= int(cont) << 7
    #logging.warning('encode ttype p3 p8 = %s %d %d', utf8(ttype), p3, p8)
    #logging.warning('encode kch = 0x%x %s', n, bin(n))
    return chr(n), p8, p3

def _decodeCh (kch):
    #logging.warning('decode kch = %s', kch)
    n  = ord (kch)
    #logging.warning('decode kch = 0x%x %s', n, bin(n))
    p3 =  n & 0b00000011   
    p8 = (n & 0b11100000) >> 5
    tt = (n & 0b00011100) >> 2
    #cont= (n & 0x80) >> 7 !=0
    #logging.warning('decode ttype p3 p8 = %s %d %d', utf8(tt), p3, p8)
    return tt, p8, p3 

def _serialize (data):
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
    # logging.warning ('saving data = %r', data)
    s = json.dumps (data, separators=(',',':'))
    return s.encode('utf-8') #byte str
    
def _deserialize (data):
    try: 
        #assert isinstance (data, unicode)
        #logging.warning('1 data: %r', data)
        obj = json.loads (data)
        #logging.warning('2 json: %r', obj)
        #logging.warning('3 %r', byteify(obj))
        return obj # byteify(obj)
    except Exception, e:
        logging.exception(e)
        return None

def byteify(input):
    '''json.loads() returns an object with unicode strings. But we might want byte strings instead.
       There's no built-in option in json module for this.  
       So use this simple recursive function to convert strings in any JSON object to use UTF-8-encoded byte strings:
    '''
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def _save_iv (iv, uid):  
    if uid:  
        k = _iv_key (uid)
        ivList = memcache.get (k)
        if ivList:
            ivList.append (iv)
        else:
            ivList = [iv]
        memcache.set (k, ivList)

def _check_iv (iv, data):
    # todo: check the ip, user-agent etc etc
    if type(data) is dict:
        # user = data.get('_u')
        # if user:
        uid = data.get('_userID')
        if uid:
            ivList = memcache.get (_iv_key (uid))
            if ivList:
               for i in ivList:
                   if utils.sameStr (iv, i):
                       ivList.remove (iv) 
                       return True # found and removed - nb slight timing differences depending on list size
               return False        # not found
    return True                # no data or not dict

# Encoded byte string with layout represented as name::bytes 
#      and RP(x,y,z) is a random permutation of elements x,y,z 
# -     
# A = RP(data:N, pad%8, userId:8) 
# B = RP(pad%3, iv:8, timestamp:4, kch)
# C = encrypt(A) 
# D = RP(B, C)                         
# E = hmac:20(D) 
# cipher = RP(D, E)
# token = base64(cipher)
#                                           |<------- L2 + pad%3 ----->|     # create byte string with this layout represented as name::bytes :-     
    # 1) encrypt:       data:N + pad%8       (iv, blowfish_key) 
    # 2) append:        |----ciph----| + pad%3 + timestamp:4 + iv:8 + kch  
    # 3) append hash:   |-----  sha1_hash of 2 -------------------------| + hmac:20 
def _encode (tokentype, obj, uid=None):
    """ data is serialised sessiondata
        returns a token string of base64 chars with iv and encrypted tokentype, uid and data
    """
#        iv_key = _iv_key(uid)
#        memcache.set(iv_key, iv)  
    #logging.warning('encode obj: %r', obj)
    data  = _serialize (obj)
    #logging.warning('encode data: %r', data)
    #logging.warning('encode obj: %r', _deserialize (data))
    kch, p8, p3 = _encodeCh (data, tokentype)
    #logging.warning('encode p8: %d', p8)
    #logging.warning('encode p3: %d', p3)
    #logging.warning('encode kch: %x %s', ord(kch), bin(ord(kch)))
    if p8:
        data += os.urandom(p8)              # data + pad8
    # if uid:                     # ToDo docs say length of ndb.model.id is 64 bit but its not clear whether this will be..
        # assert uid >= -(2**63)  # .. in the range:       0   to  2**64-1  (C unsigned int64)  
        # assert uid <    2**63   # .. or       : -(2**63)  to  2**63-1  (C   signed int64)
        # data += W._q.pack (uid)             # data + pad8 + uid
    now = utils.timeStampNow()
    k = Keys(now)
    iv= os.urandom(IV)
    _save_iv (iv, uid)
    ciph = _blowfish(iv, k.bfish).encrypt(data) 
    if p3:
        ciph += os.urandom(p3)              # data + pad8 + pad3
    ciph += W._i8sc.pack (now, iv, kch)     # data + pad8 + pad3 + ts + iv + kch
    h20   = _hash (ciph, k.hmac)
    token = urlsafe_b64encode (ciph + h20)  # data + pad8 + pad3 + ts + iv + kch + mac
    return token
    
def _decode (token):
    """inverse of encode: from token return _TokenData"""
    try:
        bytes = urlsafe_b64decode (token)       # data + pad8 + pad3 + ts + iv + kch + mac
    except TypeError:
        logging.exception('Base64: ')
        raise Base64Error
        
    n = len (bytes)-MAC
    mac = bytes [n:]
    msg = bytes [:n]                        # data + pad8 + pad3 + ts + iv + kch
    n -= TS + IV + CH
    ts, iv, kch = W._i8sc.unpack_from (bytes, n) 
    k = Keys(ts)
    mac2 = _hash (msg, k.hmac)
    bMac = utils.sameStr (mac, mac2)
    ttype, p8, p3 = _decodeCh (kch)
    # logging.warning('decode kch: %x %s', ord(kch), bin(ord(kch)))
    # logging.warning('decode p8: %d', p8)
    # logging.warning('decode p3: %d', p3)
    # logging.warning('decode tt = %s', utf8(ttype))
    n -= p3
    ciph = bytes [:n]  
    plain= _blowfish(iv, k.bfish).decrypt (ciph)
    # logging.warning('decode plain = %r', plain)
    # logging.warning('decode plainlen = %d', len(plain))
    # logging.warning('decode n = %d', n)
    # logging.warning('decode p8 = %d', p8)
    # logging.warning('decode len = %d', n-p8)
    data = plain [:n-p8]
    data = _deserialize (data)
    bIV  = _check_iv(iv, data)
    return _TokenData (token, ttype, data, bMac, ts, bIV)
    
# see http://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle    
# To shuffle an array a of n elements (indices 0..n-1):
  # for i from n − 1 downto 1 do
       # j ← random integer with 0 ≤ j ≤ i
       # exchange a[j] and a[i]
       
    # def shuffle(iv, cipher16):
        # """return bytearray of 24 bytes after 8 byte-swaps between first 8 bytes (iv) and other bytes according to _shuffleKey"""
        # assert len(cipher16) == 16
        ##assert len(key)  == 20 # == 32 * 5 / 8  --  5 bits because 32==2**5; 8 because 8 bits in byte  
        # i = 0
        ##print '       ', iv, ':', cipher16
        # biv = bytearray(iv)
        # bci = bytearray(cipher16)
        # key = _shuffleKey
        # while i < 8:
            # x = key & 0xf # lowest 4 bits
            # biv[i], bci[x] = bci[x], biv[i] 
            ##print '%2d %2d %x %s : %s'%(i, x, x, biv, bci)
            # key >>= 4
            # i +=  1
        # return biv + bci
        
    # def unshuffle(bytes):
        # """inverse of shuffle: from bytes return the tuple of bytesarrays (iv, cipher16)"""
        # assert len(bytes) == 24
        # iv = bytearray(bytes[:8])
        # ci = bytearray(bytes[8:])
        ##print ' '   
        # i = 7
        ##print '       ', iv, ':', cipher16
        # while i >= 0:
            # x = (_shuffleKey >> (i*4)) & 0xf # get 4 bits of key from high end
            ##print '%2d %2d %x %s : %s'%(i, x, x, bivo, bci)
            # iv[i], ci[x] = ci[x], iv[i] 
            ##print '%2d %2d %x %s : %s'%(i, x, x, biv, bci)
            # i -=  1
        # return str(iv), str(ci)

            
#todo global:        
#Tokens = Tokeniser( app.config['webapp2_extras.sessions']['secret_key'])
   
# This code replaces the code in webapp2_extras\securecookie.py which is entirely the one class SecureCookieSerializer

# The idea is to create bAuth tokens of different types 
# - session tokens that can be verified without needing access to the DataStore.
# - verify tokens of two types - signup (to verify email address at signup)
#                              - password lost (user must verify email address and create a new password)
# An bAuth token will be a one-time token with limited age - the age is always checked.
# Verify tokens could have a maxAge of several days eg between one day and one week.
# A new session token is generated for each http response therefore the maxAge for a session token is actually the max Idle  
# time between responses which would be much shorter than maxAge of the Verify tokens - typically from one minute to 10 minutes

#(Consider persitent cookies for "remember me" etc)

# The token is encryted from a) creation timestamp (seconds since epoch)    (4 bytes)
#                            b) the id of the user entity in the DataStore  (8 bytes)
#                            c) the token type (1 byte) - we plan for 'v'(signup) 'p'(lost pw) 's'(session)
#                               (Note:  the code will assume that a user can be in one of the states corresponding 
#                                       to 's' 'p' or 's' but cannot be in more than one simultaneously)
#                            d) a 12 byte random number which is used as the token id
#                               and also for the initial value for the encryption

# Verify tokens are sent to the user in an email and sent back as a param in the url for the link-response.
# The Session token is stored in a browser cookie and read in each rewuest-header.

# Enforcing one-time use
# ======================
# Only a few tokens are ever valid at a given moment for a given user irrespective of token-type.
# Maintain a list of valid token-ids in ndb or memcache for a particular user.
# Whenever a token is created, its added to the list. Wheneven is replaced , its removed
# Changing the token-id and making the previous tokens invalid, reduces the time window for decryting exploits 
# because the token-id is used as the iv for encrypting the data in the cookie. 

# When a token is validated first we decode it to obtain token-id, user-id, timestamp and type.
# We check the type and token's age (ie that the timestamp + maxAge is later than now), 
# then we look up the token-id in store for this user-id and compare with this token-id.
# IE its decoded token-id should be the same as the current token-id in store for this user.
# If its a Session token, we can optionally also enforce one-time use :
# immediately after validation, the token-id in store is replaced with a new token-id of the new token which sent in the response.

# For Verify tokens the one-time checking code needs to reliably store the token-id in the DataStore inside the User entity. 
# But this use of DataStore is expensive for Session tokens- a datastore read and write for every rewuest and its not always necessary.

# For Session tokens there are 6 options
# 1) enforce strict one-time use of session tokens just as for verify tokens - this implies a DataStore Read and Write on every rewuest
# 2) dont enforce one-time use at all. Rely on SSL to avoid sniffing of token and also maxIdle time ensures that the window for exploit is small 
# 3) store the token-id in MemCache - much cheaper, but sometimes it will not be found in MemCache because it has been flushed
#    We cannot know when MemCache is going to be flushed, but, we do know soon afterwards when we dont find a name we are expecting. 
#    If all the data is missing for a given user, then we do know that it has been recently flushed (at some point since the last rewuest from this user.)
#    Whenever we detect that MemCache has been flushed we have three options
#    3.1) less friendly - we end the session
#    3.2) less secure - we dont check the token-id on this occasion, an so there is a time window while a token could be hijacked. 
#         It lasts from the last rewuest to the current rewuest.
#         A hijack must get a copy of the token at that window, after a flush but before the user's next rewuest. The hijacker then gets a new token
#         and thereafter the real user would be denied access because he would have the old token issued just before the flush.     
#    3.3) compromise - we dont check the token-id on this occasion, but we end the session if an old token is presented in the 1st maxidle seconds
#         We cant distinguish a hijacked from the real user so both  are denied access.
#         Normally if a user sends an http rewuest with an invalid token, then she is redirected to logon;
#         or even if its valid but a session is already running for this user, the new conection is refused. 
#         We log the event but the existinbg session can continue. 
#         Suppose there are two http rewuests for the same user in the maxIdle time interval from after a flush. 
#         Again we seem to have have multiple connection attempts for the same user - one of them could be a hijack attempt, but we cannot tell which.
#         After a flush a new chain of tokens begins for this user. If a invalid token-id arrives in the maxIdle interval after the first in the chain 
#         (this is the nearest we get to flush time)
#         then not only the new rewuest is refused but also the current session should be terminated. 
#         Both the users with this User-id (real and hijacker) have to log in again.
#    3.4) We dont check the token-id but instead we check the ip address 
#         Normally we should not enforce that ip address cannot change because some addresses are dynamic but if we record the ip address at every rewuest 
#         then we can enforce unchanged ip only in the flushing interval - how often will an address change cpoincide with flushing interval.
#         Then as for 3.3 we end the session.

# Optionally we can/should also enforce an unchanged user-agent throughout the session ie client platform.

 # further security notes
 # ======================
 # 1) GQL-injection attack is not as bMac as SQL injection because GQL only has wueries - no modifi=ying constructs as in SQL
    # But dotn need to use GQL at all. Just use Query class - then App are totally protected 
 # 2) XSS attack. If we use jinja2 for our templates this incorporates HTML escaping so we shoud be ok.
 # 3)
 
 
 
 
 
 
