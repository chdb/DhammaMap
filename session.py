#!/usr/bin/python
# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

import logging
import cryptoken
import utils
from models import User, CredentialsError 

def loadConfig(app):

    default_config ={ 'maxIdleAnon' : None
                    , 'maxIdleAuth' : 60 * 60 # 1 hour
                    , 'cookieName'  : 'dm_session'
                                     # for effect of cookieArgs see defn of Response.set_cookie() at ...\google_appengine\lib\webob-1.2.3\webob\response.py line 690
                    , 'cookieArgs'  : { 'max_age' : None  # for persistent cookies - but use expires instead for IE 8
                                      , 'domain'  : None
                                      , 'path'    : '/'
                                      , 'secure'  : not app.debug
                                      , 'httponly': True
                                      }
                    } 
    #default_config.update(app.config)
    #app.config = default_config
    app.config.load_config ( __name__
                           , default_config
                           #, user_values 
                           #, required_keys =('secret_key',)
                           )

def cfg(handler):
    return handler.app.config [__name__]
    
# # # # # # # # # # # # # # # # # # # # 

class CookieMgr (object):
    def __init__(_s, handler):
        _s.handler = handler
        _s.cfg = cfg(handler)
        _s.name = _s.cfg['cookieName']    

    def set (_s, val):
        args= _s.cfg['cookieArgs']
        _s.handler.response.set_cookie (_s.name, val, **args)
        
    def get (_s):
        val = _s.handler.request.cookies.get (_s.name)
        if val:
            val = val.encode('utf-8') #from unicode to bytes
        #logging.debug ('cookie data = %r', val)
        return val
        
    def delete (_s):
        args= _s.cfg['cookieArgs']
        path  = args.get('path')
        domain= args.get('domain')
        _s.handler.response.delete_cookie (_s.name, path, domain)
                  
# # # # # # # # # # # # # # # # # #        

class _UpdateDictMixin (object):
    """A dict which calls `_s.on_update` on all modifying function calls."""
    on_update = None

    def calls_update (name):
        def oncall (_s, *args, **kw):
            rv = getattr (super (_UpdateDictMixin, _s), name)(*args, **kw)
            if _s.on_update is not None:
                _s.on_update()
            return rv
        oncall.__name__ = str(name)
        return oncall

    __setitem__= calls_update('__setitem__')
    __delitem__= calls_update('__delitem__')
    clear      = calls_update('clear')
    pop        = calls_update('pop')
    popitem    = calls_update('popitem')
    setdefault = calls_update('setdefault')
    update     = calls_update('update')
    del calls_update

