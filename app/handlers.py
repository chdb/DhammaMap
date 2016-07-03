#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from google.appengine.api import taskqueue
#from google.appengine.ext.ndb import Rollback
from widget import W
import models as m
from Libs.user_agents import parse as ua_parse
import basehandler as b
import datetime as d
import logging
import cryptoken
import utils as u
import i18n as i

import debug
#import json
          
#from os import path
#import webapp2 as wa2
#import time
#import session
#import httplib as http

#tqt = 'foobar11'
#------------------------------------
class H_Home (b.H_Base):

    def get (_s):
        # x =  _s.ssn.iteritems()
        # logging.info('user ssn items:||||||||||||||||||')
        # for k, v in x:
            # logging.info('         %s : %s', k, v)
        # logging.info('|||||||||||||||||||||||||||||||||||||')
          
        # l = _s.ssn.get("lang") 
        # if not l:
            # _s.ssn["lang"] = 'en' 
            # logging.info('"lang" now set. ||||||||||||||||')
            
        # _s.sendEmail ( to = 'mr.colin.barnett@gmail.com'
                     # , subject= 'test Dhamma Map'
                     # , body= 'Hi !'
                     ## , sender
                     # )
                     
        #from google.appengine.api import taskqueue
        # p = {u'foo':u'bar'}
        # u ='/some-handler'
        # t = taskqueue.add(name=tqt, url=u, params=p)
        
        # d = t.extract_params()
        # logging.debug('XXXXXXXXXXXXXXXXXX task: %r', t)              
        # logging.debug('XXXXXXXXXXXXXXXXXX payload: %r', t.payload)              
        # logging.debug('XXXXXXXXXXXXXXXXXX params: %r', d)              
        # logging.debug('XXXXXXXXXXXXXXXXXX url: %r', u)              
        #_s.abort(422)
        _s.serve ('home.html')
        
#------------------------------------
class H_NoCookie (b.H_Base):  # handles requests redirected here by decorator: @b.cookies  

    def get (_s):
        if _s.ssn:
            # ok - so there is a cookie in there now 
            if not 'rtt' in _s.ssn:
                _s.ssn['rtt'] = u.msNow() - _s.ssn['ts'] # rtt: round trip time
                logging.debug ('rtt set in ssn')
            url = _s.request.get('nextUrl')
            _s.redirect (u.utf8(url)) # go back to the page you first thought of
        else:
            ua = _s.request.headers['User-Agent']
            res = ua_parse(ua) 
            #client = u.utf8(res)
            logging.info('cookies disabled on user agent: %s',  res)
          
            # todo put links in page with cookie enabling advice appropriate to the browser
            # "your browser platform is {{client}}"
            # "click here to learn how to enable cookies on {{client}}"
            
            _s.serve ('nocookie.html')
        
#------------------------------------
class H_Signup (b.H_Base):

    @b.cookies
    def get (_s):
        #todo  
        #or else implement this make sure all SignUp links are disabled/hidden when LoggedIn: 
        # if _s.isLoggedIn():
            # warn user she is currently logged in and will be logged out if she proceeds
            # _s.logOut()
       
        # task_queue = taskqueue.Queue('default')
        # t = task_queue.delete_tasks_by_name(tqt)
        # d = t.extract_params()
        # logging.debug('XXXXXXXXXXXXXXXXXX task: %r', t)              
        # logging.debug('XXXXXXXXXXXXXXXXXX payload: %r', t.payload)              
        # logging.debug('XXXXXXXXXXXXXXXXXX params: %r', d)              

        _s.serve ('signup.html')

    @b.rateLimit
    def post (_s, user):
        ema = _s.getEma()
        _s.ssn['ema'] = ema
        _s.sendVerifyEmail (ema, 'signingUp')
        return False, '/signup/msg' # False to block all fast repeats

    def get2 (_s):
        #TODO: COMMENT OUT the test flash :-
        ema = _s.ssn['ema'] 
        debug.show(_s,'signingUp', ema)
        
        _s.serve ('message.html', txt='An email has been sent to you.' )
        
#------------------------------------
class H_SignupToken (b.H_Base):
    
    @b.cookies
    def get (_s, token): # called by link
        logging.debug ('SignupToken GET handler called')
        _s.logOut()
        if _s.validVerifyToken (token, 'signUp'):
            _s.serve ('signup2.html')#, submit_url=url)
        else:
            _s.redirect_to ('Signup')            
            
    def post (_s, token):
        _s.logOut()
        assert token == 'x'
        praw = _s.request.get('password')
        user = m.User.createFromEmail( ema     =_s.getEma()
                                     , forename=_s.request.get('forename')
                                     , lastname=_s.request.get('lastname')
                                     , pwdhash = u.passwordHString (praw)
                                     , country = i.get_country_code(_s.request)
                                     )
        if user:
            _s.logIn (user)
            return _s.redirect_to ('Secure')
    
        _s.flash ('The email is not valid for this link.  '
        'It must be exactly the same as the one you used before. Please try again.')          
        #else:
        #    _s.flash ('The token is invalid in some way. It might be too old.  Please try again.') # , 'signup1')           
        # _s.redirect_to ('Signup')
       
