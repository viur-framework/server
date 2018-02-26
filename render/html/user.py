# -*- coding: utf-8 -*-
import time, json
from string import Template
import default
from server.skeleton import Skeleton

class Render(default.Render): #Render user-data to HTML
	loginTemplate = "user_login"
	loginSuccessTemplate = "user_login_success"
	logoutSuccessTemplate = "user_logout_success"
	verifySuccessTemplate = "user_verify_success"
	verifyFailedTemplate = "user_verify_failed"
	passwdRecoverInfoTemplate = "user_passwdrecover_info"

	def login(self, skel, tpl=None,  **kwargs):
		if "loginTemplate" in dir(self.parent):
			tpl = tpl or self.parent.loginTemplate
		else:
			tpl = tpl or self.loginTemplate

		return self.edit(skel, tpl=tpl, **kwargs)

	def loginSucceeded(self, tpl=None, **kwargs):
		if "loginSuccessTemplate" in dir(self.parent):
			tpl = tpl or self.parent.loginSuccessTemplate
		else:
			tpl = tpl or self.loginSuccessTemplate

		template = self.getEnv().get_template(self.getTemplateFileName(tpl))
		return template.render(**kwargs)

	def logoutSuccess(self, tpl=None, **kwargs ):
		if "logoutSuccessTemplate" in dir( self.parent ):
			tpl = tpl or self.parent.logoutSuccessTemplate
		else:
			tpl = tpl or self.logoutSuccessTemplate
		template= self.getEnv().get_template( self.getTemplateFileName( tpl ) )
		return( template.render( **kwargs ) )

	def verifySuccess( self, skel, tpl=None,  **kwargs ):
		if "verifySuccessTemplate" in dir( self.parent ):
			tpl = tpl or self.parent.verifySuccessTemplate
		else:
			tpl = tpl or self.verifySuccessTemplate
		template= self.getEnv().get_template( self.getTemplateFileName( tpl ) )
		return( template.render( **kwargs ) )
	
	def verifyFailed( self, tpl=None,  **kwargs ):
		if "verifyFailedTemplate" in dir( self.parent ):
			tpl = tpl or self.parent.verifyFailedTemplate
		else:
			tpl = tpl or self.verifyFailedTemplate
		template= self.getEnv().get_template( self.getTemplateFileName( tpl ) )
		return( template.render( **kwargs ) )

	def passwdRecoverInfo( self, msg, skel=None, tpl=None, **kwargs ):
		if "passwdRecoverInfoTemplate" in dir( self.parent ):
			tpl = tpl or self.parent.passwdRecoverInfoTemplate
		else:
			tpl = tpl or self.passwdRecoverInfoTemplate
		template= self.getEnv().get_template( self.getTemplateFileName( tpl ) )
		if skel:
			skel = self.collectSkelData( skel )
		return( template.render( skel=skel, msg=msg, **kwargs ) )
	
	def passwdRecover(self, *args, **kwargs ):
		return( self.edit( *args, **kwargs ) )


