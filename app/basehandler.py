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
import i18n as i
import utils as u
import models as m
from jinja_boot import Jinja
import json
#import math
#from widget import W
#import utils
#import httplib as http
#import time
#from google.appengine._internal.django.utils.safestring import mark_safe
#from google.appengine.ext import ndb

# handler decorators ------------------------------------

def cookies (fn):
    """ checks that the cookie is found
        - some failure reasons:
          1) there isnt one because: a) its the 1st time this app has been run on the browser
                                     b) the user has deleted our cookie
          2) it cant be read because a) the user has disabled cookies on the browser
                                     b) the secure attribute is set but the channel is insecure  
          3) the user agent does not support cookies eg a webcrawler
        redirecting to 'NoCookie' will test again, and for case 1) or 2) it will work this time
        """
    def _cookies (h, *pa, **ka):        # h is for handler
        if h.ssn: 
            assert isinstance(h.ssn, SessionVw) 
            if 'rtt' in h.ssn:
                return fn (h, *pa, **ka)    #ok theres a cookie, so proceed   
        
        # no browser cookie so try again with 2 redirects: 1st to no-cookie, 2nd back to original url 
        h.ssn['lang'] = i.i18n().locale
        h.ssn['ts'] = u.msNow()
        url = h.request.path_url
        qs  = h.request.query_string
        if qs:
            url += u'?' + qs
        h.redirect_to('NoCookie', nextUrl=url) # handler will test again

    return _cookies

#..................................................................
def logSsn(d):
    for k,v in d.iteritems():
        logging.debug ('ssn: %s  =  %r', k, v)
        
def rateLimit (fn):
    @cookies 
    def _rateLimit (h, *pa, **ka):        # h is for handler
        assert h.__class__.__name__.startswith('H_')
        hlr = h.__class__.__name__[2:]
        ipa = h.request.remote_addr
        ema = h.getEma()
        params = {}
        rlt = RateLimiter (ema, ipa, hlr)
      #  logSsn(h.ssn)
        if rlt.ready (h.ssn['rtt']):
            try:
                assert 'user' not in ka
                assert ka == {}
                ka['user'] = m.User.byEmail (ema, ipa, hlr)
            except m.Locked:
                h.flash ('%s failed: this account is locked.  Please wait ... and try later.' % hlr)
            else:
                ok, next = fn(h, *pa, **ka) # CALL THE HANDLER
                lock = rlt.try_(ok)
                if lock:
                    name, duration = lock
                    logging.debug('xxxxxxxxxxxxxxxxxxxxxxxxxxx LOCK XXXXXXXXXXXXXXXX')
                    if name == 'ipa': # repeated bad attempts with same ipa but diferent ema's
                        kStr,mode,msg = ipa,'Local','you are now locked out'
                    elif name == 'ema_ipa':# repeated bad attempts with same ema and ipa
                        kStr,mode,msg = ema,'Local','this account is now locked'
                    elif name == 'ema': # repeated bad attempts with same ema but diferent ipa's
                        kStr,mode,msg = ema,'Distributed','this account is now locked'
                    m.Lock.set (kStr, duration, hlr)
                    h.flash ('Too many %s failures: %s for %s.' % (hlr, msg, u.hoursMins(duration)))
                    pwd = h.request.get('password')
                    logging.warning('%s BruteForceAttack! on %s page: start lock on %s: ema:%s pwd:%s ipa:%s',mode, hlr, name, ema, pwd, ipa)
                elif next: 
                    params['nextUrl'] = next
        # elif rlt.state =='429':
            # pwd = h.request.get('password')
            # logging.warning('BruteForceAttack? throttle failure 429 for ema:%s ipa:%s %s pwd:%s', ema, ipa, pwd)
            # h.flash('http code: 429 Too Many Requests')
        # elif rlt.state =='wait':
        else:
            params['delay'] = rlt.wait
        h.ajaxResponse (**params) 
        #todo: instead of auto unlock after n=locktime seconds, after n send user and email with unlock link 

    return _rateLimit
