#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

from google.appengine.api import taskqueue
#from google.appengine.ext.ndb import Rollback
from widget import W
#from models import Email, AuthKey, User, CredentialsError
import models as m
from Libs.user_agents import parse as ua_parse
import basehandler as bh
import logging
import cryptoken
import utils
from utils import utf8
import i18n
#import json
          
#from os import path
#import webapp2 as wa2
#import time
#import session
#import config as myConfig
#import httplib as http

#------------------------------------
class H_Home (bh.H_Base):

    def get (_s):
        # x =  _s.sess.iteritems()
        # logging.info('user sess items:||||||||||||||||||')
        # for k, v in x:
            # logging.info('         %s : %s', k, v)
        # logging.info('|||||||||||||||||||||||||||||||||||||')
          
        # l = _s.sess.get("lang") 
        # if not l:
            # _s.sess["lang"] = 'en' 
            # logging.info('"lang" now set. ||||||||||||||||')
            
        # _s.sendEmail ( to = 'mr.colin.barnett@gmail.com'
                     # , subject= 'test Dhamma Map'
                     # , body= 'Hi !'
                     ## , sender
                     # )
                      
        _s.serve ('home.html')
        
#------------------------------------
class H_NoCookie (bh.H_Base):  # handles requests redirected here by decorator: @bh.cookies  

    def get (_s):
        if _s.sess:
            # ok - so there is a cookie in there now 
            url = _s.request.get('nextUrl')
            _s.redirect (utf8(url))
        else:
            ua = _s.request.headers['User-Agent']
            res = ua_parse(ua) 
            #client = utf8(res)
            logging.info('cookies disabled on user agent: %s',  res)
          
            # todo put links in page with cookie enabling advice appropriate to the browser
            # "your browser platform is {{client}}"
            # "click here to learn how to enable cookies on {{client}}"
            
            _s.serve ('nocookie.html')
        
#------------------------------------
def no_JS (q):
    assert q == 'a' or q == 's' 
    return q == 'a' # whether javascript(+ajax) seems to be disabled
    
class H_Signup (bh.H_Base):

    @bh.cookies
    def get (_s, ajax):
        #todo  
        #or else implement this make sure all SignUp links are disabled/hidden when LoggedIn: 
        # if _s.isLoggedIn():
            # warn user she is currently logged in and will be logged out if she proceeds
            # _s.logOut()
        _s.serve ('signup.html')

    def post (_s, q):
        noJS = no_JS(q)
        ok = False
        tokid = utils.newSignupToken()
        logging.debug('signup token created: %s' % tokid)
        em = _s.request.get ('email')
        if noJS:   # if so, email address validation has not been done 
            #TODO: remove temporary comment below (done for testing)
                      # = utils.validEmail(em)
            valid, suggest = True, None
            if valid or suggest:
                s = 'valid' if valid else 'invalid'
                msg = 'This email address is %s: <strong>"%s"</strong>' % (s, em)
                if suggest:
                    s = 'But perhaps you meant: ' if valid else 'Did you mean: '
                    msg += 'Did you mean: <strong>"%s"</strong> ?' % (s, suggest)
                _s.flash (msg) 
        else: valid = True
        if valid:
            if m.AuthKey.createOwnID (em, tokid):
                _s.sendNewVerifyToken (tokid, 'signUp')
                ok = True
              #  _s.ajaxResponse (ajax, ok=True ):  
            else:     
                _s.flash ('Sorry, this email address is already taken. Please choose a different one.')
        if noJS:
            _s.writeResponse (ok=ok, timeout=1000)
        else:
            _s.serve ('signup.html')
                
#------------------------------------
class H_Signup_2 (bh.H_Base):

    @bh.cookies
    def get (_s, token):
        logging.debug ('signup_2 GET handler called')
        _s.logOut()
        #logging.debug('signup token resent: %s' % token)
        url = _s.uri_for ('signup_2', token=token)
        _s.serve ('signup2.html', {'submit_url':url})
      
    def post (_s, token):
        _s.logOut()
        try:
            tokID = cryptoken.decodeToken (token, _s.app.config, 'signUp')
            logging.debug('signup token found: %s' % tokID)
            if tokID:
                praw = _s.request.get('password')
                ctry = i18n.get_country_code(_s.request) or ''
                user = m.User.credSignup( tokID
                                      , _s.request.get('email')
                                      , pwdhash = utils.passwordHString (praw)
                                      , forename=_s.request.get('forename')
                                      , lastname=_s.request.get('lastname')
                                      , country = ctry
                                      )
                if user:
                    _s.logIn (user)
                    return _s.redirect_to ('secure')
        
        except m.CredentialsError:
            _s.flash ('The email or password is not valid for this link.  '
            'They must be exactly the same as the ones you used before. Please try again.')          
        else:
            _s.flash ('This link is invalid in some way. It might be too old.  Please try again.') # , 'signup1')           
        _s.redirect_to ('signup')
       
