#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import users
#from webapp2_extras import jinja2

import logging
from os import path
import webapp2 as wa2
from functools import wraps
from jinja2 import Template
from session import SessionVw
import cryptoken
import i18n
import utils
from utils import utf8
from models import User
from jinja_boot import Jinja
import json
#from widget import W
#import utils
#import httplib as http
#import time
#from google.appengine._internal.django.utils.safestring import mark_safe
#from google.appengine.ext import ndb

# handler decorators ------------------------------------

def rateLimit (fn): 
    '''To detect and foil Brute-Force attacks - 
    This decorator will issue HTTP response 429 'Too Many Requests' when the same request RECURS within nSeconds
    Same means a requests from the same IP to the same handler -
    Mechanism - Every request from a given IP, either creates or finds an entry in memcache for a given IP and Handler . 
    Memcache deletes it nSeconds after creation. If an entry is found, a 429 is issued 
    This enforces an IDLE time of nSeconds between successful requests. (Failed requests do not restart the clock )
    EG Suppose you send requests every millisec. rq0 succeeds. Then rq1 - rq999 inc fail. But rq1000 will succeed!
    '''
    #def rate_limiter(fn):
        
    @wraps(fn)
    def wrapper(h, *pa, **ka):
        for i in pa: logging.debug('pa: %r', i)
        for i in ka: logging.debug('ka: %r = %r', i, ka[i])
        
        nSeconds = h.app.config['loginDelay']
        
        
        key = '%s:%s' % ( h.__class__.__name__
                        , h.request.remote_addr or '' # ip address
                        )
        if memcache.add ( key
                        , 1                 # arbitrary value
                        , time=nSeconds     # expiry from memcache
                        #, namespace='rate_limiting'
                        ):
            #assert 'delay' not in ka 
            ka['delay'] = nSeconds * 1000
            return fn(h, *pa, **ka)  # added - ok
        # n = memcache.incr(key)
        # if n:
            # nSeconds += n
            # logging.debug('nSeconds: %r', nSeconds)
        
        # not added - found in memcache   
        if pa[0]:       
            #logging.debug('arg0: %r', arg0)
            assert pa[0] == '/ajax'
            h.flash('http code: 429 Too Many Requests')
            return h.writeResponse (mode='abort')        
        return h.abort(429)         
    return wrapper
    
    # assert len(pa1) == 1 # decorator takes one optional arg 
    # arg0 = pa1[0]
    # if callable(arg0):
        # return rate_limiter (arg0)
    # nSeconds = arg0
    # return rate_limiter
    
# class ExampleHandler(webapp2.RequestHandler):
    # @rateLimitByIP(seconds_per_request=2)
    # def get(_s):
        # _s.response.write('Hello, webapp2!')
        
#...................................-
    
def cookies (fn):
    """ checks that cookies are enabled in the browser"""
    def _cookies (h, *pa, **ka):        # h is for handler
        assert isinstance(h.sess, SessionVw)  
        if h.sess: 
            return fn (h, *pa, **ka)    #ok, proceed   
        
        # no browser cookie was read - possible reasons:
        #   1) there isnt one because: a) its the 1st time this app has been run on the browser
        #                              b) the user has deleted our cookie
        #   2) it cant be read because a) the user has disabled cookies on the browser
        #                              b) the secure attribute is set but the channel is insecure  
        #   3) the user agent does not support cookies eg a webcrawler
        # redirecting to 'nocookie' will test again, and for case 1) or 2) it will work this time
        
        h.sess['lang'] = 'en'
        
        url = h.request.path_url
        qs  = h.request.query_string
        if qs:
            url += u'?' + qs
        h.redirect_to('nocookie', nextUrl=url)

    return _cookies

#...................................-
def loggedIn (fn):
    """ Checks that there's an auth user. """
    @cookies
    def _loggedin (h, *pa, **ka):
        if h.sess.isLoggedIn (h.user, h.request.remote_addr):
            logging.info('XXXXXXXXXXXXX ok - logIn proceed ')
            return fn (h, *pa, **ka)    #ok, proceed   
        h.redirect_to ('login', ajax='a')         # fail
        
    return _loggedin

#...................................-
def loggedInRecently (fn):
    """ Checks if the auth session started recently. 
        (for handlers of sensitive operations eg change email or reset password) 
    """
    @loggedIn 
    def _loggedinRecently (h, *pa, **ka):
        if h.sess.hasLoggedInRecently (h.app.config ['maxAgeRecentLogin']):
            return fn (h, *pa, **ka)   #ok, proceed      
        h.redirect_to ('login', ajax='a')        #fail

    return _loggedinRecently

#...................................-
def taskqueueMethod (handler):
    """ Decorator to indicate that this is a taskqueue method and applies request.headers check
    """
    def _taskqueue(h, *pa, **ka):
        """ Check, if in Staging or Production, that h is being executed by Taskqueue 
            If not, allow run in localhost calling the url
        """
        if h.request.headers.get('X-AppEngine-TaskName') is None \
        and config.get('environment') == "production" \
        and not users.is_current_user_admin():
            return h.error(403) #Forbidden
        return handler(h, *pa, **ka)

    return _taskqueue

#------------------------------------
class ViewClass:
    """ ViewClass to insert variables into the template.
        ViewClass is used in H_Base to promote variables automatically that can be used in jinja2 templates.
        Use case in a H_Base Class:
            self.view.dict = dict(a=[1, 2, 3], b="hello")
        Can be accessed in the template by just using the variables like {{dict.b}}
    """
    pass
    
