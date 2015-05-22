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
    
    logging.getLogger().setLevel (logging.DEBUG) 
    # Note that this setting only affects app's logs not the app engine system logs
    # Can also use command line https://cloud.google.com/appengine/docs/python/tools/devserver#Python_Command-line_arguments
    # eg   -dev_appserver.py --log_level=debug    Possible values are debug, info, warning, error, and critical.
    
    logging.info('####################### startup ###############################')

    routes = [ 
      wa2.Route ('/'                             , h.H_Home       , 'home'               )
    , wa2.Route ('/nocookie'                     , h.H_NoCookie   , 'nocookie'           )
    , wa2.Route ('/<ajax:a|s>/signup'            , h.H_Signup     , 'signup'             )
    , wa2.Route ('/<ajax:a|s>/login'             , h.H_Login      , 'login'              )
    #, wa2.Route ('/aLogin'                       , h.H_aLogin     , 'alogin'             )
    , wa2.Route ('/logout'                       , h.H_Logout     , 'logout'             )
    , wa2.Route ('/forgot'                       , h.H_Forgot     , 'forgot'             )
    , wa2.Route ('/secure'                       , h.H_Auth       , 'secure'             )
    , wa2.Route ('/s2/<token:.+>'                , h.H_Signup_2   , 'signup_2'           )
    , wa2.Route ('/np/<token:.+>'                , h.H_NewPassword, 'newpassword'        )
    , wa2.Route ('/taskqueue-sendEmail/'         , h.H_SendEmail  , 'taskqueue-sendEmail')
    # , wa2.Route ('/taskqueue-badLogin/'          , h.H_BadLogin   , 'tq-badLogin'        )
    , wa2.Route ('/admin/'                       , h.H_Admin      ,'admin-users-geochart') 
    , wa2.Route ('/admin/newkeys'                , h.H_AdminNewKeys                      ) 
    , wa2.Route ('/admin/users/'                 , h.H_AdminUserList    , 'admin-users-list'            )
    , wa2.Route ('/admin/logout/'                , h.H_AdminLogout      , 'admin-logout'                )
    , wa2.Route ('/admin/users/<user_id>/'       , h.H_AdminUserEdit    , 'admin-user-edit', handler_method='edit')
    , wa2.Route ('/admin/logs/emails/'           , h.H_AdminLogsEmails  , 'admin-logs-emails'           )
    , wa2.Route ('/admin/logs/emails/<email_id>/', h.H_AdminEmailView   , 'admin-logs-email-view'       )
    , wa2.Route ('/admin/logs/visits/'           , h.H_AdminLogsVisits  , 'admin-logs-visits'           )
    , wa2.Route ('/crontasks/cleanuptokens/'     , h.H_AdminCleanupTokens,'admin-crontasks-cleanuptokens')

             ]
        #   , wa2.Route ('/<ttype:s|p>/<token:.+>',h.H_Verify, 'verify')
            #, wa2.Route ('/signup2'      , h.H_Signup2          )
            #, wa2.Route ('/password'     , h.H_ResetPassword    )
    bDebug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
    a = wa2.WSGIApplication( routes
                           , debug =bDebug
                           , config=myConfig.config
                           )
    session.loadConfig(a)   # override/add-to  session config defaults with myConfig               
    return a
    
app = app_main()