#..................................................................
# NB 'bad' in context of the RateLimiter means a request will count towards the lockout count.
# The handler determines which requests are 'bad'. 
# Only failed logins are 'bad' requests to rate-limited login handler 
#... but all requests to rate-limited forgot handler and signup handler are 'bad' 
# because any rapid sequence of requests to those handlers is suspect

class RateLimiter (object):
                
    def __init__(_s, ema, ipa, hlr):
        
        def _initDelay (minWait):
            _s.delay = minWait # ds
            for key, diff, cf in _s.monitors.itervalues():
                nBad = _s._get (key, diff) [0]
                if nBad:
                    #logging.debug('extra = %d for %d bad %s logins', cf.delayFn(nBad), nBad, cf.name)
                    _s.delay += cf.delayFn(nBad)
            d = _s.delay*100.0                  # Convert from int-deciseconds to float-milliseconds 
            mcka = u.config('MemCacheKeepAlive')# Divide d into a series of equal waits so each wait is the max that is less than MemCacheKeepAlive
            n = -(-d//mcka) # number of waits. NB -(-a//b) rounds up and is equivalent to math.ceil (a/b)
            _s.wait = int(-(-d//n)) # .. round up to int-millisecs
            
            logging.debug('delay = %d ms, n = %d, wait = %d ms, total = %d', d, n, _s.wait, _s.wait*n)
            assert _s.wait <= mcka
            assert n     * _s.wait >= d
            assert (n-1) * _s.wait <= d
        
        def _initMonitors (ema, ipa, hlr):
        
            def _insert (name, key, diff):
                assert name in lCfg
                #diff is the distinct value 
                _s.monitors[name] = ('L:'+hlr+':'+key, diff, lCfg[name])

            cfg = u.config(hlr)
            lCfg = cfg.lockCfg
            _s.monitors = {}
                    # name    ,key  ,diff
            _insert ('ema_ipa',_s.ei,None)
            _insert ('ema'    ,ema  ,ipa )
            _insert ('ipa'    ,ipa  ,ema )       
            #logging.debug('monitors = %r',_s.monitors)
            return cfg
        
        #_s.state = None
        _s.ei = ema + ipa
        _s.mc = memcache.Client()        
        cfg = _initMonitors (ema, ipa, hlr)
        _initDelay (cfg.minDelay)       

    def _get (_s, key, diff):
        val = _s.mc.get (key)
        if val:
            if diff:# set of distinct emails or ips
                dset, exp = val
                nBad = len(dset) # number of bad login attempts under this key
                assert nBad > 0
                return nBad, dset, exp
            return val, None, None  # in this case val is nBad
        return None, None, None  
            
    def ready (_s, rtt):
       # _s.delay += minDelay
        now = u.dsNow() # deciseconds
        key = 'W:'+ _s.ei
        expiry = _s.mc.get (key)
        logging.debug('expiry = %r  key = %s',expiry, key)
        if expiry:
            if expiry <= now:
                _s.mc.delete (key)
                #_s.state = 'good' 
                return True #handler state 'good':-> | 'bad' | 'locked'
            #_s.state = '429'
        else: # key not found 
            #_s.state = 'wait' 
            exp = _s.delay+rtt # exp = relative expiry = delay+maxLatency. For maxLatency(ds), rtt * 100 (say) gives a v rough upper limit 
            _s.mc.set (key, now+_s.delay, exp)  # ... but because rtt / 100 to convert ms to ds, maxLatency(ds) = rtt(ms) [!] - IE do nothing!
        return False                                   

    def try_ (_s, ok):
        '''Updates the monitors which are configured for this RateLimiter. 
        Return None or if a lock is triggered, the cfg for it.  
        '''
        def update (lockname):
            found = False
            lock = None
            key, diff, cfg = _s.monitors[lockname]
            nBad, dset, exp = _s._get (key, diff)
            if nBad:
                found = True     
                if ok: # the user result
                    if cfg.bGoodReset:
                        _s.mc.delete (key)
                else:   
                    if nBad < cfg.maxbad:
                        logging.debug('same %s count = %d', lockname, nBad)
                        if diff:
                            assert diff not in dset
                            dset.append(diff)
                            _s.mc.set (key, (dset,exp), exp) # set() needs explicit abs exp to keep to same exp time
                            logging.debug('diffset: %r', dset)
                        else: _s.mc.incr (key)        # incr() implicitly keeps same exp time
                    else: 
                        _s.mc.delete (key)
                        logging.debug('duration =  %r secs!', cfg.duration)
                        logging.debug('same %s count = %d  Locked for %r secs!', lockname, nBad, cfg.duration)
                        lock = lockname, cfg.duration # ok so lock the account in ndb
            elif not ok: #not found in mc so create it
                #logging.debug('ts: %x', u.dsNow())
                #logging.debug('period: %x', cfg.period)
                exp = u.sNow() + cfg.period #need use absolute time to keep same exp time when calling mc.set
                #logging.debug('exp: %x', exp)
                val = ([diff], exp) if diff else 1 # diff set needs a tuple so it knows the expiry 
                _s.mc.set (key, val, exp)
            return found, lock
        
        #assert _s.state == 'good', 'Must call ready() before calling try_()'
        found, lock = update('ema_ipa')
        if not found:
            found, lock = update('ema')
            found, lock = update('ipa')
        return lock
#------------------------------------
        
def loggedIn (fn):
    """ Checks that there's an auth user. """
    @cookies
    def _loggedin (h, *pa, **ka):
        if h.ssn.isLoggedIn (h.user, h.request.remote_addr):
            logging.debug('XXXXXXXXXXXXX ok - logIn proceed ')
            return fn (h, *pa, **ka)    #ok, proceed   
        h.redirect_to ('Login')         # fail
        
    return _loggedin

#...................................-
def loggedInRecently (fn):
    """ Checks if the auth session started recently. 
        (for handlers of sensitive operations eg change email or reset password) 
    """
    @loggedIn 
    def _loggedinRecently (h, *pa, **ka):
        if h.ssn.hasLoggedInRecently (u.config('maxAgeRecentLogin')):
            return fn (h, *pa, **ka)   #ok, proceed      
        h.redirect_to ('Login')        #fail

    return _loggedinRecently

#...................................-
def pushQueueMethod (taskhandler):
    """ Decorator to check that this is a taskqueue method using request.header
    """
    def _taskqueue(h, *pa, **ka):
        """ Check, if in Staging or Production, that h is being executed by Taskqueue 
            Otherwise, allow run in localhost calling the url
        """
        if h.request.headers.get('X-AppEngine-TaskName'):
            assert h.request.path.startswith('/tq')
        elif u.config('Env') == 'Prod': 
            if not users.is_current_user_admin():   # we cant use this test in devServer or if logged-in as admin 
                logging.warning('Someone hacking a task url? pushQueueMethod does not have taskname header')  
                return h.error(403) #Forbidden
        try:
            return taskhandler(h, *pa, **ka)
        except (TransientError, DeadlineExceededError):
            raise # keep trying! (Exceptions in Push Queue Tasks are caught by the system and retried with exp backoff.)
        except: 
            logging.exception("Task Failed:") #other exceptions - just give up!

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
        _s.localeStrings = i.getLocaleStrings(_s) # getLocaleStrings() must be called before setting path_qs in render_template()

    def getEma (_s):
        ema = _s.request.get('ema')
        # sanity check: email validation is done client side using MailGun API
        logging.debug('ema = %s', ema)
        if len(ema) < 5:
            _s.abort(422) # Unprocessable Entity 
        if '@' not in ema:
            _s.abort(422) # Unprocessable Entity 
        return ema
    
    # def decodeToken (token, type):
    # try:
            # return 
                    
        # except Base64Error:
            # logging.warning ('invalid Base64 in %s Token: %r', type, token)
        # except:
            # logging.exception('unexpected exception decoding %s token : %r', type, token)  
            
        
    def validVerifyToken (_s, token, type):
        data, expired = cryptoken.decodeToken (token, type)
        if expired:
            #if _s.logOut():
            _s.flash ('This token has expired. Please try again.')
        else:
            try:
                ema, tok = data
                logging.debug('ema found: %s' % ema)
                logging.debug('%s token found: %s', type, tok)
                if b.tqCompare (ema, tok,'tok'):
                    return True
            except:
                logging.exception('token data has unexpected structure? : %r', tokData)       
            _s.flash ('Your token is invalid. Please try again')
        return False

    def logIn (_s, user):
        _s.ssn.logIn (user, _s.request.remote_addr)
         
    def logOut (_s):
        return _s.ssn.logOut()
        
    # @webapp2.cached_property
    # def jinja2 (_s):  
        # return jinja2.get_jinja2 (factory=jinja_boot.jinja2_factory, app=_s.app)

    @property
    def ssn (_s):
        """access to the current session."""
        
        sn = _s.request.registry.get('session')
        if not sn:
           sn =_s.request.registry['session'] = SessionVw(_s)
        if sn.expired:
            if sn.logOut():
                _s.flash ('This session has expired. Please log in again.')
        return sn

    #override wa2.RequestHandler.dispatch()
    def dispatch (_s):
        try: 
        # try:# csrf protection
            if _s.request.method == "POST" \
            and not _s.request.path.startswith('/tq'): # tq indicates a TaskQueue handler: they are internal therefore not required to have csrf token
                ssnTok  = _s.ssn.get('_csrf_token')
                postTok = _s.request.get('_csrf_token')
                if (not ssnTok  # toks differ or if both are the same falsy
                or  ssnTok != postTok):
                    logging.warning('path = %r',_s.request.path)
                    logging.warning('ssn  csrf token = %r',ssnTok)
                    logging.warning('post csrf token = %r',postTok)
                    logging.warning('CSRF attack or bad or missing csrf token?')
                    wa2.abort(403) # 'Forbidden'
                    #_s.response.set_status(403)
    
            wa2.RequestHandler.dispatch (_s) # Dispatch the request.this is needed for wa2 sessions to work
        finally:
            u = _s.user
            if u and u.modified:
                u.put() # lazy put() to not put user more than once per request 
            _s.ssn.save() # Save ssn after every request
        # except: # an exception in TQ handler causes the TQ to try again which loops
            # logging.exception('unexpected exception in dispatch')
    
    @wa2.cached_property
    def user (_s):
        uid = _s.ssn.get('_userID')
        logging.debug('xxxxxxxxxx ssn = %r',_s.ssn)
        if uid:
            return m.User.byUid (uid)
        return None

    def flash(_s, msg):
        #logging.info('>>>>>>>>>>>>> msg: %r' % msg)  
        _s.ssn.addFlash (msg)
         
    def get_fmessages (_s):
        fmsgs_html = u''
        f = _s.ssn.getFlashes()
        #logging.info('>>>>>>>>>>>>> ok added fmsgs: %r' % f)  
        if f:
            fmsgsTmpl = Template (  '{%- if fmessages -%}'
                                        '{%- for fmsg in fmessages -%}'
                                            '<li>{{ fmsg.0 }}</li>'
                                        '{%- endfor -%}'
                                    '{%- endif -%}'
                                 )
            fmsgs_html = fmsgsTmpl.render (fmessages= f) # _s.ssn.getFlashes())
            # logging.info('>>>>>>>>>>>>> ok tmplate fmsgs: %r' % fmsgs_html)  
            # logging.info('>>>>>>>>>>>>> ok tmplate fmsgs: %r' %  str(fmsgs_html))  
        return u.utf8(fmsgs_html)

    def serve (_s, filename, **ka):
        ka['user'] = _s.user
        ka['locale_strings'] = _s.localeStrings
        # if not params.get('wait'): # if there's no 'wait' or its set to False
        
        #fmsgs_html = fmsgs_tmpl.render (fmsgs=_s.ssn.get_flashes())
        ka['fmsgs'] = _s.get_fmessages()
        # logging.info('>>>>>>>>>>>>>  added fmsgs: %r' % f)
        # logging.info('>>>>>>>>>>>>>  serving %s page ', filename)
        # for k,v in params.iteritems():
            # logging.info('params:  %s  =  %r', k, v)
        # viewpath = path.join (path.dirname (__file__), 'views', view_filename)
        #_s.response.out.write (template.render (viewpath, params))
        _s.response.write (Jinja().render (filename, ka))

    def ajaxResponse (_s, **ka):
        '''use this for ajax responses'''
        ka['msgs'] = _s.get_fmessages()
        resp = json.dumps (ka)
        
        # Note: old browsers may have JSON Vulnerability if the JSON string is an array [...] at top level.
        # But we are safe since ka is a python 'dictionary' so json.dumps() converts it to a JSON 'object' {...}. 
        assert resp.lstrip()[0] == '{', 'JSON Vulnerability'
        assert resp.rstrip()[-1]== '}', 'JSON Vulnerability'
        
        _s.response.write (resp)

    # def sendNewVerifyToken (_s, tokData, route):
        # tokenStr = cryptoken.encodeVerifyToken (tokData, tt)
        # #logging.info('token = %s', tokenStr)
        # if   tt == 'signUp': route = 'signup_2'
        # elif tt == 'pw1': route = 'newpassword'
        # else: assert False
            
        # verify_url = _s.uri_for ( route
                                # , token=tokenStr
                                # , _full=True
                                # )
        # logging.info('sent  url = %s', verify_url)
                            
        # #todo replace with 'an email has been sent' + code sending email
        # _s.sendEmail(to=)
        # _s.flash ('An email has been sent to you. Please follow the instructions.'
                  
                 # ) 
        # _s.flash ('Click this link: <a href="{url}">{url}</a>'
                  # .format (url=verify_url)
                 # )
        #_s.redirect_to('home')
        # replace with redirect
        #_s.serve ('message.html', {'message': msg})
        
    def verifyMsg (_s, msg, route, ema=None, nonce=None, tt=None): #todo use same string for tt as for route and simplifycode!
        assert bool(nonce) == bool(tt),'theres a nonce iff theres a tt'
        assert bool(nonce) == bool(ema),'theres a nonce iff theres a ema'
        if nonce:
            tqSave (ema, nonce,'tok')
            tok = cryptoken.encodeVerifyToken ((ema, nonce), tt)
            url = _s.uri_for (route, token=tok, _full=True)
        else:
            url = _s.uri_for (route, _full=True)    
        return msg % (url,url)
        
    def sendVerifyEmail (_s, ema, mod):
        taskqueue.add ( url=_s.uri_for('TQSendVerifyEmail')
                      , params= {'ema':ema
                                ,'mode' :mod  
                                }
                      , queue_name='mailSender' #todo use a different Q  so it can have different config. Possible Disadvantage: might spin up extra instance?
                      #, countdown=5  # wait at least this (secs) before executing task
                      )
        logging.debug ('sent verify email to taskqueue' )

    def sendEmail (_s, **ka):  
        assert  'to'     in ka
        assert  'subject'in ka
        assert( 'body'   in ka 
             or 'html'   in ka )
        # mailgun mail can also have these params/headers:   attachment inline
        # appengine mail can also have these: attachments reply_to  
        #          and also extra headers eg  List-Unsubscribe On-Behalf-Of
        # both can have these:                cc bcc 
        html = ka.get('html')
        if html and not html.endswith('\n'):
            html += '\n'
       # if not 'sender' in ka:
       #     ka['sender'] = 'chdb@blueyonder.co.uk'#'sittingmap@gmail.com'
            
        # sender = params.get('sender').strip()
        ##todo this block is all about checking and setting static data so run it at startup eg in main.py 
        # if not u.validEmail(sender):
            # cs = _s.app.config.get('contact_sender')
            # if u.validEmail(cs):
                # sender = cs
            # else:
                # from google.appengine.api import app_identity
                # app_id = app_identity.get_application_id()
                # sender = "%s <no-reply@%s.appspotmail.com>" % (app_id, app_id)
        # params['sender'] = sender

        logging.debug ('send email to taskqueue' )
        taskqueue.add ( url=_s.uri_for('TQSendEmail')
                      , params=ka
                      , queue_name='mailSender'
                      , countdown=5 # wait at least this (secs) before executing task
                      )

    # def doLocking (_s, rl, ema, pw, ipa):
        # if   rl.state == 'locked': _s.flash ('log-in failed: this account is locked.  Please wait ... and try later.')
        # elif rl.state == 'bad'   : _s.flash ('log-in failed: either the email or the password is wrong.')
        # elif rl.state == '429':
            # logging.warning('BruteForceAttack? throttle failure 429 for ema:%s ipa:%s %s pwd:%s', ema, ipa, pw)
            # _s.flash('http code: 429 Too Many Requests')
        # name, locktime = rl.try_() # try_() is a noop and returns None,None unless rl.state=='good' or 'bad'
        # if name:
            # if name == 'ipa':
                # m.BadIP.lock (ipa, locktime)
                # attack,msg = 'Local','you are now locked out'
            # elif name == 'ema_ipa':
                # m.User.lock (ema, locktime)
                # attack,msg = 'Local','this account is now locked'
            # elif name == 'ema':
                # m.User.lock (ema, locktime)
                # attack,msg = 'Distributed','this account is now locked'
            # _s.flash ('Too many log-in failures: %s for %s.' % (msg, u.hoursMins(locktime)))
            # logging.warning('%s BruteForceAttack! start lock on %s: email:%s pwd:%s ipa:%s',attack ,name, ema, pw, ipa)
            
            #todo: instead of auto unlock after n=locktime seconds, after n send user and email with unlock link 
#import datetime

def sendEmailNow (**ka):  
    ok = u.sendEmail(**ka)        
    if ok and u.config('recordEmails'):
        try:
            m.SentEmail.create (**ka)
        except: # (apiproxy_errors.OverQuotaError, BadValueError):
            logging.exception("Error saving SentEmail in datastore")

            
def tqSave (tag_, nonce, pname):
    q = taskqueue.Queue('pullq')
    #eta_ = datetime.datetime.now()
    tasks = q.lease_tasks_by_tag(1, 1000, tag=tag_)
    if tasks:
        q.delete_tasks(tasks)
        logging.info('Deleting %d old tasks for r %s!', len(tasks), tag_)
    t = taskqueue.Task(method='PULL', params={pname:nonce}, tag=tag_)#, eta=eta_)
    # , countdown=5 wait at least this (secs) before executing task
    q.add (t)
    logging.debug('added task = %r', t)


def tqCompare (tag_, token, pname):
    '''if tag is found, check that its unique. 
    Return whether its tok value is same as token, and delete if so.''' 
    q = taskqueue.Queue('pullq')
    tasks = q.lease_tasks_by_tag(0.1, 1000, tag=tag_)
    logging.debug('tasks = %r', tasks)
    n = len(tasks)
    if n == 0:
        logging.warning('Not one single pullq task for %s!', tag_) # todo try again message ?
        return False
    if n > 1:    
        logging.warning('Multiple (%d) pullq task for %s!', n, tag_)
    # GAE Bug? What does ETA really mean? For push queues its clearly the earliest time to start executing - should be ETE or ETS ?
    #           but for Pull queues it seems to be lease expiry time E the latest possible time to finish executing --  LTE ?
    # If we find multiple tasks for a tag, (there shouldnt be but in case ...) we want to read the most recent one and discard the others.
    # From Docs and StackOverflow it seems that we should use eta which we can optionally set (it should default to when the Task was created)
    # and not use the list ordering (which is unspecified in Docs )
    # However in devServer at least, the eta seem to be set to the time of lease expiry.  (current_time + lease_time)
    # and so all the leased tasks seem to always have the same eta.
    # todo: test this on env:prod and if necessary on creating a Task, pass in a creation timestamp as a param
    p = tasks[n-1].extract_params() # There should only be one but however many there are, we choose the last one ...
    logging.debug('params found: %r' % p)
    nonce = p[pname]
    if u.sameStr (token, nonce):        
        q.delete_tasks(tasks)       # .. and then delete them all
        return True
    logging.warning('url   token has: %s', token)
    logging.warning('pullq tasks has: %s', nonce)
    return False

#------------------------------------
