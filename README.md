# Dhamma Map

* ~~Implement user registration~~
* ~~Write code to handle login~~
* ~~Setup email verification and password recovery~~ (This has been done for you already)
* [Configure](https://developers.google.com/appengine/docs/python/config/appconfig#Secure_URLs) login and password reset urls to use https (you will have to deploy your app to test this)
	
* register domain DhammaMap.org .info?
	
### generic

* cleanup Token code	
<p>
* Send email 
	* verification
	* password recovery
<p>
* recieve email 
	* contact
<p>
* admin access page
	* test new keys	
	* resend signup verification
	* cron to cleanup incomplete signups
<p>
* authomatic
	* federated login with authomatic
<p>	
* Pure CSS
	* create colour scheme etc with yui skinner
<p> 
* form validation	
	 * client side
		 * modernizr
		 * webshims (forms)
		 * zxcvbn password strength meter
		 * mailgun email validator
	* server side
		* wtforms
<p>
* I18N with babel 
	* install babel
	* apply gettext() wrappers to 
		* .py files
		* html templates
		* .js files ? or import dict from template
	* compile to .pot file and .po files
	* translate .po files 
	* compile to .mo files
	* impl dropdown lang menu 
<p>
* impl csfr protection
	
	
### Dhamma Map
	
1. official only
	* fusion tables
	* google maps
	* data entry 
		* GS
		* Centre
		* meditator
		* potential host (looking for co-host)
	<p>
2. unofficial
	* data entry 
		* unofficial GS
		* other practises ?
		* public places ?
		* flatshare ?
	* user feedback (multiple choice only)
		* rules conformance
		* quiet
		* comfort
		* friendliness
		* easy to find
	* add messaging?
		* SMS

[markdown cheatsheet](https://github.com/adam*p/markdown*here/wiki/Markdown*Cheatsheet#lists)