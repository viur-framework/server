# -*- coding: utf-8 -*-
import HTMLParser
import htmlentitydefs

from google.appengine.api import search

from server import db
from server.bones import baseBone
from server.bones.stringBone import LanguageWrapper
from server.config import conf
import logging, string


_defaultTags = {
	"validTags": [  # List of HTML-Tags which are valid
		'b', 'a', 'i', 'u', 'span', 'div', 'p', 'img', 'ol', 'ul', 'li', 'abbr', 'sub', 'sup',
		'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'br',
		'hr', 'strong', 'blockquote', 'em'],
	"validAttrs": {  # Mapping of valid parameters for each tag (if a tag is not listed here: no parameters allowed)
		"a": ["href", "target", "title"],
		"abbr": ["title"],
		"span": ["title"],
		"img": ["src", "srcset", "alt", "title"],
		"td": ["colspan", "rowspan"],
		"p": ["data-indent"],
		"blockquote": ["cite"]
	},
	"validStyles": [
		"color"
	],  # List of CSS-Directives we allow
	"validClasses": ["vitxt-*", "viur-txt-*"],  # List of valid class-names that are valid
	"singleTags": ["br", "img", "hr"]  # List of tags, which don't have a corresponding end tag
}


class HtmlSerializer(HTMLParser.HTMLParser):  # html.parser.HTMLParser
	def __init__(self, validHtml=None):
		global _defaultTags
		HTMLParser.HTMLParser.__init__(self)
		self.result = ""  # The final result that will be returned
		self.openTagsList = []  # List of tags that still need to be closed
		self.tagCache = []  # Tuple of tags that have been processed but not written yet
		self.validHtml = validHtml

	def handle_data(self, data):
		data = unicode(data) \
			.replace("<", "&lt;") \
			.replace(">", "&gt;") \
			.replace("\"", "&quot;") \
			.replace("'", "&#39;") \
			.replace("\0", "")
		if data.strip():
			self.flushCache()
			self.result += data

	def handle_charref(self, name):
		self.flushCache()
		self.result += "&#%s;" % (name)

	def handle_entityref(self, name):  # FIXME
		if name in htmlentitydefs.entitydefs.keys():
			self.flushCache()
			self.result += "&%s;" % (name)

	def flushCache(self):
		"""
			Flush pending tags into the result and push their corresponding end-tags onto the stack
		"""
		for start, end in self.tagCache:
			self.result += start
			self.openTagsList.insert(0, end)
		self.tagCache = []

	def handle_starttag(self, tag, attrs):
		""" Delete all tags except for legal ones """
		filterChars = "\"'\\\0\r\n@()"
		if self.validHtml and tag in self.validHtml["validTags"]:
			cacheTagStart = '<' + tag
			isBlankTarget = False
			styles = None
			classes = None
			for k, v in attrs:
				k = k.strip()
				v = v.strip()
				if any([c in k for c in filterChars]) or any([c in v for c in filterChars]):
					if k in {"title", "href", "alt"} and not any([c in v for c in "\"'\\\0\r\n"]):
						# If we have a title or href attribute, ignore @ and ()
						pass
					else:
						# Either the key or the value contains a character that's not supposed to be there
						continue
				elif k == "class":
					# Classes are handled below
					classes = v.split(" ")
					continue
				elif k == "style":
					# Styles are handled below
					styles = v.split(";")
					continue
				elif k == "src":
					# We ensure that any src tag starts with an actual url
					checker = v.lower()
					if not (checker.startswith("http://") or checker.startswith("https://") or \
						checker.startswith("/")):
						continue
				if not tag in self.validHtml["validAttrs"].keys() or not k in \
					self.validHtml["validAttrs"][tag]:
					# That attribute is not valid on this tag
					continue
				if k.lower()[0:2] != 'on' and v.lower()[0:10] != 'javascript':
					cacheTagStart += ' %s="%s"' % (k, v)
				if tag == "a" and k == "target" and v.lower() == "_blank":
					isBlankTarget = True
			if styles:
				syleRes = {}
				for s in styles:
					style = s[: s.find(":")].strip()
					value = s[s.find(":") + 1:].strip()
					if any([c in style for c in filterChars]) or any(
						[c in value for c in filterChars]):
						# Either the key or the value contains a character that's not supposed to be there
						continue
					if value.lower().startswith("expression") or value.lower().startswith("import"):
						# IE evaluates JS inside styles if the keyword expression is present
						continue
					if style in self.validHtml["validStyles"] and not any(
						[(x in value) for x in ["\"", ":", ";"]]):
						syleRes[style] = value
				if len(syleRes.keys()):
					cacheTagStart += " style=\"%s\"" % "; ".join(
						[("%s: %s" % (k, v)) for (k, v) in syleRes.items()])
			if classes:
				validClasses = []
				for currentClass in classes:
					validClassChars = string.ascii_lowercase + string.ascii_uppercase + string.digits + "-"
					if not all([x in validClassChars for x in currentClass]):
						# The class contains invalid characters
						continue
					isOkay = False
					for validClass in self.validHtml["validClasses"]:
						# Check if the classname matches or is white-listed by a prefix
						if validClass == currentClass:
							isOkay = True
							break
						if validClass.endswith("*"):
							validClass = validClass[:-1]
							if currentClass.startswith(validClass):
								isOkay = True
								break
					if isOkay:
						validClasses.append(currentClass)
				if validClasses:
					cacheTagStart += " class=\"%s\"" % " ".join(validClasses)
			if isBlankTarget:
				# Add rel tag to prevent the browser to pass window.opener around
				cacheTagStart += " rel=\"noopener noreferrer\""
			if tag in self.validHtml["singleTags"]:
				# Single-Tags do have a visual representation; ensure it makes it into the result
				self.flushCache()
				self.result += cacheTagStart + '>' # dont need slash in void elements in html5
			else:
				# We opened a 'normal' tag; push it on the cache so it can be discarded later if
				# we detect it has no content
				cacheTagStart += '>'
				self.tagCache.append((cacheTagStart, tag))
		else:
			self.result += " "

	def handle_endtag(self, tag):
		if self.validHtml:
			if self.tagCache:
				# Check if that element is still on the cache
				# and just silently drop the cache up to that point
				if tag in [x[1] for x in self.tagCache] + self.openTagsList:
					for tagCache in self.tagCache[::-1]:
						self.tagCache.remove(tagCache)
						if tagCache[1] == tag:
							return
			if tag in self.openTagsList:
				# Close all currently open Tags until we reach the current one. If no one is found,
				# we just close everything and ignore the tag that should have been closed
				for endTag in self.openTagsList[:]:
					self.result += "</%s>" % endTag
					self.openTagsList.remove(endTag)
					if endTag == tag:
						break

	def cleanup(self):  # FIXME: vertauschte tags
		""" Append missing closing tags """
		self.flushCache()
		for tag in self.openTagsList:
			endTag = '</%s>' % tag
			self.result += endTag

	def sanitize(self, instr):
		self.result = ""
		self.openTagsList = []
		self.feed(instr.replace("\n", " "))
		self.close()
		self.cleanup()
		return self.result



