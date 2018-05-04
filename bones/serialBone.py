# -*- coding: utf-8 -*-
from server import errors
from server.bones import baseBone

class serialBone(baseBone):
	type = "serial"

	def __init__(self, validChars="0123456789", invalidChars=None, minLength=2, maxLength = None,
	                fill=None, align=None, *args, **kwargs):
		super(serialBone, self).__init__(*args, **kwargs)
		self.validChars = validChars
		self.invalidChars = invalidChars
		self.minLength = minLength
		self.maxLength = maxLength

		assert not fill or len(fill) == 1, "fill may only be one character long!"
		self.fill = fill

		if self.fill and align is None:
			align = "right"

		assert not align or align in ["left", "right"], "align must be 'left', 'right' or None."
		self.align = align

	def format(self, value):
		if not self.align:
			return value

		if self.minLength:
			length = self.minLength
		elif self.maxLength:
			length = self.maxLength

			if self.fill and len(value) > length:
				if self.align == "right":
					while value.startswith(self.fill):
						value = value[1:]
				else:
					while value.endswith(self.fill):
						value = value[:1]
		else:
			return value

		fills = "".join([self.fill for _ in range(len(value), length)])
		return fills + value if self.align == "right" else value + fills

	def isInvalid(self, value):
		for pos, ch in enumerate(value):
			if (self.validChars and ch not in self.validChars
				or self.invalidChars and ch in self.invalidChars):
				return _(u"'{{char}}' at position {{pos}} is not allowed", char=ch, pos=pos + 1)

		if self.minLength is not None and len(value) < self.minLength:
			return _(u"Value is too short, at least {{min}} characters allowed", min=self.minLength)
		elif self.maxLength is not None and len(value) > self.maxLength:
			return _(u"Value is too long, exceeds maximum of {{max}} characters", max=self.maxLength)

		return None

	def fromClient(self, valuesCache, name, data):
		value = data.get(name)

		if value:
			value = self.format(value)
			err = self.isInvalid(value)

			if err:
				return errors.ReadFromClientError({name: err}, True)
				#return err

		elif self.required:
			return _(u"No value entered")

		valuesCache[name] = value
		return None
