#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from google.appengine.ext import ndb
import logging
import utils as u
#import config
import datetime as d

class Locked (Exception):
    pass
class AlreadyInUse (Exception):
    pass
class BadData (Exception):
    pass
    
    # def __init__(_s, str):
        # assert isinstance(str, basestring)
        # _s.userMsg = str
        
    # def __str__(_s):
        # return _s.userMsg
        
# class UnknownAuthID  (CredentialsError):
    # pass
# class WrongPassword  (CredentialsError):
    # pass
# class UnVerifiedEmail(CredentialsError):
    # pass
    
# class AlreadyExistsError (Exception):
    # '''this authid is already taken'''
#from socket import inet_aton

# def bLocked (m, hlr): 
    
    # if m.handler != hlr:
        # return False
    # togo = m.lockUntil - d.datetime.now()
    # bUnexpired = togo > d.timedelta()
    # if bUnexpired:
        # logging.warning('locked for %d more seconds', togo.total_seconds())
    # return bUnexpired

class Lock (ndb.Model):
#    handler   = ndb.  StringProperty(required=True)
    lockUntil = ndb.DateTimeProperty(required=True)

    @staticmethod
    def _keystr (str, hlr):
        assert' 'not in str
        assert' 'not in hlr
        return hlr +' '+ str
  
    @classmethod
    def _find (C, str, hlr):
        keystr = C._keystr (str, hlr)
        return C.get_by_id (keystr)
        
    @classmethod
    def _create (C, str, hlr, exp): 
        keystr = C._keystr (str, hlr)
        k = ndb.Key(C, keystr)
        e = k.get() 
        if e is not None:
            logging.info('Lock key already exists: %s' % keyStr)
            raise AlreadyInUse
        e = C(lockUntil=exp)
        e.key = k
        e.put()
        return e
    
    # @classmethod
    # def create (C, duration): 
        # exp = u.dtExpiry (duration)
        # e = C(lockUntil=exp)
        # e.put()
        # return e
    
# class LockSet (ndb.Model):
    # lockList = ndb.LocalStructuredProperty (Lock, repeated=True)
    
    # def _find (_s, hlr):
        # '''return 1st item in lockList with hlr as handler'''
        # return next((x for x in _s.lockList if x.handler == hlr), None) 
    
    @staticmethod
    def set (str, duration, hlr):
        '''put a lock for duration seconds on a given str and handler, hlr'''
        #logging.debug('xxxxxxxxxxxx key = %r', str)
        exp = u.dtExpiry (duration)
        lock = Lock._find(str, hlr)
        if lock:
            lock.lockUntil = exp
        else: 
            lock = Lock._create (str, hlr, exp)
        lock.put()

    # def lock (_s, duration):
        # '''for a given handler, hlr, put a lock on hld for duration seconds '''
        # exp = u.dtExpiry (duration)
        # _s.lockUntil = exp
        # _s.put()
                
    @staticmethod
    def isSet (str, hlr):
        '''return whether there is a current lock on a given str, and handler, hlr '''
        lock = Lock._find(str, hlr)
        if lock:
            togo = lock.lockUntil - d.datetime.now()
            bUnexpired = togo > d.timedelta()
            if bUnexpired:
                logging.warning('locked for %d more seconds', togo.total_seconds())
            return bUnexpired
        return False
        

# class BadIP    (LockSet): pass
# class BadEmail (LockSet): pass

