# -*- coding: utf-8 -*-
from server.bones import bone
from server import request, utils
from google.appengine.api import urlfetch
import urllib
import logging
import json

class captchaBone( bone.baseBone ):
	type = "captcha"

	def __init__(self, publicKey=None, privateKey=None, *args,  **kwargs ):
		bone.baseBone.__init__(self,  *args,  **kwargs )
		self.defaultValue = self.publicKey = publicKey
		self.privateKey = privateKey
		self.required = True
		self.hasDBField = False

	def serialize(self, valuesCache, name, entity ):
		return entity

	def unserialize(self, valuesCache, name, values):
		valuesCache[name] = self.publicKey
		return True

	def fromClient(self, valuesCache, name, data):
		"""
			Reads a value from the client.
			If this value is valid for this bone,
			store this value and return None.
			Otherwise our previous value is
			left unchanged and an error-message
			is returned.

			:param name: Our name in the skeleton
			:type name: String
			:param data: *User-supplied* request-data
			:type data: Dict
			:returns: None or String
		"""
		if request.current.get().isDevServer: #We dont enforce captchas on dev server
			return None
		user = utils.getCurrentUser()
		if user and "root" in user["access"]: # Don't bother trusted users with this (not supported by admin/vi anyways)
			return None
		if not "g-recaptcha-response" in data:
			return u"No Captcha given!"
		data = {"secret": self.privateKey,
				"remoteip": request.current.get().request.remote_addr,
				"response": data["g-recaptcha-response"]
			}
		response = urlfetch.fetch(url="https://www.google.com/recaptcha/api/siteverify",
						payload=urllib.urlencode( data ),
						method=urlfetch.POST,
						headers={"Content-Type": "application/x-www-form-urlencoded"} )
		if json.loads(response.content.decode("UTF-8")).get("success"):
			return None
		return( u"Invalid Captcha" )

	def renderBoneStructure( self, renderer = None, *args, **kwargs ):
		ret = super(captchaBone, self).renderBoneStructure(renderer, *args, **kwargs)
		ret.update( {
			"publicKey": self.publicKey,
		} )
		return ret