class textBone( baseBone ):
	class __undefinedC__:
		pass

	type = "text"

	@staticmethod
	def generageSearchWidget(target,name="TEXT BONE",mode="equals"):
		return ( {"name":name,"mode":mode,"target":target,"type":"text"} )

	def __init__( self, validHtml=__undefinedC__, indexed=False, languages=None, maxLength=200000, *args, **kwargs ):
		baseBone.__init__( self,  *args, **kwargs )
		if indexed:
			raise NotImplementedError("indexed=True is not supported on textBones")
		if self.multiple:
			raise NotImplementedError("multiple=True is not supported on textBones")
		if validHtml==textBone.__undefinedC__:
			global _defaultTags
			validHtml = _defaultTags
		if not (languages is None or (isinstance( languages, list ) and len(languages)>0 and all( [isinstance(x,basestring) for x in languages] ))):
			raise ValueError("languages must be None or a list of strings ")
		self.languages = languages
		self.validHtml = validHtml
		self.maxLength = maxLength
		if self.languages:
			self.defaultValue = LanguageWrapper( self.languages )

	def serialize( self, valuesCache, name, entity ):
		"""
			Fills this bone with user generated content

			:param name: The property-name this bone has in its Skeleton (not the description!)
			:type name: str
			:param entity: An instance of the dictionary-like db.Entity class
			:type entity: :class:`server.db.Entity`
			:return: the modified :class:`server.db.Entity`
		"""
		if name == "key" or not name in valuesCache:
			return( entity )
		if self.languages:
			for k in entity.keys(): #Remove any old data
				if k.startswith("%s." % name) or k.startswith("%s_" % name ) or k==name:
					del entity[ k ]
			for lang in self.languages:
				if isinstance(valuesCache[name], dict) and lang in valuesCache[name]:
					val = valuesCache[name][ lang ]
					if not val or (not HtmlSerializer().sanitize(val).strip() and not "<img " in val):
						#This text is empty (ie. it might contain only an empty <p> tag
						continue
					entity.set("%s.%s" % (name, lang), val, self.indexed)
		else:
			entity.set( name, valuesCache[name], self.indexed )
		return( entity )

	def unserialize( self, valuesCache, name, expando ):
		"""
			Inverse of serialize. Evaluates whats
			read from the datastore and populates
			this bone accordingly.

			:param name: The property-name this bone has in its Skeleton (not the description!)
			:type name: str
			:param expando: An instance of the dictionary-like db.Entity class
			:type expando: :class:`db.Entity`
		"""
		if not self.languages:
			if name in expando:
				valuesCache[name] = expando[ name ]
		else:
			valuesCache[name] = LanguageWrapper( self.languages )
			for lang in self.languages:
				if "%s.%s" % ( name, lang ) in expando:
					valuesCache[name][ lang ] = expando[ "%s.%s" % ( name, lang ) ]
			if not valuesCache[name].keys(): #Got nothing
				if name in expando: #Old (non-multi-lang) format
					valuesCache[name][ self.languages[0] ] = expando[ name ]
				for lang in self.languages:
					if not lang in valuesCache[name] and "%s_%s" % ( name, lang ) in expando:
						valuesCache[name][ lang ] = expando[ "%s_%s" % ( name, lang ) ]

		return( True )

	def fromClient( self, valuesCache, name, data ):
		"""
			Reads a value from the client.
			If this value is valid for this bone,
			store this value and return None.
			Otherwise our previous value is
			left unchanged and an error-message
			is returned.

			:param name: Our name in the skeleton
			:type name: str
			:param data: *User-supplied* request-data
			:type data: dict
			:returns: None or String
		"""
		if self.languages:
			lastError = None
			valuesCache[name] = LanguageWrapper(self.languages)
			for lang in self.languages:
				if "%s.%s" % (name,lang) in data:
					val = data["%s.%s" % (name,lang)]
					err = self.isInvalid(val) #Returns None on success, error-str otherwise
					if not err:
						valuesCache[name][lang] = HtmlSerializer(self.validHtml).sanitize(val)
					else:
						lastError = err
			if not any(valuesCache[name].values()) and not lastError:
				lastError = "No / invalid values entered"
			return lastError
		else:
			if name in data:
				value = data[name]
			else:
				value = None
			if not value:
				valuesCache[name] = ""
				return "No value entered"
			if not isinstance(value, str) and not isinstance(value, unicode):
				value = unicode(value)
			err = self.isInvalid(value)
			if not err:
				valuesCache[name] = HtmlSerializer(self.validHtml).sanitize(value)
			return err

	def isInvalid( self, value ):
		"""
			Returns None if the value would be valid for
			this bone, an error-message otherwise.
		"""
		if value==None:
			return "No value entered"
		if len(value) > self.maxLength:
			return "Maximum length exceeded"

	def getReferencedBlobs(self, valuesCache, name):
		"""
			Test for /file/download/ links inside our text body.
			Doesn't check for actual <a href=> or <img src=> yet.
		"""
		newFileKeys = []
		if self.languages:
			if valuesCache[name]:
				for lng in self.languages:
					if lng in valuesCache[name]:
						val = valuesCache[name][ lng ]
						if not val:
							continue
						idx = val.find("/file/download/")
						while idx!=-1:
							idx += 15
							seperatorIdx = min( [ x for x in [val.find("/",idx), val.find("\"",idx)] if x!=-1] )
							fk = val[ idx:seperatorIdx]
							if not fk in newFileKeys:
								newFileKeys.append( fk )
							idx = val.find("/file/download/", seperatorIdx)
		else:
			values = valuesCache.get(name)
			if values:
				idx = values.find("/file/download/")
				while idx != -1:
					idx += 15
					seperatorIdx = min([x for x in [values.find("/", idx), values.find("\"", idx)] if x != -1])
					fk = values[idx:seperatorIdx]
					if fk not in newFileKeys:
						newFileKeys.append(fk)
					idx = values.find("/file/download/", seperatorIdx)
		return newFileKeys

	def getSearchTags(self, valuesCache, name):
		res = []
		if not valuesCache.get(name):
			return( res )
		if self.languages:
			for v in valuesCache.get(name).values():
				value = HtmlSerializer( None ).sanitize(v.lower())
				for line in unicode(value).splitlines():
					for key in line.split(" "):
						key = "".join( [ c for c in key if c.lower() in conf["viur.searchValidChars"]  ] )
						if key and key not in res and len(key)>3:
							res.append( key.lower() )
		else:
			value = HtmlSerializer( None ).sanitize(valuesCache.get(name).lower())
			for line in unicode(value).splitlines():
				for key in line.split(" "):
					key = "".join( [ c for c in key if c.lower() in conf["viur.searchValidChars"]  ] )
					if key and key not in res and len(key)>3:
						res.append( key.lower() )
		return( res )

	def getSearchDocumentFields(self, valuesCache, name, prefix = ""):
		"""
			Returns a list of search-fields (GAE search API) for this bone.
		"""
		if valuesCache.get(name) is None:
			# If adding an entry using an subskel, our value might not have been set
			return []
		if self.languages:
			assert isinstance(valuesCache[name], dict), "The value shall already contain a dict, something is wrong here."

			if self.validHtml:
				return [search.HtmlField(name=prefix + name, value=unicode(valuesCache[name].get(lang, "")), language=lang)
				        for lang in self.languages]
			else:
				return [search.TextField(name=prefix + name, value=unicode(valuesCache[name].get(lang, "")), language=lang)
				        for lang in self.languages]
		else:
			if self.validHtml:
				return [search.HtmlField(name=prefix + name, value=unicode(valuesCache[name]))]
			else:
				return [search.TextField(name=prefix + name, value=unicode(valuesCache[name]))]