class AuthKey (ndb.Model):
    """A model to implement a many-to-one relationship from unique stringIDs (authID-strings) to User entities: 
        stringID -> AuthKey  ||  AuthKey.numID -> User   (where -> goes from key to entity)
    The stringID is a "named key" for an AuthKey entity and therefore unique among all AuthKey named keys.
    AuthKey stores a numID, which is an integer key to some entity in another model. (a UID key for a User entity)
    Each stringID refers to the same AuthKey entity but multiple stringIDs can of course refer to entities with the same numID.
    Therefore a User can have multiple authID-strings as (stringID) keys.
    """
    ''' Every named key for an entity in any ndb model, must be unique. (Two entities can have the same values, but their keys must differ) 
    We can test uniqueness of a string by using it as a named key and then see if we can get() an entity with that key.
    If not, then the string is unique over those entities. 
    Initially at signup the first entity for a particual User is created with uid==0. 
    Later when the email is validated at signup2, the User entity is created and the AuthKey uid is update to the User id.   
    Additional AuthKey's for the same User will be created with non-zero uids.
    '''
    created= ndb.DateTimeProperty (auto_now_add=True)
    userID = ndb.IntegerProperty (required=True) # todo perhaps this really should be a KeyProperty
    
    # @staticmethod
    # @ndb.transactional
    # def _putIfNew (entity):
        # '''return None if entity.key already stored, otherwise store and return entity.key'''
        # return None if entity.key.get() else entity.put()
    
    # @classmethod
    # def create (C, value, uid):
        # '''Try to create entity with a key id of new unique value string, and return whether succeeded.'''
        # en = C (key=ndb.Key(C, value), userID=uid)

        # return C._putIfNew(en) is not None

    @classmethod
    #todo - commented out - because _create is private and we only call it from a transactional User.create() - is this ok  ?
    #@ndb.transactional 
    def _create (C, keyStr, uid): 
        '''
        Find the AuthKey if it exists for this keyStr, else create it. 
        return tuple: 1) entity
                      2) boolean: whether already existed (ie not created)
        '''
        k = ndb.Key(C, keyStr)
        ent = k.get() 
        if ent is not None:
            logging.info('key already exists: %s' % keyStr)
    #        if ent.verified()
            raise AlreadyInUse
            # return ent, False 
    #       ent.token = token
    #       return False, ent.put()
            #raise ndb.Rollback      # return None after being caught by transactional decorator
        #logging.debug ('Creating .token = %s' % tokID)
        ent = C(userID=uid)
        ent.key = k
        ent.put()
        return ent
        
    @staticmethod
    def ownID (own):
        '''user creates her own id string'''
        return 'own:'+ own

    @staticmethod
    def emailID (ema):
        return 'ema:'+ ema
        
    # @classmethod
    # def getFromOwnID (C, own):
         # return C._get( C.ownID (own))
        
    # @classmethod
    # def getFromEmail (C, ema):
        # return C._get( C.emailID (ema))
        
    @classmethod
    def _byEmail (C, ema):
        '''use with caution - no password needed'''
        ak = C.byID (C.emailID (ema))
        # if ak and not ak.userID:
            # raise BadData
        return ak
        
    @classmethod
    def byID (C, authID):
        assert ':' in authID
        return C.get_by_id (authID)
        # if u:
            # if tokID is None \
            # or u.token == tokID:  # check the tokID if there is one
                # return u
            # logging.warning ('non-matching AuthKey.token = %s' % u.token)
            # logging.warning ('non-matching         tokID = %s' % tokID)
        # return None               # either bad authID of non-matching tokID

    # def getUser (_s):
        # if _s.userID:
            # return User.byUid (_s.userID)
        # logging.warning('Un-Verified Email. AuthKey: %r' % _s.key.id())
        # return None

    # @classmethod
    # def purge(C):
        # t = config.config['maxAgeSignUpTok']
        # end = dt.datetime.now() - dt.timedelta(seconds=t)
        # def expired(dt):
            # return d.datetime.now() > dt + d.timedelta(seconds=u.config('maxAgeSignUpTok'))
        # crop = C.query(C.userID == 0) \
                 # .filter(expired(C.created))
        # keys = [k for k in crop.iter(keys_only=true)]
        # ndb.delete_multi(keys)
        # return len(keys)
        
    # def verified(_s):
        # return _s.userID != 0
        
