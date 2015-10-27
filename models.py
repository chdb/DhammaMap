#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from google.appengine.ext import ndb
import logging
import utils

# class CredentialsError (Exception):
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

class AuthKey (ndb.Model):
    """A model to implement a many-to-one relationship from unique stringIDs (authID-strings) to User entities: 
        stringID -> AuthKey  ||  AuthKey.numID -> User   (where -> goes from key to entity)
    The stringID is a "named key" for an AuthKey entity and therefore unique among all AuthKey named keys.
    AuthKey stores a numID, which is an integer key to some entity in another model. (a UID key for a User entity)
    Each stringID refers to the same AuthKey entity but multiple stringIDs can of course refer to entities with the same numID.
    Therefore a User can have multiple authID-strings as (stringID) keys.
    """
    created= ndb.DateTimeProperty (auto_now_add=True)
    userID = ndb.IntegerProperty (required=True) # todo perhaps this really should be a KeyProperty
    token  = ndb.StringProperty() # sign-up token, forgot token, or session token
    
    # @staticmethod
    # @ndb.transactional
    # def _putIfNew (entity):
        # '''return None if entity.key already stored, otherwise store and return entity.key'''
        # return None if entity.key.get() else entity.put()
    
    # @classmethod
    # def create (_C, value, uid):
        # '''Try to create entity with a key id of new unique value string, and return whether succeeded.'''
        # en = _C (key=ndb.Key(_C, value), userID=uid)

        # return _C._putIfNew(en) is not None

    @classmethod
    @ndb.transactional
    def _getFrom (_C, uniqueStr, token): 
        ''' Every named key for an entity in any ndb model, must be unique. (Two entities can have the same values, but their keys must differ) 
        We can test uniqueness of a string by using it as a named key and then see if we can get() an entity with that key.
        If not, then the string is unique over those entities. 
        Initially at signup1 the first entity for a particual User is created with uid==0. 
        Later when the email is validated at signup2, the User entity is created and the AuthKey uid is update to the User id.   
        Additional AuthKey's for the same User will be created with non-zero uids.
        returns tuple: boolean: whether already exists (ie not created)
                       AuthID entity
        '''
        k = ndb.Key(_C, uniqueStr)
        ent = k.get() 
        if ent is not None:
            logging.info('key already exists: %s' % uniqueStr)
    #        if ent.verified()
            return True, ent
    #       ent.token = token
    #       return False, ent.put()
            #raise ndb.Rollback      # return None after being caught by transactional decorator
        #logging.debug ('Creating .token = %s' % tokID)
        ent = _C(userID=0, token=token)
        ent.key = k
        return False, ent.put() 
        
    @staticmethod
    def ownID (own):
        return 'own:'+ own

    @staticmethod
    def emailID (email):
        return 'email:'+ email
        
    @classmethod
    def getFromOwnID (_C, own, tokID):
         return _C._getFrom( _C.ownID (own), tokID)
        
    @classmethod
    def getFromEmail (_C, email, tokID):
        return _C._getFrom( _C.emailID (email), tokID)
        
    @classmethod
    def byEmail (_C, email):
        '''use with caution - no password needed'''
        return _C.byID ( _C.emailID (email))
        
    @classmethod
    def byID (_C, authID, tokID=None):
        assert ':' in authID
        u = _C.get_by_id (authID)
        if u:
            if tokID is None \
            or u.token == tokID:  # check the tokID if there is one
                return u
            logging.warning ('non-matching AuthKey.token = %s' % u.token)
            logging.warning ('non-matching         tokID = %s' % tokID)
        return None               # either bad authID of non-matching tokID

    @classmethod
    def purge(_C):
        #t = config.config['maxAgeSignUpTok']
        #end = dt.datetime.now() - dt.timedelta(seconds=t)
        crop = _C.query(_C.userID == 0) \
                 .filter(not inCfgPeriod(_C.created, 'maxAgeSignUpTok'))
        keys = [k for k in crop.iter(keys_only=true)]
        ndb.delete_multi(keys)
        return len(keys)
        
    def verified(_s):
        return _s.userID != 0
        
