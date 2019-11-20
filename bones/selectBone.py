# -*- coding: utf-8 -*-
from server.bones import baseBone
from collections import OrderedDict
import logging


class selectBone(baseBone):
	type = "select"

	def __init__(self, defaultValue=None, values=None, multiple=False, *args, **kwargs):
		"""
			Creates a new selectBone.

			:param defaultValue: List of keys which will be checked by default
			:type defaultValue: list
			:param values: dict of key->value pairs from which the user can choose from. Values will be translated
			:type values: dict|OrderedDict|callable
		"""

		if defaultValue is None and multiple:
			defaultValue = []

		super(selectBone, self).__init__(defaultValue=defaultValue, multiple=multiple, *args, **kwargs)

		if "sortBy" in kwargs:
			logging.warning("The sortBy parameter is deprecated. Please use an orderedDict for 'values' instead")

		if isinstance(values, dict) and not isinstance(values, OrderedDict):
			vals = list(values.items())
			if "sortBy" in kwargs:
				sortBy = kwargs["sortBy"]

				if not sortBy in ["keys", "values"]:
					raise ValueError("sortBy must be \"keys\" or \"values\"")

				if sortBy == "keys":
					vals.sort(key=lambda x: x[0])
				else:
					vals.sort(key=lambda x: x[1])
			else:
				vals.sort(key=lambda x: x[1])

			self._values = OrderedDict(vals)

		elif isinstance(values, list):
			self._values = OrderedDict([(x, x) for x in values])

		elif isinstance(values, OrderedDict):
			self._values = values

		elif callable(values):
			self._values = values

		else:
			self._values = {}

	def __getattribute__(self, item):
		if item == "values":
			values = self._values
			if callable(values):
				values = values()
				if not isinstance(values, (dict, OrderedDict)):
					values = {}

			return values

		return super(selectBone, self).__getattribute__(item)

	def fromClient(self, valuesCache, name, data):
		values = data.get(name)

		# single case
		if not self.multiple:
			for key in self.values.keys():
				if unicode(key) == unicode(values):
					err = self.isInvalid(key)
					if not err:
						valuesCache[name] = key

					return err

			return "No or invalid value selected"

		# multiple case
		else:
			if not values:
				if not self.required:
					valuesCache[name] = []

				return "No item selected"

			if not isinstance(values, list):
				if isinstance(values, basestring):
					values = values.split(":")
				else:
					values = []

			lastErr = None
			valuesCache[name] = []

			for key, value in self.values.items():
				if unicode(key) in [unicode(x) for x in values]:
					err = self.isInvalid(key)
					if not err:
						valuesCache[name].append(key)
					else:
						lastErr = err

			if len(valuesCache[name]) > 0:
				return lastErr

			return "No item selected"


	def serialize(self, valuesCache, name, entity):
		if not self.multiple:
			return super(selectBone, self).serialize(valuesCache, name, entity)

		entity.set(name, None if not valuesCache[name] else valuesCache[name], self.indexed)
		return entity


	def unserialize(self, valuesCache, name, expando):
		if not self.multiple:
			return super(selectBone, self).unserialize(valuesCache, name, expando)

		if name in expando:
			valuesCache[name] = expando[name]

			if not valuesCache[name]:
				valuesCache[name] = []
		else:
			valuesCache[name] = []

		return True


class selectOneBone(selectBone):
	def __init__(self, *args, **kwargs):
		super(selectOneBone, self).__init__(multiple=False, *args, **kwargs)
		logging.warning("%s: The selectOneBone is deprecated. Please use selectBone() instead.", self.descr)


class selectMultiBone(selectBone):
	def __init__(self, *args, **kwargs):
		super(selectMultiBone, self).__init__(multiple=True, *args, **kwargs)
		logging.warning("%s: The selectMultiBone is deprecated. Please use selectBone(multiple=True) instead.",
						self.descr)


class selectAccessBone(selectBone):
	type = "select.access"

	def __init__(self, *args, **kwargs):
		"""
			Creates a new AccessSelectMultiBone.
			This bone encapulates elements that have a postfix "-add", "-delete",
			"-view" and "-edit" and visualizes them as a compbound unit.

			This bone is normally used in the userSkel only to provide a
			user data access right selector.
		"""
		super(selectAccessBone, self).__init__(multiple=True, *args, **kwargs)
