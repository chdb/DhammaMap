#!/usr/bin/python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals

import webapp2 as wa2
from webapp2_extras import jinja2
import session
import utils
import logging

def generate_csrf_token():
    session = wa2.get_request().registry['session']
    t = session.get('_csrf_token')
    if not t:
        t = utils.newToken()
        session['_csrf_token'] = t
    return t
    
def set_autoescape(template_name):
    ''' Set the auto-escaping of the template values 
        according to the file-extension'''
    if template_name is None \
    or '.' not in template_name:
        return False
    ext = template_name.rsplit('.', 1)[1]
    return ext in ('html', 'htm', 'xml')

#@utils.Singleton
class Jinja (object):

    def __init__ (_s):
        _s.instance = jinja2.get_jinja2 (factory=_s._jinja2_factory, app=wa2.get_app())
        
    @staticmethod
    def _jinja2_factory(app):
        key = 'webapp2_extras.jinja2'
        # d = utils.update (jinja2.default_config, app.config[key])
        
        # for k,v in d.iteritems():
            # logging.info('d  >>>>>>>>> %s : %s' % (k,v))
    
        j = jinja2.Jinja2(app)
        # see http://jinja.pocoo.org/docs/dev/api/#high-level-api
        # j.environment.autoescape=set_autoescape # overrides True, set in webapp2_extras.jinja2
        j.environment.filters.update({  # Set filters  ...
                                    })
        j.environment.globals.update({ 'csrf_token': generate_csrf_token
                                     , 'uri_for': wa2.uri_for
                                     , 'getattr': getattr
                                    })
        j.environment.tests.update  ({  # Set test  ...
                                    })
        # for k,v in j.config.iteritems():
            # logging.info('jinja2 cfg >>>>>>>>> %s : %s' % (k,v))
            
        # for k,v in j.environment.__dict__.iteritems():
            # logging.info('jinja2 env >>>>>>>>> %s : %s' % (k,v))
        return j

    def render (_s, template, params): 
        return _s.instance.render_template (template, **params)