class UserBase (ndb.Model):
    """Stores user authentication credentials or authorization ids."""
    updated  = ndb.DateTimeProperty (auto_now=True)
    #handler  = ndb. StringProperty(required=True)
    authIDs  = ndb.StringProperty (repeated=True) # list of IDs. EG for third party authentication, eg 'google:username'. UNIQUE.
    pwdhash  = ndb.StringProperty (required=True) # Hashed password string. NB not a required prop because third party authentication doesn't use password.
 #   locks    = ndb.LocalStructuredProperty (LockSet)
   # token    = ndb.StringProperty() # sign-up token, forgot token, or session token
   # lastIP  = ndb.StringProperty()
    # @classmethod
    # def _uniPair (C, n, v):
        # '''from n, v  (name, value) pairs of strings return (User.<n>.<v>, <n>) '''
        # return '%s.%s:%s' %(C.__name__, n, v) , n
    
    def __init__(_s, *pa, **ka):
        _s.modified = False         # if modified, a lazy put() is called by H_base.dispatch()
        super(UserBase, _s).__init__(*pa, **ka) # call base __init__

    def id (_s):
        return _s._key.id()

    @ndb.transactional(xg=True)
    def addAuthID (_s, authID):
        """AuthID is a string used for login.
        Users may have multiple authIDs, but each must have different prefix (before ':'). 
        Examples:
             - own:myusername
             - ema:myemail@example.com
             - google:g-username
             - yahoo:y-username
        Each auth_id must be unique across users ie not already taken by any other user
        """
        assert ':' in authID
        ok = AuthKey._get (authID, _s.uid) [0] #  _s.unique_model.create (C._uniPair('auth_id', auth_id)) :
        if ok:        
            _s.authIDs.append (authID) #ToDo: test this line  (moved from before the conditional)
            _s.modified = True
            return True
        return False

    # @classmethod
    # def _byOwnID (C, id):
        # '''this method is private or admin only - 
        # Normally you use need the pw and you call byCredentials()'''
        # ema = C.ownAuthID(id)
        # user = C._byAuthID (ema)
        # if not user:
            # logging.warning('not found email: %s', ema)
        # return user

    # @classmethod
    # def byFedID (C, fedID):
        # assert ':' in fedID
        # return _byAuthID (C, fedID)
        
    @staticmethod
    def byAuthID (authID):
        ak = AuthKey.byID (authID)
        if ak:
            #if ak.userID:
            return User.byUid (ak.userID)
            # logging.warning('Un-Verified Email. AuthKey: %r' % ak)
        # else:
            # logging.warning('User name not recognised.Unknown AuthID: %r' % authID)
        return None

    @staticmethod
    def byUid (uid):
        # import traceback
        # for l in traceback.format_stack():
            # logging.debug(l.strip())
        #logging.debug('uid: %r' % uid)
        if uid:
            u = User.get_by_id (uid)
            if not u:
                logging.warning('invalid uid: %r' % uid)
            return u
        return None
    # @classmethod
    # def _byAuthID (C, authID):
        # '''authID is expected to be valid 
        # return a UserBase or issue a warning and return None
        # '''
        # ak = AuthKey.get_by_id(authID)
        # if ak:
            # user = C.get_by_id(ak.userID)
            # if user is None: 
                # logging.warning('authid: "%s" has an invalid uid.', authID) 
            # return user
        # logging.warning('authid: "%s" is not signed up.', authID) 
        # return None

    # @staticmethod
    # def lock (ema, duration, hlr):
        # user = UserBase._byEmail(ema)
        # if user:
            #user.lockUntil = u.dtExpiry (duration)
            # lks = user.locks
            # if lks:
                # lks.lock(duration, hlr)
            # else:
                # user.locks = LockSet() 
                # user.locks.lockList = [Lock.create (duration, hlr)]
            # user.put()  ###???
        # else:
 #           BadEmail.lockFor (ema, duration, hlr)

    # def locked (_s):
        # return _s.lockUntil > d.datetime.now()
    @staticmethod
    def byCredentials (user, praw):
        if u.badPassword (user.pwdhash, praw):      
            logging.warning('wrong praw: %s', praw)
            return False
        return True
        
    @staticmethod
    def byEmail (ema, ipa, hlr):
        user = UserBase._byEmail (ema)  
        if not user:
            logging.warning ('unrecognised email: %s', ema)
        if Lock.isSet (ipa, hlr):
            logging.warning ('locked out by ip: %s for %s handler. User: %r', ip, hlr, user)
            raise Locked
        if Lock.isSet (ema, hlr):
            logging.warning ('locked out by email: %s for %s handler. User: %r', ema, hlr, user)
            raise Locked
        return user
        
    @staticmethod
    def _byEmail (ema):
        '''use with caution - no password needed'''
        if ema:
            authID = AuthKey.emailID (ema)
            logging .debug('>>>>>>>>>>>>> authID: %r'% authID)
            return UserBase.byAuthID (authID)  
        return None
                
    # def _byCredentials (_s, ema, praw):     
        # if u.checkPassword(_s.pwdhash, praw):            
             # return _s if _s.isValidated() else None # user has not validated
        # raise CredentialsError # invalid pw
    
    # def sameToken (_s, oldTok):
        # if u.sameStr(_s.token, oldTok):
            # return True
        # logging.debug ('tokens dont match: user.token: %s', _s.token)
        # logging.debug ('tokens dont match: ssn.token: %s', oldTok)
        # return False

    # def sameIP (_s, ip):
        # if u.sameStr(_s.lastIP, ip):
            # return True
        # logging.debug ('ip doesnt match: ip1: %s', _s.lastIP)
        # logging.debug ('ip doesnt match: ip2: %s', ip)
        # return False

    # def validate (_s, tok, newTok=''):
        # if not _s.sameToken (tok):
            # raise ValueError('tokens dont match')
        # _s.token = newTok
        # _s.modified = True
        
    # def isValidated (_s):
        # if _s.token == '':      # logged out
            # return True
        # if _s.token[0] == 'x':  # logged in
            # return True
        # logging.debug ('not an empty token: %s', _s.token)
        # return False
        
    @staticmethod
    def resetPassword (ema, praw):
        user = User._byEmail(ema) 
        user.pwdhash = u.passwordHString (praw)
        user.modified = True
        return user
        
    # def setToken (_s, tokid):
        # if _s.token != '':
            # logging.debug ('overwriting old token: %s with new token: %s', _s.token, tokid)
        # _s.token = tokid
        # _s.modified = True
            
