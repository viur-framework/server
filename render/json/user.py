# -*- coding: utf-8 -*-
import time, json
from string import Template
import default

class UserRender(default.DefaultRender): #Render user-data to json

	def login(self, skel, **kwargs):
		if kwargs.get("loginFailed", False):
			return json.dumps("FAILURE")

		return self.edit(skel, **kwargs)

	def loginSecondFactor(self, factor, **kwargs):
		return json.dumps(factor)

	def loginSucceeded(self, **kwargs):
		return json.dumps("OKAY")

	def logoutSuccess(self, **kwargs):
		return json.dumps("OKAY")

	def verifySuccess(self, skel, **kwargs):
		return json.dumps("OKAY")
	
	def verifyFailed(self, **kwargs):
		return json.dumps("FAILED")

	def passwdRecoverInfo(self, msg, skel=None, tpl=None, **kwargs):
		if skel:
			return self.edit(skel, **kwargs)

		return json.dumps(msg)
	
	def passwdRecover(self, *args, **kwargs):
		return self.edit(*args, **kwargs)
