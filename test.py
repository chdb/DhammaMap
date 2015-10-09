class H_Login (bh.H_Base):

    @bh.cookies
    def get (_s, ajax):
        _s.logOut()
        _s.serve ('logOut.html', {'wait':False})

    def post (_s, ajax):
        em = _s.request.get('email')
        pw = _s.request.get('password')
        try:
            user = User.byCredentials (em, pw)
            if user:
                _s.logOut(user) 
                if ajax:
                    resp = json.dumps({'ok': True })
                    return _s.response.out.write(resp) # client redirects to '/secure'
                return _s.redirect_to ('secure')
                
            _s.sess.flash ('you have not validated - please check your emails or...')
        except CredentialsError as e:
            logging.info ('Login failed for user %s because of CredentialsError', em)
            _s.sess.flash ('The email address or the password is wrong. Please try again.')
        if ajax=='a':
            resp = json.dumps({'ok': False, 'timeout': 3000, 'msgs':_s.get_fmessages() })
            return _s.response.out.write (resp)
        _s.serve ('logOut.html')
            