class SessionVw (_UpdateDictMixin, dict):
    """ Owing to statelessness of http, we cannot really have a Session object. 
    Instead we have SessionVw which lasts only for lifetime of a request, retrieving the session data from the session cookie.
    It looks like a session but its really just a *snapshot in time* view of a session - same data but much shorter life.
    """
    __slots__ = ('modified') # 'container', 'new', is not used
    #_userKey = '_u'

    def __init__ (_s, handler):  # container, , new=False
        _s.modified = False
        _s.cookie = CookieMgr(handler)
        obj = None
        val = _s.cookie.get()
        if val:
            obj = cryptoken.decodeToken (val, _s.cookie.cfg)
            #logging.debug ('session data = %r', obj)
            if obj is None:
                logging.warning ('deleting invalid cookie = %r', val)
                _s.cookie.delete ()
            else:
                #assert len(obj) == 2  
                # sess = SessionVw (obj[0])
                # user = SessionVw (obj[1]) if obj[1] else None
                assert type(obj) is dict            
        #else: logging.info('No cookie found')           
        dict.update (_s, obj or ())

    def save (_s):
        #   memcache.set(sess['_userID'] + 'x', ok) 
        # logging.info('Save sess items:||||||||||||||||||')
        # for k, v in sess.iteritems():
            # logging.info('         %s : %s', k, v)
        #logging.info('|||||||||||||||||||||||||||||||||||||')
        #user = handler.userDict
        #smod = sess and sess.modified
        #umod = user and user.modified
        # if umod:
            # um = usermodel().get_by_id(u[_id])
            # um.update(u)
            # um.put()
        sess = _s.cookie.handler.sess
        if sess and sess.modified:
                #logging.debug ('1 setting session data = %r', sess)
                #logging.debug ('2 setting user data = %r', user)
                 #obj = (dict(sess), dict(user)) if user else dict(sess)
                val = cryptoken.encodeSessionToken (sess) #, user
                if len (val) <= 4093: #some browsers will accept more but this is about the lowest browser limit
                    #logging.debug ('setting cookie = %r', val)
                    _s.cookie.set(val)
                    return True
                logging.warning ('Cookie size is %d bytes and exceeds max: 4093', n)
                #todo:what to do? too big for cookie!!!
        return False
          #  else: todo - save in token with modified timestamp (and mac) - copy the rest!
        
        
    def on_update (_s):
        _s.modified = True
        
    # def pop (_s, key, *args):
        # if key in _s:
            # return super(SessionVw, _s).pop (key, *args)# Only pop if key exists
        # if args:
            # return args[0] # no key so return the default val specified at args[0]
        # raise KeyError (key)

    # 2 funcs to maintain a list of msg items at key='_flash'
    # Each msg item is a duple (msg, level)
    def getFlashes (_s): #, key='_flash'
        """The list of Flash messages is deleted when read. """
        return _s.pop ('_flash', [])                         # a list of duples: [(msg, level), ...]

    def addFlash (_s, msg, level=None): #, key='_flash'
        '''add a (msg, level) to the list
        NB. Caller of this func must ensure the msg content is safe from injection attack. 
        Especially if it contains results from a form input. Form input should be validated server-side
        (also on client-side if possible). Any text fields that are not entirely alphanumeric are suspect.
        The msg either must be TRUSTED content (ie without any non-alphanumeric user input) 
        or else it must be html ESCAPED content, before passing to flash()
        because this msg will inserted in the template html body WITH AUTOESCAPE OFF
        '''
        _s.setdefault ('_flash', []).append((msg, level))  # append to duple list:  [(msg, level), ...]

    def logIn (_s, user, ip):
        _s['_userID'] = user.id()
        _s['_logInTS']= utils.timeStampNow()
        _s['_sessIP'] = ip
       # _s['_sessID'] = sid = utils.newSessionToken()
       # user.token = sid
       # user.modified = True
        
    def logOut (_s, user):
        if user:
            user.token = ''
            user.modified = True
        _s.pop('_userID' , None)
        _s.pop('_logInTS', None)
        _s.pop('_sessIP' , None)
       # _s.pop('_sessID' , None)

    def isLoggedIn (_s, user, ip):  
        if ( '_logInTS'in _s # \        # and '_sessID' in _s \
        and '_sessIP' in _s): 
            if user:
              #  if user.sameToken(_s['_sessID']):
                if ip == _s['_sessIP']:
                    return True
        return False

    def hasLoggedInRecently (_s, maxAge):
        timeStamp = _s['_logInTS']
        return utils.validTimeStamp (timeStamp, maxAge)
     
    
    #   3) encode(new) to save IP address when new==True to memcache and 
    #   4) decode(new) to compare IP when new==False and if different decode() fails unless memcache fails
    #   
#from google.appengine.api import memcache
    
# def get (handler):
    # sess = _get (handler.request)
    # logging.info('get sess items:||||||||||||||||||')
    # for k, v in s.iteritems():
        # logging.info('         %s : %s', k, v)
    # logging.info('|||||||||||||||||||||||||||||||||||||')

 # if not sess:
    # sess['lang'] = 'en'
    # _save (handler, sess)
    # handler.redirect_to('nocookie', abort=True)
    
    
   # cookieWasSet = memcache.get(sess['_userID'] + 'x') 
#        if cookieWasSet:
 #           sess.addFlash('There seems to be a problem reading the browser cookie. Please ensure cookies are not disabled.')
    # return sess
    
# import traceback as tb

def get (handler):
    cookie = CookieMgr (handler)
    val = cookie.get()
    if val:
        #obj = None
        #logging.debug("decode start")
        #for i in range(10):        
        obj = cryptoken.decodeToken (val, cookie.cfg)
            #logging.debug("decode %d", i)
            
        #logging.debug("decode end")
        #logging.debug ('1 getting session data = %r', obj)
        if obj is None:
            logging.warning ('deleting invalid cookie = %r', ckVal)
            cookie.delete ()
        else:
            #assert len(obj) == 2  
            # sess = SessionVw (obj[0])
            # user = SessionVw (obj[1]) if obj[1] else None
            # logging.debug ('2 getting session data = %r', (sess , user) )
            # return sess, user
            assert type(obj) is dict
            #logging.debug ('2 getting session data = %r', SessionVw (obj)  )
            
            return SessionVw (obj)
    #logging.info('No cookie found')   
    
    # for i in tb.format_list( tb.extract_stack()):
        # logging.info('No cookie found: %s', i)   
    
    return SessionVw ({})


#...............................................


