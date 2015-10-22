#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import logging
import time
import os
import base64
from webapp2_extras import security

def utf8 (u):
    assert isinstance (u, unicode)
    return u.encode('utf-8')

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

def timeStampNow():
    return int(time.time()) # seconds since the epoch.  time() returns float with system-dependent resolution - some only resolve to nearest second

def validTimeStamp (timeStamp, maxAge):
    assert type (timeStamp) is int
    assert maxAge is None or type (maxAge) is int
    if maxAge is None:
        return True
    return timeStampNow() - timeStamp <= maxAge


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
    r = 0
    for x, y in zip(a, b):
        r |= ord(x) ^ ord(y)    
    if len(a) != len(b):
        return False
    return r == 0

def newToken():
    r = os.urandom(15) # Todo: is this enough?  - should be plenty if we just want to avoid a clash on same machine 
    return base64.b64encode(r) # 15/3*4 == 20 bytes
    
def newSignupToken ():
    return 'signUp' + newToken()
    
def newPasswordToken ():
    return 'pw1' + newToken()

# def newForgotToken ():
    # return 'f' + newToken()
    
def newSessionToken ():
    return 'auth' + newToken()
    
def passwordHString (praw):
    return security.generate_password_hash( praw
                                          , method='sha1'
                                          , length=12   #num bytes of salt to generate - unless method is 'plain' when salt is ''
                                          , pepper=None)
                                          
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

def hashPassword (praw, method, salt):   
    return security.hash_password ( praw
                                  , method
                                  , salt
                                  , pepper=None)

def checkPassword(uph, praw):
    if uph.count('$') != 2:
        logging.warning('Checking creds - hashStr: "%s" has an invalid format.', uph) 
    else:
        hash, method, salt = uph.split('$', 2)
        ph = hashPassword (praw, method, salt)
        if sameStr (ph, hash):
            return True
    return False

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