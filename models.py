#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from google.appengine.ext import ndb
import logging
import utils

class CredentialsError (Exception):
    '''wrong password or authid or both'''
    
# class AlreadyExistsError (Exception):
    # '''this authid is already taken'''

class Unique (ndb.Model):
    """A model to implement uniqueness of values. 
    For all entities in an ndb model, every named key is guaranteed to be unique.  
    So we make the value a named key and see if we can create an entity with that key.
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
    def create (_C, uniqueStr, token, uid=0): 
        k = ndb.Key(_C, uniqueStr)
        ent = k.get()
        if ent is not None:
            logging.info('key already exists: %s' % uniqueStr)
            raise ndb.Rollback      # will return None after being caught by transactional decorator
        ent = _C(userID=uid, token=token)
        ent.key = k
        return ent.put() 
        
    @staticmethod
    def ownID (email):
        return 'own:'+ email
        
    @classmethod
    def createOwnID (_C, email, tokID):
        logging.warning (' .token = %s' % tokID)
        return _C.create( _C.ownID (email), tokID)
        
    @classmethod
    def byID (_C, authID, tokID=None):
        assert ':' in authID
        u = _C.get_by_id (authID)
        if u:
            if tokID is None \
            or u.token == tokID:
                return u
            logging.warning ('Unique.token = %s' % u.token)
            logging.warning ('       tokID = %s' % tokID)
        return None

        
class UserBase (ndb.Model):  #todo why mot use Model and subclass with whatever Properties
    """Stores user authentication credentials or authorization ids."""
    
    # next two statements look like aggregation but are not - they do not add functionality 
    # - they merely allow some indirect names in the code for User - EG instead of writing Unique we can write _C.unique_model
    #unique_model = Unique#: The model used to ensure uniqueness.
    # token_model  = UserToken#: The model used to store tokens.

    updated = ndb.DateTimeProperty (auto_now=True)
    authIDs = ndb.StringProperty   (repeated=True) # list of IDs. EG for third party authentication, e.g. 'google:username'. UNIQUE.
    pwdhash = ndb.StringProperty() # Hashed password string. Not a required prop because third party authentication doesn't use password.
   # lastIP  = ndb.StringProperty()
    # @classmethod
    # def _uniPair (_C, n, v):
        # '''from n, v  (name, value) pairs of strings return (User.<n>.<v>, <n>) '''
        # return '%s.%s:%s' %(_C.__name__, n, v) , n
    
    def __init__(_s, *pa, **ka):
        _s.modified = False
        super(UserBase, _s).__init__(*pa, **ka) # call base __init__
                
    # @staticmethod
    # @ndb.transactional(xg=True)
    # def _store (user, authID):  # uniques=None, 
        # '''authID is expected to be previously unused 
        # return a new UserBase, or issue warning and return None
        # '''
        # uid = user.put().id() # save user to Datastore and return integer id 
        # if not Unique.create (authID, uid):
            # logging.warning('authid: "%s" is in use.', authID) 
            # raise ndb.Rollback
        # logging.warning('modified set WWWWWWWWWWWWWWWW.') 
        # return user
 
    def id (_s):
        return _s._key.id()

    @ndb.transactional(xg=True)
    def addAuthID (_s, authID):
        """Users may have multiple authIDs. Example authIDs:
             - own:username
             - own:email@example.com
             - google:username
             - yahoo:username
           each auth_id must be user-unique ie not already taken by another user
        """
        if Unique.create (authID, _s.uid):         #  _s.unique_model.create (_C._uniPair('auth_id', auth_id)) :
            assert ':' in authID
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
        un = Unique.byID (authID)
        if un:
            return _C.byUid (un.userID)
        logging.warning('######### invalid authID: %r' % authID)
        return None

    @classmethod
    def byUid (_C, uid):
        u = _C.get_by_id (uid)
        if not u:
            logging.warning('invalid uid: %r' % uid)
        return u
        
    # @classmethod
    # def _byAuthID (_C, authID):
        # '''authID is expected to be valid 
        # return a UserBase or issue a warning and return None
        # '''
        # un = Unique.get_by_id(authID)
        # if un:
            # user = _C.get_by_id(un.userID)
            # if user is None: 
                # logging.warning('authid: "%s" has an invalid uid.', authID) 
            # return user
        # logging.warning('authid: "%s" is not signed up.', authID) 
        # return None

    @classmethod
    def byCredentials (_C, email, praw):
        logging .warning('>>>>>>>>>>>>> email: %r'% email)
        authID = Unique.ownID (email)
        logging .warning('>>>>>>>>>>>>> authID: %r'% authID)
        user   = User.byAuthID (authID)  
        if user:
            if utils.checkPassword (user.pwdhash, praw):      
                return user
        # todo: replace these logs with incremented counted in db
        # otherwise in the event of a brute force attack, the log file will get swamped and cause DoS
        logging.warning('wrong praw: %s', praw)  
        raise CredentialsError # invalid email
        
    # def _byCredentials (_s, email, praw):     
        # if utils.checkPassword(_s.pwdhash, praw):            
             # return _s if _s.isValidated() else None # user has not validated
        # raise CredentialsError # invalid pw
    
    def sameToken (_s, oldTok):
        if utils.sameStr(_s.token, oldTok):
            return True
        logging.warning ('tokens dont match: user.token: %s', _s.token)
        logging.warning ('tokens dont match: sess.token: %s', oldTok)
        return False

    def sameIP (_s, ip):
        if utils.sameStr(_s.lastIP, ip):
            return True
        logging.warning ('ip doesnt match: ip1: %s', _s.lastIP)
        logging.warning ('ip doesnt match: ip2: %s', ip)
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
        logging.warning ('not an empty token: %s', _s.token)
        return False
        
    def setPassword (_s, praw):
        _s.pwdhash = utils.passwordHString (praw)
        _s.modified = True
            
    def setToken (_s, tokid):
        if _s.token != '':
            logging.warning ('overwriting old token: %s with new token: %s', _s.token, tokid)
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
        authID = Unique.ownID(email)
        return User._signup (authID, tokID, authIDs=[authID] ,**ka) 
        
    # @staticmethod
    # def fedSignup (fedID, **ka):
        # authID = Unique.fedID(fedID) 
        # return User._signup (un, authIDs =[authID], ka)
                   
    @staticmethod
    def _signup (authID, tokID, **ka):
        un = Unique.byID (authID, tokID)        
        if un:
            user = User ( **ka)
            k = user.put()
            un.userID = k.id()
            un.put()
            return user
        return None  # wrong tokID or unknown authID 
     


class Email (ndb.Model):
    sent   = ndb.BooleanProperty(required=True)
    sender = ndb.StringProperty (required=True)
    to     = ndb.StringProperty (required=True)
    subject= ndb.StringProperty (required=True)
    body   = ndb.TextProperty   (required=True)  # text version of the body
    html   = ndb.TextProperty()                  # html version
    when   = ndb.DateTimeProperty (auto_now_add=True)
 