#------------------------------------   
class H_Forgot (bh.H_Base):

    def get (_s):
        _s.logOut()
        _s.serve ('forgot.html')

    def post (_s):
        em = _s.request.get ('email')
        user = m.User._byOwnID (em)
        if user:
            # todo:  checks eg security questions, captcha
            tokid = utils.newForgotToken()
            logging.debug ('@bh token = %s',tokid)
            user.setToken (tokid)
            _s.sendNewVerifyToken ((user.id(), tokid), 'pw1')
            _s.serve ('message.html')
        else:
            logging.info ('Could not find any user entry for username: %s', em)
            _s.flash('We could not find any user with this username.')
            _s.serve ('forgot.html')

#------------------------------------
class H_NewPassword (bh.H_Base):
    '''get and post are called when 1) anon user has lost password 
                                or  2) auth user wants to change password'''

    def serve (_s, uid, newTok):
        logging.debug ('H_NewPassword serve  called')
        assert uid, 'no uid!'
        data = (uid, newTok, _s.request.remote_addr)
        verTok = cryptoken.encodeVerifyToken (data, 'q')
        #url = _s.uri_for ('newpassword', token=verTok)
        _s.serve ('resetpassword.html', {'token':verTok})
        
    def get (_s, token):
        logging.debug ('H_NewPassword GET handler called')
        if not token:
            newTok = utils.newPasswordToken()
            return loggedInRecently(_s.serve) (_s.sess['_userID'], newTok)

        tokData = cryptoken.decodeToken (token, _s.app.config, 'pw1')
        if tokData:
            uid, oldTok = tokData
            user = m.User.byUid(uid)
            if user:
                newTok = utils.newPasswordToken()
                if user.validate(oldTok, newTok):
                    return _s.serve (uid, newTok)
        _s.logOut()
        _s.flash ('Your token is invalid. It may have expired. Please try again')
        return _s.redirect_to ('forgot')

    def post (_s, token):
        logging.debug ('H_NewPassword POST handler called token = %s', token)
        #assert token is None
        #logging.debug ('H_NewPassword POST handler called')
        pw = _s.request.get ('password')
        if not pw or pw != _s.request.get ('confirm_password'):
            _s.flash ('passwords do not match') # also do this check client side
        else:
            token = utf8(_s.request.get ('t'))
            data = cryptoken.decodeToken (token, _s.app.config, 'pw2')
            if data:
                uid, tid, ip = data
                if uid:
                    user = m.User.byUid(uid)
                    if user:
                        logging.debug ('H_NewPassword user found')
                        if ip == _s.request.remote_addr:
                            if user.validate(tid):
                                user.setPassword (pw)
                                _s.logIn(user) # if user is already logged in, this will update the login timestamp
                                #todo sendEmail("Your password has been changed")
                                _s.flash ('Your password has been changed')
                                return _s.redirect_to ('secure')
            _s.flash ('Password not updated.  Please try again.')
        _s.redirect_to ('forgot')

#------------------------------------
# class H_BadLogin (bh.H_Base):
    # def get (_s):
        # logging.info ('OK login again' )
        # _s.logOut()
       

    # @bh.taskqueueMethod
    # def post (_s):
        # logging.info ('do bad login result' )
        # _s.logOut()
        # _s.flash ('OK you can try again now.')
        # _s.redirect_to ('login')
        # _s.serve ('home.html') # ('login.html', {'wait':False})
