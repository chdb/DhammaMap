#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import logging
import time as t
import os
import base64
from webapp2_extras import security
import datetime as d
#import config
import random
import string  
import webapp2 as wa2 

def config(key):
    '''Return the value of key in the app's config object. 
    The data is initialised by the global cfg object defined in config module but global objects are not thread safe.
    Suppose you have two modules creating two WSGIApplication's.
    Then config() will return different objects because get_app() will return different instances in a threadsafe manner.  
    The config obj is stored in the app. Therefore config() returns the right config for each app.
    All globals should be made threadsafe in this way.'''
    cfg = wa2.get_app().config
    assert key in cfg, 'config missing key"%r"' % key 
    return cfg[key]

def utf8 (u):
    assert isinstance (u, unicode)
    return u.encode('utf-8')
    
def randomPrintable():
    return random.choice(string.printable)

def hoursMins(seconds):
    assert seconds >= 0
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    str = '%d hours' % h if h else ''
    if h and m: 
        str+= ', '
    if m:
        str+= '%d minutes' % m
    return str

    
# class Singleton (object):
    # """ A non-thread-safe helper class to ease implementing singletons.
    # This should be used as a decorator -- not a metaclass -- to the class that should be a singleton.
        # @Singleton
        # class Foo (obect):
           # def __init__(_s):
               # print 'Foo created'
    # The decorated class (Foo) can define one `__init__` function that takes only the `_s` argument. 
    # Other than that, there are no restrictions that apply to the decorated class.
    # To get the singleton instance, use the `Instance` method. 
        # f = Foo.Instance()  # Good. Being explicit is in line with the Python Zen
        # g = Foo.Instance()  # Returns already created instance
        # print f is g        # True
    # Trying to use `__call__` will result in a `TypeError` being raised.
        # f = Foo()           # Error, this isn't how you get the instance of a singleton
    # Limitations: The decorated class cannot be inherited from.
    # """

    # def __init__(_s, decorated):
        # _s._decorated = decorated

    # def Instance(_s):
        # """ Returns the singleton instance. Upon its first call, it creates a
        # new instance of the decorated class and calls its `__init__` method.
        # On all subsequent calls, the already created instance is returned.
        # """
        # try:
            # return _s._instance
        # except AttributeError:
            # _s._instance = _s._decorated()
            # return _s._instance

    # def __call__(_s):
        # raise TypeError('Singletons must be accessed through `Instance()`.')

    # def __instancecheck__(_s, inst):
        # return isinstance(inst, _s._decorated)

def sNow():
    return int(t.time()) # seconds since epoch.  time() returns float with system-dependent resolution - some only resolve to nearest second

def msNow():
    return int(t.time()*1000) # milliSeconds since epoch.  

def dsNow():
    return int(t.time()*10) # deciSeconds since epoch.  

def dtExpiry(secs):
    logging.debug('secs = %r', secs)
    return d.datetime.now() + d.timedelta (seconds=secs)
    
def validTimeStamp (timeStamp, maxAge):
    assert type (timeStamp) is int
    assert maxAge is None or type (maxAge) is int
    if maxAge is None:
        return True
    logging.debug('elapsed:  %d', sNow() - timeStamp)
    logging.debug('maxAge:   %d', maxAge)
    return sNow() - timeStamp <= maxAge

#def inCfgPeriod (datetime, period):
    #t = config.config[cfg_field]
#    end = d.datetime.now() - d.timedelta(seconds=period)
#    return datetime < end

# def sameStr (a, b): # a version of this is in python 3 and 2.7.7 as hmac.compare_digest
    # r = _sameStr (a, b)
    # if not r and devServer():
        # import inspect
        # l = inspect.getargspec(sameStr)[0]
        # logging.debug('inspect XXXXXXXXXXXXXXXXXXXXXXXXX: %s ', repr(l)) 
        # logging.debug('inspect XXXXXXXXXXXXXXXXXXXXXXXXX: %s ', repr(inspect.getargspec(sameStr)[1])) 
    # return r