#------------------------------------  
class H_Login (b.H_Base):

    @b.cookies
    def get (_s):
        _s.logOut()
        _s.serve ('login.html')#, wait=False)
        
    @b.rateLimit
    def post (_s, **ka):
        #ipa = _s.request.remote_addr
        #ema = _s.request.get('email')
        pwd = _s.request.get('password')
        #cf = _s.app.config ['loginRateLimit']
        #rl = b.RateLimiter (ema, ipa, cf)
        #if rl.ready (_s.ssn['rtt']):
        user = ka['user']
        logging.debug('user = %r',user)
        if user and m.User.byCredentials (user, pwd):
            _s.logIn(user) 
            return True, '/secure'
        _s.flash ('Login failed: either the email or the password is wrong.')
        return False, None
            #_s.doLocking(rl, ema, pwd, ipa)
        #logging.debug('login handler ##### delay: %d ms', rl.delay*100)
   #     _s.ajaxResponse (mode=rl.state, delay=rl.delay*100, nextUrl='secure') # 100 converts ds to ms
        
#------------------------------------
class H_Forgot (b.H_Base):
    
    #@b.rateLimit
    def post (_s): # "post" not "get": we dont pass the ema in the query string
        ema = _s.getEma() 
        logging.debug('################################### forgot post ema= %s',ema)
        _s.serve ('forgot.html', email=ema)
        
    @b.rateLimit
    def post2 (_s, **ka):
        ema = _s.getEma()
        _s.ssn['ema'] = ema#TODO: COMMENT OUT 
        _s.sendVerifyEmail (ema, 'forgot')
        return False, '/forgot' # False: all calls count towards a lockout  -  its always bad to forget yor password
        
    def get (_s):
        #TODO: COMMENT OUT the test flash :-
        ema = _s.ssn['ema'] 
        debug.show(_s, 'forgot', ema)
        #
        _s.serve ('message.html', txt='An email has been sent to you.' )

#------------------------------------
 
class H_NewPassword (b.H_Base):
    '''anon user has lost password 
    or auth user wants to change password'''
    
    def _serve (_s, uid, newTok):
        logging.debug ('H_NewPassword serve  called')
        assert uid, 'no uid!'
        data = (uid, newTok, _s.request.remote_addr)
        verTok = cryptoken.encodeVerifyToken (data, 'pw1')
        #url = _s.uri_for ('newpassword', token=verTok)
        _s.serve ('resetpassword.html', token=verTok)
        
    def get (_s, token):
        logging.debug ('H_NewPassword GET handler called, token = %r', token)
        # if not token:
            # newTok = u.newPasswordToken()
            # _s.loggedInRecently (_s._serve)(_s.ssn['_userID'], newTok)
        # else:
        if _s.validVerifyToken (token, 'pw1'):
            _s.serve ('resetpassword.html')#, submit_url=url)
        else:
            _s.redirect_to ('Forgot')

    def post (_s, token):
        logging.debug ('H_NewPassword POST handler called token = %s', token)
        #assert token is None
        #logging.debug ('H_NewPassword POST handler called')
        pwd = _s.request.get ('password')
        if not pwd or pwd != _s.request.get ('confirm_password'):
            _s.flash ('passwords do not match') # also do this check client side
            _s.serve ('resetpassword.html')
        else:
            # if user.validate(tid):
            ema = _s.getEma()
            user = m.User.resetPassword (ema, pwd)
            _s.logIn(user) # if user is already logged in, this will update the login timestamp
            #todo sendEmail("Your password has been changed")
            _s.flash ('Your password has been changed')
            _s.redirect_to ('Secure')
            #return 
            #_s.flash ('Password not updated.  Please try again.')

#------------------------------------
class H_Logout (b.H_Base):

    def get (_s):
        _s.logOut()
        _s.redirect_to ('Login')

#------------------------------------
class H_Secure (b.H_Base):

    @b.loggedIn
    def get (_s):#, stoken=None):
        #todo use stoken from the url, as a ssn token, when cookies are disabled
        #implement: in savesess() NoCookie = check when dummy? cookie is not coming back
        #              when NoCookie save ssn in stok in url 
        #           in getsess when NoCookie get ssn from stok in url