#------------------------------------
# class H_Login (bh.H_Base):

    # @bh.cookies
    # def get (_s):
        # _s.logOut()
        # _s.serve ('login.html', {'wait':False})

    # def post (_s):
        # em = _s.request.get ('email')
        # try:
            # user = m.User.byCredentials (em, _s.request.get('password'))
            # if user:
                # _s.login(user) 
                # logging.info ('LogGED in OK - NOW REDIRECT TO SECURE')
                # return _s.redirect_to ('secure')
                
            # _s.flash ('you have not validated - please check your emails or...')
        # except m.CredentialsError as e:
            # logging.info ('Login failed for user %s because of CredentialsError', em)
            # _s.flash ('The email address or the password is wrong. Please try again.')
        # _s.serve ('login.html', {'wait':True})

#------------------------------------
class H_Login (bh.H_Base):

    @bh.cookies
    def get (_s, q=False):
        _s.logOut()
        _s.serve ('login.html', {'wait':False})

    @bh.rateLimit
    def post (_s, ajax=False):
        logging.debug('~~~~~~ ######### q=%r'%ajax)
        #noJS = no_JS(q)
        em = _s.request.get('email')
        pw = _s.request.get('password')
        logging.debug('~~~~~~ ######### em=%r'%em)
        logging.debug('~~~~~~ ######### pw=%r'%pw)
        try:
            user = m.User.byCredentials (em, pw)
            if user:
                _s.logIn(user) 
                if ajax:
                    return _s.redirect_to ('secure')
                return _s.writeResponse (mode='ok', url='secure') 
            logging.error('no user')
        except m.CredentialsError as e:
            if _s.app.config['HighSecurity']:
                _s.flash ('If you have completed the sign-up process, then either the username or the password is wrong. Please try again or click "signUp" to register your login details.')
            else:
                _s.flash (e.userMsg)          
        if ajax:
            _s.writeResponse (mode='wait', delay=5000)
        else:
            _s.serve ('login.html')

#------------------------------------
class H_Logout (bh.H_Base):

    def get (_s):
        _s.logOut()
        _s.redirect_to ('home')

#------------------------------------
class H_Auth (bh.H_Base):

    @bh.loggedIn
    def get (_s, stoken=None):
        #todo use stoken from the url, as a sess token, when cookies are disabled
        #implement: in savesess() NoCookie = check when dummy? cookie is not coming back
        #              when NoCookie save sess in stok in url 
        #           in getsess when NoCookie get sess from stok in url
        logging.debug('stoken: %s', stoken if stoken else '-')
        _s.serve ('secure.html')
        
#------------------------------------
from collections import Counter

class H_Admin (bh.H_Base):

   # @bh.loggedIn
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
class H_AdminUserList (bh.H_Base):

   # @bh.loggedIn
    def get (_s):
        _s.serve('admin_users_list.html')

#------------------------------------
class H_AdminLogout (bh.H_Base):
    
   # @bh.loggedIn
    def get (_s):
        from google.appengine.api import users
        _s.redirect(users.create_logout_url(dest_url=self.uri_for('home')))

#------------------------------------
class H_AdminUserEdit (bh.H_Base):

   # @bh.loggedIn
    def edit (_s, user_id):
        _s.serve('admin_user_edit.html')
        
class H_AdminLogsEmails (bh.H_Base):

   # @bh.loggedIn
    def get (_s):
        _s.serve('admin_logs_emails.html')

class H_AdminEmailView (bh.H_Base):

   # @bh.loggedIn
    def get (_s):
        _s.serve('admin_logs_email_view.html')

class H_AdminLogsVisits (bh.H_Base):

   # @bh.loggedIn
    def get (_s):
        _s.serve('admin_logs_visits.html')

class H_PurgeAuthKeys (bh.H_Base):

   # @bh.loggedIn
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
class H_AdminNewKeys (bh.H_Base):

 #   @bh.loggedIn
    def post (_s):
        W.addNewKeys()

#------------------------------------
class H_SendEmail (bh.H_Base):
    #mailgunClient = mailgun.client (wa2.get_app().config)
    
    @bh.taskqueueMethod
    def post(_s):
        params = dict(_s.request.POST.items())
        logging.info ("params: %r" % params)
         
        ok = utils.sendEmail(**params)
        
        if _s.app.config['log_email']:
            try:
                log = m.Email (sent=ok, **params)
                log.put()
            except: # (apiproxy_errors.OverQuotaError, BadValueError):
                logging.exception("Error saving Email Log in datastore")
 