#------------------------------------
class H_Base (wa2.RequestHandler):

    def __init__(_s, request, response):
        _s.initialize(request, response)
        _s.view = ViewClass()
        _s.localeStrings = i18n.getLocaleStrings(_s) # getLocaleStrings() must be called before setting path_qs in render_template()

    def logIn (_s, user):
        _s.sess.logIn (user, _s.request.remote_addr)
         
    def logOut (_s):
        _s.sess.logOut (_s.user)
        
    # @webapp2.cached_property
    # def jinja2 (_s):
        # return jinja2.get_jinja2 (factory=jinja_boot.jinja2_factory, app=_s.app)

    @wa2.cached_property
    def sess (_s):
        """ Shortcut to access the current sess."""
        sn = _s.request.registry['session'] = SessionVw(_s)
        return sn

    #override wa2.RequestHandler.dispatch()
    def dispatch (_s):
        # try:
        try: # csrf protection
            if _s.request.method == "POST" \
            and not _s.request.path.startswith('/taskqueue'):
                token = _s.sess.get('_csrf_token')
                if not token \
                or token != _s.request.get('_csrf_token'):
                    _s.abort(403)
            wa2.RequestHandler.dispatch (_s) # Dispatch the request.this is needed for wa2 sessions to work
        finally:
            u = _s.user
            if u and u.modified:
                u.put() # lazy put() to not put user more than once per request 
            _s.sess.save() # Save sess after every request
        # except: # an exception in TQ handler causes the TQ to try again which loops
            # logging.exception('unexpected exception in dispatch')
    
    @wa2.cached_property
    def user (_s):
        uid = _s.sess.get('_userID')
        if uid:
            return User.byUid (uid)
        return None

    def flash(_s, msg):
        #logging.info('>>>>>>>>>>>>> msg: %r' % msg)  
        _s.sess.addFlash (msg)
         
    def get_fmessages (_s):
        f = _s.sess.getFlashes()
        #logging.info('>>>>>>>>>>>>> ok added fmsgs: %r' % f)  
        fmsgs_tmpl = Template ("""  {%- if fmessages -%}
                                        <ul>
                                            {%- for fmsg in fmessages -%}
                                                <li>{{ fmsg.0 }}</li>
                                            {%- endfor -%}
                                        </ul>
                                        <hr>
                                     {%- endif -%}
                               """)
        fmsgs_html = fmsgs_tmpl.render (fmessages= f) # _s.sess.getFlashes())
        # logging.info('>>>>>>>>>>>>> ok tmplate fmsgs: %r' % fmsgs_html)  
        # logging.info('>>>>>>>>>>>>> ok tmplate fmsgs: %r' %  str(fmsgs_html))  
        return utf8(fmsgs_html)

    def serve (_s, filename, **ka):
        ka['user'] = _s.user
        ka['locale_strings'] = _s.localeStrings
        # if not params.get('wait'): # if there's no 'wait' or its set to False
        
        #fmsgs_html = fmsgs_tmpl.render (fmsgs=_s.sess.get_flashes())
        ka['fmsgs'] = _s.get_fmessages()
        # logging.info('>>>>>>>>>>>>>  added fmsgs: %r' % f)
        # logging.info('>>>>>>>>>>>>>  serving %s page ', filename)
        # for k,v in params.iteritems():
            # logging.info('params:  %s  =  %r', k, v)
        # viewpath = path.join (path.dirname (__file__), 'views', view_filename)
        #_s.response.out.write (template.render (viewpath, params))
        _s.response.write (Jinja().render (filename, ka))

    def writeResponse (_s, **ka):
        '''use this for ajax responses'''
        ka['msgs'] = _s.get_fmessages()
        resp = json.dumps (ka)
        _s.response.write (resp)

    # def sendNewVerifyToken (_s, tokData, route):
        # tokenStr = cryptoken.encodeVerifyToken (tokData, tt)
        ##logging.info('token = %s', tokenStr)
        # if   tt == 'signUp': route = 'signup_2'
        # elif tt == 'pw1': route = 'newpassword'
        # else: assert False
            
        # verify_url = _s.uri_for ( route
                                # , token=tokenStr
                                # , _full=True
                                # )
        # logging.info('sent  url = %s', verify_url)
        
        ##todo replace with 'an email has been sent' + code sending email
        # _s.sendEmail(to=)
        # _s.flash ('An email has been sent to you. Please follow the instructions.'
                  
                 # ) 
        # _s.flash ('Click this link: <a href="{url}">{url}</a>'
                  # .format (url=verify_url)
                 # )
        #_s.redirect_to('home')
        # replace with redirect
        #_s.serve ('message.html', {'message': msg})
        
    def sendEmail (_s, **ka):  
        assert 'to'     in ka
        assert 'subject'in ka
        assert 'body'   in ka  \
            or 'html'   in ka
        # mailgun mail can also have these:   attachment inline
        # appengine mail can also have these: attachments reply_to  and also extra headers eg {List-Unsubscribe On-Behalf-Of etc}
        # both can have these:                cc bcc 
        
        if not 'sender' in ka:
            ka['sender'] = 'chdb@blueyonder.co.uk'#'sittingmap@gmail.com'
            
        # sender = params.get('sender').strip()
        ##todo this block is all about checking and setting static data so run it at startup eg in main.py 
        # if not utils.validEmail(sender):
            # cs = _s.app.config.get('contact_sender')
            # if utils.validEmail(cs):
                # sender = cs
            # else:
                # from google.appengine.api import app_identity
                # app_id = app_identity.get_application_id()
                # sender = "%s <no-reply@%s.appspotmail.com>" % (app_id, app_id)
        # params['sender'] = sender

        logging.info ('send to taskqueue' )
        taskqueue.add ( url=_s.uri_for('taskqueue-sendEmail')
                      , params=ka
                      , queue_name='mailSender'
                      , countdown=5
                      )


#------------------------------------