class UserBase (ndb.Model):
    """Stores user authentication credentials or authorization ids."""

    updated      = ndb.DateTimeProperty (auto_now=True)
    lockoutstart = ndb.DateTimeProperty()
    authIDs = ndb.StringProperty   (repeated=True) # list of IDs. EG for third party authentication, e.g. 'google:username'. UNIQUE.
    pwdhash = ndb.StringProperty() # Hashed password string. NB not a required prop because third party authentication doesn't use password.
   # lastIP  = ndb.StringProperty()
    # @classmethod
    # def _uniPair (_C, n, v):
        # '''from n, v  (name, value) pairs of strings return (User.<n>.<v>, <n>) '''
        # return '%s.%s:%s' %(_C.__name__, n, v) , n
    
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
             - email:myemail@example.com
             - google:g-username
             - yahoo:y-username
        Each auth_id must be unique across users ie not already taken by any other user
        
        """
        assert ':' in authID
        ok = AuthKey._getFrom (authID, _s.uid) [0] #  _s.unique_model.create (_C._uniPair('auth_id', auth_id)) :
        if ok:        
            _s.authIDs.append (authID) #ToDo: test this line  (moved from before the conditional)
            _s.modified = True
            return True
        return False

    # @classmethod
    # def _byOwnID (_C, id):
        # '''this method is private or admin only - 
        # Normally you use need the pw and you call byCredentials()'''
        # email = _C.ownAuthID(id)
        # user = _C._byAuthID (email)
        # if not user:
            # logging.warning('not found email: %s', email)
        # return user
         
    # @classmethod
    # def byFedID (_C, fedID):
        # assert ':' in fedID
        # return _byAuthID (_C, fedID)
        
    @classmethod
    def byAuthID (_C, authID):
        un = AuthKey.byID (authID)
        if un:
            if un.userID:
                return _C.byUid (un.userID)
            logging.warning('Un-Verified Email. AuthKey: %r' % un)
        else:
            logging.warning('User name not recognised.Unknown AuthID: %r' % authID)
        return None

    @classmethod
    def byUid (_C, uid):
        # import traceback
        # for l in traceback.format_stack():
            # logging.debug(l.strip())
        logging.debug('uid: %r' % uid)
        u = _C.get_by_id (uid)
        if not u:
            logging.warning('invalid uid: %r' % uid)
        return u
        
    # @classmethod
    # def _byAuthID (_C, authID):
        # '''authID is expected to be valid 
        # return a UserBase or issue a warning and return None
        # '''
        # un = AuthKey.get_by_id(authID)
        # if un:
            # user = _C.get_by_id(un.userID)
            # if user is None: 
                # logging.warning('authid: "%s" has an invalid uid.', authID) 
            # return user
        # logging.warning('authid: "%s" is not signed up.', authID) 
        # return None

    @classmethod
    def byCredentials (_C, email, praw):
        user = _C.byEmail (email)  
        if user:
            if user.lockoutstart /
            and utils.inCfgPeriod (user.lockoutstart, 'lockoutPeriod'):
                logging.warning ('locked out: %s', email)
                return None
            if utils.checkPassword (user.pwdhash, praw):      
                logging.debug('wrong praw: %s', praw)  
        return user
        
    @classmethod
    def byEmail (_C, email):
        '''use with caution - no password needed'''
        authID = AuthKey.emailID (email)
        logging .debug('>>>>>>>>>>>>> authID: %r'% authID)
        return User.byAuthID (authID)  
                
    # def _byCredentials (_s, email, praw):     
        # if utils.checkPassword(_s.pwdhash, praw):            
             # return _s if _s.isValidated() else None # user has not validated
        # raise CredentialsError # invalid pw
    
    def sameToken (_s, oldTok):
        if utils.sameStr(_s.token, oldTok):
            return True
        logging.debug ('tokens dont match: user.token: %s', _s.token)
        logging.debug ('tokens dont match: sess.token: %s', oldTok)
        return False

    def sameIP (_s, ip):
        if utils.sameStr(_s.lastIP, ip):
            return True
        logging.debug ('ip doesnt match: ip1: %s', _s.lastIP)
        logging.debug ('ip doesnt match: ip2: %s', ip)
        return False

    def validate (_s, tok, newTok=''):
        if _s.sameToken (tok):
            _s.token = newTok
            _s.modified = True
            return True
        return False
        
    def isValidated (_s):
        if _s.token == '':      # logged out
            return True
        if _s.token[0] == 'x':  # logged in
            return True
        logging.debug ('not an empty token: %s', _s.token)
        return False
        
    def setPassword (_s, praw):
        _s.pwdhash = utils.passwordHString (praw)
        _s.modified = True
            
    def setToken (_s, tokid):
        if _s.token != '':
            logging.debug ('overwriting old token: %s with new token: %s', _s.token, tokid)
        _s.token = tokid
        _s.modified = True
            
class User (UserBase):

    forename = ndb.StringProperty()
    lastname = ndb.StringProperty()
    country  = ndb.StringProperty()
    
    # @staticmethod
    # def credCreate (id, token): 
        # """checks for duplicates in unique fields 
        # id:  string id for authorisation of user - must be unique among all users (create with one - addothers later with add_auth_id())
        # """
        
        
        # ph = utils.passwordHString (praw)
         
        # authID = User.ownAuthID(id)
        # user = User( authIDs=[authID]
                   # , pwdhash= ph
                   # , token  = token
                   # )    
        # return UserBase._store (user, authID)
    
    @staticmethod
    def credSignup (tokID, email, **ka):
        authID = AuthKey.emailID(email)
        return User._signup (authID, tokID, authIDs=[authID] ,**ka) 
        
    # @staticmethod
    # def fedSignup (fedID, **ka):
        # authID = AuthKey.fedID(fedID) 
        # return User._signup (un, authIDs =[authID], ka)
                   
    @staticmethod
    def _signup (authID, tokID, **ka):
        un = AuthKey.byID (authID, tokID)        
        if un:
            user = User (**ka)
            k = user.put()
            un.userID = k.id()
            un.put()
            return user
        return None  # wrong tokID or unknown authID 


class Email (ndb.Model):
    sender = ndb.StringProperty (required=True)
    to     = ndb.StringProperty (required=True)
    subject= ndb.StringProperty (required=True)
    body   = ndb.TextProperty   (required=True)  
    html   = ndb.BooleanProperty(required=True)   # whether body is html 
    sent   = ndb.BooleanProperty(required=True)
    when   = ndb.DateTimeProperty (auto_now_add=True)
 
    @classmethod
    def create(_C, **ka):
        assert ('html' in ka) != ('body' in ka)
        # Semantics of params 'body' and 'html' are different in Email model from ones for the input params (which were as used for sending email. )
        # Instead of either having content in one or the other param, all content goes in 'body' and we distiguish with boolean 'html'
        bHtml = 'html' in ka
        if bHtml:
            ka['body'] = ka.pop ('html') # delete string 'html'
        emailLog = _C (html=bHtml, **ka) # insert boolean 'html' 
        emailLog.put()
 
    