def sameStr (a, b): # a version of this is in python 3 and 2.7.7 as hmac.compare_digest
    """Checks if two strings, a, b have identical content. 
    The running time of this algorithm is independent of the length of the common substring.
    A naive implementation ie a == b is subject to timing attacks, because the execution time is
    roughly proportional to the length of the common substring. 
    """
    #logging.debug('a: %s', a)
    #logging.debug('b: %s', b)
    if len(a) != len(b):
        return False
    r = 0
    for x, y in zip(a, b):
        r |= ord(x) ^ ord(y)    
        #logging.debug('r: %s', r)
    return r == 0

#todo provide a raw token - they will be b64-encoded again 
#because the token is part of the Kryptoken 
def newToken():
    r = os.urandom(8) 
    #return os.urandom(8) # Todo: is this enough?  - should be plenty if we just want to avoid a clash on same machine 
    #todo Do we need to base64-encode? Surely the token will be wrappped in a crytoken which ill do it?
    return base64.b64encode(r) 

# class Verify:
    # signup = True
    # forgot = False
    
# def newVerifyToken (b):
    # assert type(b) is bool
    # if   b == Verify.signup: prefix = 's'
    # elif b == Verify.forgot: prefix = 'f'
    # else: assert False
    # return prefix + newToken()
    
def newSignUpToken ():
    return 's' + newToken()
    
def newPasswordToken ():
    return 'p' + newToken()

def newForgotToken ():
    return 'f' + newToken()
    
def newSessionToken ():
    return 'a' + newToken()
                                          
import mailgun   #  if poss we should import mailgun in only one place   
from google.appengine.api import mail      
                         
def validEmail (emailAddress):
    try: 
        return mailgun.client.validate (emailAddress)                                     
    except Exception as e:
        logging.error('Unable to validate email: %r' % e)
        return True, None

def sendEmail (**ka):
    try: 
        #todo: if mail quota not exceeded: 
        # (daily free quota is only 100 and @ max 8 per minute but you can apply for 20,000 if billing is enabled)
        logging.info ("sending email with params: %r" % ka)
        
        #todo: un-comment
        # if ka['sender'].endswith('@gmail.com') \
        # or ka['sender'].endswith('@googlemail.com'): 
            # mail.send_mail(**ka)            # api.mail.send_mail() only works with gmail as sender account
        # else:         
            # mailgun.client.sendMail(**ka)   # use mailgun   
        
        return True
    except Exception as e:
        logging.error('Unable to send email: %r' % e)
        return False

        
##todo - instead!!!!!
# from libs.passlib.hash import bcrypt
# bcrypt.encrypt("password", rounds=8)

# bcrypt.verify("password", h)
    
def passwordHString (praw):
    return security.generate_password_hash( praw
                                          , method='sha1' ##Todo: Very Bad!! Not secure for password hashing! Use bcrypt!
                                          , length=12   #num bytes of salt to generate - unless method is 'plain' when salt is ''
                                          , pepper=None)
# def hashPassword (praw, method, salt):   
    # return security.hash_password ( praw
                                  # , method
                                  # , salt
                                  # , pepper=None)

def badPassword(uph, praw):
    #logging.debug('uph = %s praw = %s', uph, praw)
    if uph.count('$') != 2:
        logging.warning('Checking creds - hashStr: "%s" has an invalid format.', uph) 
    else:
        hash, method, salt = uph.split('$', 2)
        ph = security.hash_password ( praw
                                  , method
                                  , salt
                                  , pepper=None)
        #logging.debug('hash = %s', hash)
        #logging.debug(' ph  = %s', ph)
        if sameStr (ph, hash):
            return False
    return True

#recursive version of dict.update    
# import collections
# def update(d, u):
    # for k, v in u.iteritems():
        # if isinstance(v, collections.Mapping):
            # d[k] = update(d.get(k, {}), v)
        # elif isinstance(v, list)
            # append ?
        # else:
            # d[k] = u[k]
    # return d