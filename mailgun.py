#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import urllib
import base64
import json
from google.appengine.api import urlfetch

class MailgunAPIError (Exception) :
    pass

class Mailgun (object):
    def __init__(_s, deadline=5): # , cfg):
        apiKey          = "key-e7c4a3130a0736ab9db62de7d11cb928" # cfg['<your mailgun api key>']
        pubApiKey       = "pubkey-de2b8eec354ab953aa65771e9fc553e2"  # Mailgun public API e.g.: 'pubkey-1a2b3d4e5f67d8dc8a76c1bee5e1ef9c'
        _s.mailUrl      = "https://api.mailgun.net/v3/sandbox69a44c209d7d45cba9db1c9968a45504.mailgun.org/messages"
                        # cfg['<your mailgun mailUrl>']
        _s.validateUrl  = "https://api.mailgun.net/v2/address/validate?address="
        _s.deadline     = deadline
        _s.mailHeaders    = _s._headers(apiKey)
        _s.validateHeaders= _s._headers(pubApiKey)

    def _headers (_s, key):
        base64string = base64.encodestring('api:' + key).replace('\n','')
        return {'Authorization' : ("Basic %s" % base64string)}
           
    def _result (_s, res, name):     
        hcode = res.status_code
        rc    = json.loads(res.content) # str into dict
        if hcode != 200:
            raise MailgunAPIError('MailGun %s failed with: %d: %s : %s' % (name, hcode, rc.get('error','-'), rc.get('message','-')))
        return rc
    
    def sendMail(_s, **ka): # to, subject, body, sender=None, html=None): 
        '''returns a dict with message and id 
        eg  { "message": "Queued. Thank you."
            , "id"     : "<20150322212543.mailgun.org>"
            }
        or raises MailgunAPIError
        '''
        # some Mailgun key names are different from google ones
                            # if there is a 'sender' replace it with 'from'  else use ...
        ka['from'] = ka.pop('sender', "Mailgun Sandbox <postmaster@sandbox69a44c209d7d45cba9db1c9968a45504.mailgun.org>")
        ka['text'] = ka.pop('body', None) # replace 'body' with 'text' 
        
        r = urlfetch.fetch( _s.mailUrl
                          , deadline=_s.deadline
                          , method  = urlfetch.POST
                          , headers = _s.mailHeaders
                          , payload = urllib.urlencode(ka)
                          )
        return _s._result (r, 'sendMail')
 
    def validate (_s, address):
        '''returns True,  None  
           or      False, None
           or      False, 'suggestion@xyz.com'   (did_you_mean?)
        or raises MailgunAPIError
        '''
        r = urlfetch.fetch( _s.validateUrl + urllib.quote_plus (address)
                          , deadline=_s.deadline
                          , method  =urlfetch.GET
                          , headers =_s.validateHeaders
                          )
        rc = _s._result (r, 'validate_email')
        return rc['is_valid'], rc['did_you_mean'] # not really interested in the others eg display name
            

client = Mailgun ( # cfg
                ## , deadline=optional_urlfetch_deadline_in_seconds
                  )
####################################################

# from Libs import requests 

    
####################################################

# import urllib2
# from base64 import b64encode

# request = urllib2.Request('https://api.github.com/user')
# request.add_header('Authorization', 'Basic ' + b64encode('user' + ':' + 'pass'))
# r = urllib2.urlopen(request)

# print r.getcode()
# print r.headers["content-type"]
# print r.headers["X-RateLimit-Limit"]

 ################################################                
                 
# import datetime
# from google.appengine.api import urlfetch
# def monkeypatched_http_call(_s, url, method, **kwargs):

    # logging.info('Request[%s]: %s' % (method, url))
    # start_time = datetime.datetime.now()

    # payload = kwargs.get("data")
    # headers = kwargs.get("headers")
    # uf_response = urlfetch.fetch( url
                                # , method=method
                                # , payload=payload
                                # , headers=headers)
    ##requests.request(method, url, proxies=_s.proxies, **kwargs)

    # class _Response(object):
        # def __init__(_s, dict):
            # _s.__dict__ = dict

    ##construct a request-like response
    # response = _Response ({ 'status_code' : uf_response.status_code
                          # , 'reason'  : None
                          # , 'content' : uf_response.content
                          # , 'headers' : uf_response.headers
                          # })

    # duration = datetime.datetime.now() - start_time
    # logging.info('Response[%d]: %s, Duration: %s.%ss.' % (response.status_code, response.reason, duration.seconds, duration.microseconds))
    # debug_id = response.headers.get('PayPal-Debug-Id')
    # if debug_id:
        # logging.debug('debug_id: %s' % debug_id)

    # return _s.handle_response(response, response.content.decode('utf-8'))

# paypalrestsdk.Api.http_call = monkeypatched_http_call                 
##################################################
                 
                 
#!/usr/bin/python
"""
python-mailgun-validator
A small pure Python wrapper for the Mailgun email validator API
(http://documentation.mailgun.com/api-email-validation.html#email-validation)
"""
#import requests # todo install requests

#class MailgunAPIException(Exception):
#    pass
##################################################

