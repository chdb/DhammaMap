#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals


''' NB: The sub-dict module design pattern is used here to merge over defaults in the module.
        but merging of cfg[<module>] keys over module.default-cfg keys only occurs at the module level 
Details:
If a top level key is a module name, then a subdict can be provided under that key,
and there can be a default-config dict hardcoded in the named module.
A subkey under modulename will override any key with same name in default-config.

EG for  config[<module>] the resulting cfg will be a merge of its subkeys as follows
- all keys that are only in config[<module>]
- all keys that are only in module.default_config
- plus those keys in both, but with values from config[<module>] overriding 

This works because the module (generally) calls webapp2.Config.load_config() which uses dict.update()
to replace each default val with the subdict val. However the impl of dict.update() is not recursive 

Suppose a subdict eg config[<module>] has a val1 which itself is a dict, config[<module>][<val1>]
 eg config ['webapp2_extras.jinja2']['environment_args']
and suppose there is another val2 also called 'environment_args' in the default config,
then val1 completely replaces val2 - IE within a sub-sub-dict, there's no merging or updating of elements.

This could however be done programmatically but it is complicated by the fact 
that a) in many cases, you might want to keep only some of the default values 
and  b) there are also lists to consider - whether replace or append these and what order to use?
and  c) we dont want to tinker with the code in webapp2, some of which calls webapp2.Config.load_config()

Therefore for a sub-sub-dict, when we want some/all of its default-values, we do this manually,
by copying any default-values that we want to keep, from the module. 
eg below for
        config ['webapp2_extras.jinja2'][''environment_args']
'''
from jinja_boot import set_autoescape
from collections import namedtuple

# DelayCfg = namedtuple('DelayCfg', ['delay'     # deciSeconds - minimum time between requests.
                                  # ,'latency'   # deciSeconds - maximum time for network plus browser response
                                  # ])           # ... after this it will try again. Too small will prevent page access for slow systems. Too big will cause 
                                                #Todo: set latency value at runtime from multiple of eg a redirect

LockCfg  = namedtuple('LockCfg' , ['name'      #
                                  ])

LockCfg  = namedtuple('LockCfg' , ['name'      # string - the monitor id
                                  ,'maxbad'    # number consecutive 'bad' requests in 'period' ds to trigger lockout
                                  ,'bGoodReset'# boolean - whether reset occurs for good login
                                  #,'bDiffList' # boolean - whether uses difference list
                                  ,'period'    # seconds - time permitted for < maxbad consecutive 'bad' requests
                                  ,'locktime'  # seconds - duration of lockout
                                  ])
                          # seconds
cfg={ 'maxAgeRecentLogin' : 60*10  
    , 'maxAgeSignUpTok'   : 60*60*24
    , 'maxAgePasswordTok' : 60*60  
    , 'maxAgePassword2Tok': 60*60  
    
    , 'login_wait':          10     # deciSeconds - minimum time between requests.
    , 'login_lock': LockCfg ('testname'      #name
                            , 3      #maxbad
                            , True   #bGoodReset
                            , 60*1   #period
                            , 60*3   #locktime
                            )
    , 'pepper'            : None          
    , 'log_email'         : True
    , 'email_developers'  : True
    , 'developers'        : (('Santa Klauss', 'snowypal@northpole.com'))
    
 
    # add-to/update the default_config at  \webapp2_extras\jinja2.py
    , 'webapp2_extras.jinja2':  { 'template_path'   : [ 'template' ]
                                , 'environment_args': { 'extensions': ['jinja2.ext.i18n'
                                                                      ,'jinja2.ext.autoescape'
                                                                      ,'jinja2.ext.with_'
                                                                      ]
                                                     # , 'autoescape': set_autoescape
                                                      }
                                }
    }
