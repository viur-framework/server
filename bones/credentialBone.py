# -*- coding: utf-8 -*-
from server.bones import stringBone


class credentialBone(stringBone):
	"""
		A bone for storing credentials.
		This is always empty if read from the database.
		If its saved, its ignored if its values is still empty.
		If its value is not empty, it will update the value in the database
	"""
	type = "str.credential"

	def __init__(self, *args, **kwargs):
		super(credentialBone, self).__init__(*args, **kwargs)
		if self.indexed:
			raise ValueError("Credential-Bones must not be indexed!")
		if self.multiple or self.languages:
			raise ValueError("Credential-Bones cannot be multiple or translated!")

	def serialize(self, valuesCache, name, entity):
		"""
			Update the value only if a new value is supplied.
		"""
		if valuesCache.get(name, None) and valuesCache[name] != "":
			entity.set(name, valuesCache[name], self.indexed)
		return entity

	def unserialize(self, valuesCache, name, values):
		"""
			We'll never read our value from the database.
		"""
		return {}

	def buildDBFilter(self, name, skel, dbFilter, rawFilter, prefix=None):
		"""
			Prevent considering this bone in queries as it may leak our data
		"""
		return dbFilter

	def buildDBSort( self, name, skel, dbFilter, rawFilter ):
		"""
			Prevent considering this bone for sorting as it may leak our data
		"""
		return dbFilter
