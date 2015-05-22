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

import session
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


def rateLimit (nSeconds=1): 
    '''This decorator will rate-limit requests from the same IP to same handler class -
    a 429 'Too Many Requests' HTTP response is issued whenever a request RECURS within nSeconds,

    Mechanism - Every request from a given IP, either creates or finds an entry in memcache. An entry is unique for a given IP and Handler.
    From CREATION, entries live for nSeconds. But if an EXISTING entry is found, a 429 is issued 

    Note - This is not the same as an IDLE time of nSeconds because Failed requests do not restart the clock 
    - the clock only restarts with a successful request.
    EG you send requests every millisec, and rq0 succeeds. Then rq1 - rq999 inc fail. But 1 ms later, rq1000 will succeed!
    '''
    def rate_limiter(fn):
        @wraps(fn)
        def wrapper(h, *pa, **ka):
            if memcache.add ( '%s:%s' % ( h.__class__.__name__
                                        , h.request.remote_addr or ''
                                        )
                            , 1                 # arbitrary value
                            , time=nSeconds     # expiry from memcache
                            , namespace='rate_limiting'
                            ):
                return fn(h, *pa, **ka)  # added - ok
            return h.abort(429)          # not added - already in memcache
        return wrapper
    return rate_limiter

# class ExampleHandler(webapp2.RequestHandler):
    # @rateLimitByIP(seconds_per_request=2)
    # def get(_s):
        # _s.response.write('Hello, webapp2!')
        
#------------------------------------
    
def cookies (fn):
    """ checks that cookies are enabled in the browser"""
    def _cookies (h, *pa, **ka):        # h is for handler
        assert isinstance(h.sess, session.SessionDict)  
        if h.sess: 
            return fn (h, *pa, **ka)    #ok, proceed   
        
        # no browser cookie was read - reasons:
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

#------------------------------------
def loggedIn (fn):
    """ Checks that there's an auth user. """
    @cookies
    def _loggedin (h, *pa, **ka):
        if h.sess.isLoggedIn (h.user, h.request.remote_addr):
            logging.info('XXXXXXXXXXXXX ok - login proceed ')
            return fn (h, *pa, **ka)    #ok, proceed   
        h.redirect_to ('login', ajax='a')         # fail
        
    return _loggedin

#------------------------------------
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

#------------------------------------
def taskqueueMethod (handler):
    """ Decorator to indicate that this is a taskqueue method and applies request.headers check
    """
    def _taskqueue(h, *pa, **ka):
        """ Check if it is executed by Taskqueue in Staging or Production
            Allow run in localhost calling the url
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
from jinja2 import Template
fmsgs_tmpl = Template ("""  {% if fmessages %}
                                <ul>
                                    {% for fmsg in fmessages %}
                                        <li>
                                            {{ fmsg.0 }}
                                        </li>
                                    {% endfor %}
                                </ul>
                             {% endif %}
                      """)
#------------------------------------
class H_Base (wa2.RequestHandler):

    def __init__(_s, request, response):
        _s.initialize(request, response)
        _s.view = ViewClass()
        _s.localeStrings = i18n.getLocaleStrings(_s) # getLocaleStrings() must be called before setting path_qs in render_template()

    def login (_s, user):
        _s.sess.login (user, _s.request.remote_addr)
         
    def logout (_s):
        _s.sess.logout (_s.user)
        
    # @webapp2.cached_property
    # def jinja2 (_s):
        # return jinja2.get_jinja2 (factory=jinja_boot.jinja2_factory, app=_s.app)

    @wa2.cached_property
    def sess (_s):
        """ Shortcut to access the current sess."""
        sn = _s.request.registry['session'] = session.get(_s)
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
            session.save (_s) # Save sess after every request
        # except: # an exception in TQ handler causes the TQ to try again which loops
            # logging.exception('unexpected exception in dispatch')
    
    @wa2.cached_property
    def user (_s):
        uid = _s.sess.get('_userID')
        if uid:
            return User.byUid (uid)
        return None

    def get_fmessages (_s):
        # f = _s.sess.get_flashes()
        # logging.info('>>>>>>>>>>>>> ok added fmsgs: %r' % f)  
        fmsgs_html = fmsgs_tmpl.render (fmessages=_s.sess.get_flashes())
        # logging.info('>>>>>>>>>>>>> ok tmplate fmsgs: %r' % fmsgs_html)  
        # logging.info('>>>>>>>>>>>>> ok tmplate fmsgs: %r' %  str(fmsgs_html))  
        return utf8(fmsgs_html)

    def serve (_s, filename, params=None):
        if not params:
            params = {}
        params['user'] = _s.user
        params['locale_strings'] = _s.localeStrings
        # if not params.get('wait'): # if there's no 'wait' or its set to False
        
        #fmsgs_html = fmsgs_tmpl.render (fmsgs=_s.sess.get_flashes())
        params['fmsgs'] = f = _s.get_fmessages()
        # logging.info('>>>>>>>>>>>>>  added fmsgs: %r' % f)
        # logging.info('>>>>>>>>>>>>>  serving %s page ', filename)
        # for k,v in params.iteritems():
            # logging.info('params:  %s  =  %r', k, v)
        # viewpath = path.join (path.dirname (__file__), 'views', view_filename)
        #_s.response.out.write (template.render (viewpath, params))
        _s.response.write (Jinja().render (filename, params))

    def sendNewVerifyToken (_s, tokData, tt):
        tokenStr = cryptoken.encodeVerifyToken (tokData, tt)
        #logging.info('token = %s', tokenStr)
        if   tt == 's': route = 'signup_2'
        elif tt == 'p': route = 'newpassword'
        else: assert False
            
        verify_url = _s.uri_for ( route
                                , token=tokenStr
                                , _full=True
                                )
        logging.info('sent  url = %s', verify_url)
        
        #todo replace with 'an email has been sent' + code sending email
        #msg = ()
        _s.sess.flash('Send an email to user in order to verify their address. '
                      'Ask them to click this link: <a href="{url}">{url}</a>'
                      .format (url=verify_url)
                     )
        #_s.redirect_to('home')
        # replace with redirect
        #_s.serve ('message.html', {'message': msg})

    def ajaxResponse (_s, ajax, **ka):
        if ajax!='a':
            return False
        resp = json.dumps (ka)
        _s.response.out.write (resp)
        return True
        
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