#        logging.debug('stoken: %s', stoken if stoken else '-')
        _s.serve ('secure.html')
        
#------------------------------------
from collections import Counter

class H_Admin (b.H_Base):

   # @b.loggedIn
    def get (_s):
    
        users = m.User.query().fetch(projection=['country'])
        users_by_country = Counter()
        for user in users:
            if user.country:
                users_by_country[user.country] += 1
                
        for n,v in users_by_country.iteritems():
            logging.info('users in %s: %d'%(n, v))
        
        params = { "data": users_by_country.items() }
    
        _s.serve('admin_geochart.html', params)

#------------------------------------
class H_AdminUserList (b.H_Base):

   # @b.loggedIn
    def get (_s):
        _s.serve('admin_users_list.html')

#------------------------------------
class H_AdminLogout (b.H_Base):
    
   # @b.loggedIn
    def get (_s):
        from google.appengine.api import users
        _s.redirect(users.create_logout_url(dest_url=self.uri_for('home')))

#------------------------------------
class H_AdminUserEdit (b.H_Base):

   # @b.loggedIn
    def edit (_s, user_id):
        _s.serve('admin_user_edit.html')
        
class H_AdminLogsEmails (b.H_Base):

   # @b.loggedIn
    def get (_s):
        _s.serve('admin_logs_emails.html')

class H_AdminEmailView (b.H_Base):

   # @b.loggedIn
    def get (_s):
        _s.serve('admin_logs_email_view.html')

class H_AdminLogsVisits (b.H_Base):

   # @b.loggedIn
    def get (_s):
        _s.serve('admin_logs_visits.html')

class H_PurgeAuthKeys (b.H_Base):

   # @b.loggedIn
    def get (_s):
        n = m.AuthKey.purge()        
        logging.info('purged %d dead AuthKeys', n)

        ##parameter in timedelta() assumes that tokens expire ~1 month1 after creation:
        # pastdate = (datetime.datetime.utcnow() - datetime.timedelta(1*365/12))
        # expiredTokens = User.token_model.query(User.token_model.created <= pastdate)
        # tokensToDelete = expiredTokens.count()
        ##delete the tokens in bulks of 100:
        # while expiredTokens.count() > 0:
            # keys = expiredTokens.fetch(100, keys_only=True)
            # ndb.delete_multi(keys)

        # _s.response.write('looking for tokens <= %s<br>%s tokens deleted <br> <a href=%s>home</a>' %
                            # (pastdate, tokensToDelete, _s.uri_for('home')))
#------------------------------------
class H_AdminNewKeys (b.H_Base):

 #   @b.loggedIn
    def post (_s):
        W.addNewKeys()

#------------------------------------
class H_TQSendEmail (b.H_Base):
    #mailgunClient = mailgun.client (wa2.get_app().config)
    
    @b.pushQueueMethod
    def post(_s):
        ka = dict(_s.request.POST.items())
        b.sendEmailNow (**ka)

#------------------------------------

class H_TQSendVerifyEmail (b.H_Base):

    @b.pushQueueMethod
    def post(_s):
        mode= _s.request.get('mode') # 'signingUp' or 'forgot'
        ema = _s.getEma()
        logging.debug('mode = %r ema = %r',mode,ema)
        signedUp = m.AuthKey._byEmail (ema)
        if mode == 'signingUp':
            subj = 'Signing Up to DhammaMap'
            if signedUp: 
                msg = _s.verifyMsg( 'There was a request to sign up with DhammaMap. '
                                    'However you are already registered. If you need to change your account details, go to '
                                    '<a href="%s">%s</a>. ', 'Home')
            else: 
                nonce = u.newSignUpToken()
                msg = _s.verifyMsg( 'Please click this link: <a href="%s">%s</a>. '
                                    'This will verify your email address so that you can continue the sign up process.'
                                  , 'Signup-token', ema, nonce, 'signUp')
        else:
            assert mode == 'forgot'
            subj = 'Lost password to DhammaMap'
            if signedUp: 
                nonce = u.newForgotToken()
                msg = _s.verifyMsg( 'Click here <a href="%s">%s</a><br>'
                                    'to proceed to security questions before changing your password.'
                                  , 'NewPassword', ema, nonce, 'pw1') 
                                    # todo: security questions
            else:
                msg = _s.verifyMsg( 'There was a request on DhammaMap for a forgotten password reset. However there is no account at DhammaMap with this email address. '
                                    'If this request was not from you, please click here to alert us ... .' #todo contact/alert page
                                    'If you want to open an account at DhammaMap please click here '
                                    '<a href="%s">%s</a>. ', 'Signup')
        #todo: comment-out!
        debug.save (mode, ema, msg)
        #
        b.sendEmailNow (to=ema,subject=subj,html=msg)
         