class User (UserBase):

    forename = ndb.StringProperty()
    lastname = ndb.StringProperty()
    country  = ndb.StringProperty()
    
    # @staticmethod
    # def credCreate (id, token): 
        # """checks for duplicates in unique fields 
        # id:  string id for authorisation of user - must be unique among all users (create with one - addothers later with add_auth_id())
        # """
        
        
        # ph = u.passwordHString (praw)
         
        # authID = User.ownAuthID(id)
        # user = User( authIDs=[authID]
                   # , pwdhash= ph
                   # , token  = token
                   # )    
        # return UserBase._store (user, authID)
    
    @staticmethod
    @ndb.transactional(xg=True)
    def createFromEmail (ema, **ka):
        assert ema #todo validate?
        authid = AuthKey.emailID(ema)
        user = User (authIDs=[authid], **ka)
        ukey = user.put()
        AuthKey._create (authid, ukey.id())
        return user
        
    # @staticmethod
    # def fedSignup (fedID, **ka):
        # authID = AuthKey.fedID(fedID) 
        # return User._signup (ak, authIDs =[authID], ka)
                   
    # @staticmethod
    # def _signup (authID, **ka):
        # ak = AuthKey.byID (authID)        
        # if ak:
            # user = User (**ka)
            # k = user.put()
            # ak.userID = k.id()
            # ak.put()
           # if user.token == tokID:  # check the tokID if there is one
            # return user
            # logging.warning ('non-matching AuthKey.token = %s' % user.token)
            # logging.warning ('non-matching         tokID = %s' % tokID)
        # return None               # either bad authID of non-matching tokID


class SentEmail (ndb.Model):

    #sender = ndb.StringProperty  (required=True)
    to     = ndb.StringProperty  (required=True)
    subject= ndb.StringProperty  (required=True)
    body   = ndb.TextProperty    (required=True)  
    html   = ndb.BooleanProperty (required=True)   # whether body is html 
 #   sent   = ndb.BooleanProperty (required=True)
    when   = ndb.DateTimeProperty(auto_now_add=True)
 
    @classmethod
    def create(C, **ka):
        assert ('html' in ka) != ('body' in ka)
        # in SentEmail semantics of params 'body' and 'html' are different from ones for the input params (which were as used for sending the email. )
        # Instead of either having content in one or the other param, 
        # But here all content goes in 'body' and we distiguish with boolean 'html'
        bHtml = 'html' in ka
        if bHtml:
            ka['body'] = ka.pop ('html') # delete string 'html'
        emailLog = C (html=bHtml, **ka) # insert boolean 'html' 
        emailLog.put()
 
    