#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import logging
import webapp2 as wa2
import os
import sys
import config as myConfig
import session

# Third party libraries path must be findable before importing webapp2
sys.path.insert(0, os.path.join (os.path.dirname(__file__), 'Libs'))

# logging.info ('+++++++++++++++++ ++++++++++++++++++')
# for i in sys.path:
    # logging.info ('+++++++++++++++++ %s' % i)
#------------------------------------
import handlers as h

def app_main():
    
    logging.getLogger().setLevel (logging.DEBUG)  # Note that this setting only affects app's logs not the app engine system logs
    # Can also use command line https://cloud.google.com/appengine/docs/python/tools/devserver#Python_Command-line_arguments
    # eg   -dev_appserver.py --log_level=debug    Possible values are debug, info, warning, error, and critical.
    
    logging.info('####################### startup ###############################')
    logging.info('####################### ======= ###############################')
    
    # def route(C, suffix='', **ka):   
        # n = C.__name__
        # s = n[2:].lower()
        # u = '/' + s + suffix
        # return wa2.Route (u, C, s, **ka)

    # def route(n, hm=None, ms=None, **ka): 
        # assert not n.startswith('/') 
        # m = n[:-1] if n[-1].isdigit() else n
        # m = m.replace('/','-')
        # C = eval('h.H_'+ m)
        # u = '/' if n == 'Home' else '/' + n.lower()
        # logging.debug ('route = %s,%s,%s',u, C, n )
        # return wa2.Route (u, C, n, handler_method=hm, methods=ms, **ka)

    rts = [#  url                              handlerClass      name 
  wa2.Route ('/'                             , h.H_Home         	, 'Home'               )
, wa2.Route ('/nocookie'                     , h.H_NoCookie     	, 'NoCookie'           )
, wa2.Route ('/signup'                       , h.H_Signup       	, 'Signup'             )
, wa2.Route ('/signup/msg'                   , h.H_Signup           , handler_method='get2' , methods=['GET' ])
, wa2.Route ('/signup/<token:.+>'            , h.H_SignupToken      , 'Signup-token'       )
, wa2.Route ('/forgot'                       , h.H_Forgot       	, 'Forgot'             )
, wa2.Route ('/forgot/a'                     , h.H_Forgot       	, handler_method='post2', methods=['POST'])
, wa2.Route ('/login'                        , h.H_Login        	, 'Login'              )
, wa2.Route ('/logout'                       , h.H_Logout       	, 'Logout'             )
, wa2.Route ('/secure'                       , h.H_Secure       	, 'Secure'             )
, wa2.Route ('/np/<token:.+>'                , h.H_NewPassword  	, 'NewPassword'        )
, wa2.Route ('/tqsendemail'                  , h.H_TQSendEmail  	, 'TQSendEmail'        )                           
, wa2.Route ('/tqverify'                     , h.H_TQSendVerifyEmail, 'TQSendVerifyEmail'  )
, wa2.Route ('/admin/'                       , h.H_Admin            , 'Admin-users-geochart') 
, wa2.Route ('/admin/newkeys'                , h.H_AdminNewKeys                             ) 
, wa2.Route ('/admin/users/'                 , h.H_AdminUserList    , 'Admin-users-list'            )
, wa2.Route ('/admin/logout/'                , h.H_AdminLogout      , 'Admin-logout'                )
, wa2.Route ('/admin/users/<user_id>/'       , h.H_AdminUserEdit    , 'Admin-user-edit', handler_method='edit')
, wa2.Route ('/admin/logs/emails/'           , h.H_AdminLogsEmails  , 'Admin-logs-emails'           )
, wa2.Route ('/admin/logs/emails/<email_id>/', h.H_AdminEmailView   , 'Admin-logs-email-view'       )
, wa2.Route ('/admin/logs/visits/'           , h.H_AdminLogsVisits  , 'Admin-logs-visits'           )
#, wa2.Route ('/crontasks/purgeAuthKeys/'     , h.H_PurgeAuthKeys    , 'Crontasks-purgeAuthKeys'     )
             ]
         
    # rts = [# urlbase, handler_method,  methods 
      # route ('Home'    )
    # , route ('NoCookie')
    # , route ('Signup1' , 'get1' ,['GET' ])
    # , route ('Signup2' ,  None  ,['POST'])
    # , route ('Signup3' , 'get2' ,['GET' ])
    # , route ('Forgot1' , 'post1',['POST'])
    # , route ('Forgot2' , 'post2',['POST'])
    # , route ('Forgot3' ,  None  ,['GET' ])
    # , route ('Login'   )
    # , route ('Logout'  )
    # , route ('Secure'  )
    # , route ('TQSendEmail'  )                           
    # , route ('TQVerify'     )
    # , wa2.Route ('/s2/<token:.+>'                , h.H_Signup_2   , 'signup_2'           )
    # , wa2.Route ('/np/<token:.+>'                , h.H_NewPassword, 'newpassword'        )
    # , wa2.Route ('/admin/'                       , h.H_Admin      ,'admin-users-geochart') 
    # , wa2.Route ('/admin/newkeys'                , h.H_AdminNewKeys                      ) 
    # , wa2.Route ('/admin/users/'                 , h.H_AdminUserList    , 'admin-users-list'            )
    # , wa2.Route ('/admin/logout/'                , h.H_AdminLogout      , 'admin-logout'                )
    # , wa2.Route ('/admin/users/<user_id>/'       , h.H_AdminUserEdit    , 'admin-user-edit', handler_method='edit')
    # , wa2.Route ('/admin/logs/emails/'           , h.H_AdminLogsEmails  , 'admin-logs-emails'           )
    # , wa2.Route ('/admin/logs/emails/<email_id>/', h.H_AdminEmailView   , 'admin-logs-email-view'       )
    # , wa2.Route ('/admin/logs/visits/'           , h.H_AdminLogsVisits  , 'admin-logs-visits'           )
    # , wa2.Route ('/crontasks/purgeAuthKeys/'   , h.H_PurgeAuthKeys  , 'crontasks-purgeAuthKeys'   )
             # ]
        #   , wa2.Route ('/<ttype:s|p>/<token:.+>',h.H_Verify, 'verify')
            #, wa2.Route ('/signup2'      , h.H_Signup2          )
            #, wa2.Route ('/password'     , h.H_ResetPassword    )
            
    myConfig.cfg['Env'] = 'Dev' if os.environ['SERVER_SOFTWARE'].startswith('Dev') else 'Prod'
    
    wa = wa2.WSGIApplication( rts
                            , debug =myConfig.cfg['DebugMode']
                            , config=myConfig.cfg
                            )
    session.loadConfig(wa)   # override/add-to  session config defaults with myConfig               
#    logging.debug('config = %r', a.config)
    return wa
    
app = app_main()

