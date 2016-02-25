# -*- coding: utf-8 -*-
from server.bones import baseBone
from server import request

from pynetree import Parser
import re, json

class ContentFieldParser(Parser):
	def __init__(self):
		super(ContentFieldParser, self).__init__("""
			$               /\s+/   %ignore;

			name            : /\w+/ %emit;
			value           : /[^\s,:=]+/ %emit;
			valuelist       : valuelist ',' value | value ;

			option %emit    : "type" [:=] ("input"|"textarea"|"dropdown"|"image")
			                | "descr" [:=] value
			                | "values" [:=] valuelist ;

			field           : name option* ;
			""")

	def compile(self, fielddef):
		print(fielddef)
		fielddef = fielddef.strip()
		if not fielddef:
			return None

		ast = self.parse(fielddef)
		if ast is None:
			print("PARSE ERROR")
			name = re.match(r"\w+", fielddef).group(0)
		else:
			name = ast[0][1][0][1]

		ret = {"name": name,
		       "type": "input",
		       "descr": name,
		       "values": []}

		if ast is None:
			return ret

		self.dump(ast)

		for node in ast[1:]:
			if node[0] == "option":
				opt = node[1][0][1]

				if opt == "type":
					ret["type"] = node[1][1][1]
				elif opt == "descr":
					ret["descr"] = node[1][1][1][0][1]
				elif opt == "values":
					print(node[1][1:])
					ret["values"] = [val[1][0][1] for val in node[1][1:]]

		return ret

parser = ContentFieldParser()

class contentBone(baseBone):
	type = "content"

	BASEKINDREPO = "viur-contentbone-templates"
	templatesRepo = None

	def __init__(self, templates = None, templatesKindName = None, languages = None, multiple = False, *args, **kwargs):
		super(contentBone, self).__init__( *args,  **kwargs )

		self.templates = templates if isinstance(templates, dict) else {}

		if isinstance(templatesKindName, (str, unicode)):
			self.templatesKindName = templatesKindName
		else:
			self.templatesKindName = self.BASEKINDREPO

		self.languages = languages
		self.multiple = multiple
		self.renderedValue = None

	def getTemplateFieldNames(self, tpl):
		if not tpl in self.templates.keys():
			return []

		return [re.search(r"\w+", field).group(0)
		            for field in re.findall(r"{{(\w+)[^}]*}}", self.templates[tpl]["template"])]

	def render(self, lang = None):
		if self.languages:
			if lang is None:
				lang = request.current.get().language
		else:
			lang = None

		ret = ""

		for entry in (self.value if self.multiple else [self.value]):

			tpl = self.templates.get(entry["template"])
			if not tpl:
				continue

			code = tpl["template"]

			for part in re.split("({{\w+[^}]*}})", code):
				if not (part.startswith("{{") and part.endswith("}}")):
					ret += part
					continue

				info = parser.compile(part[2:-2])
				if info is None:
					continue

				if lang:
					val = entry["values"].get("%s.%s" % (info["name"], lang), "")
				else:
					val = entry["values"].get(info["name"], "")

				fn = "renderType%s%s" % (info["type"][0].upper(), info["type"][1:])
				if fn in dir(self):
					val = getattr(self, fn)(val)

				ret += val


		return ret


	def serialize(self, name, entity):
		entity.set(name, json.dumps(self.value), False)

		if self.languages:
			for lang in self.languages:
				entity.set("%s.rendered.%s" % (name, lang), self.render(), self.indexed)
		else:
			entity.set("%s.rendered" % name, self.render(), self.indexed)

		return entity

	def unserialize(self, name, expando):
		if name in expando.keys():
			self.value = json.loads(expando[name])

			if self.languages:
				self.renderedValue = {}

				for lang in self.languages:
					if "%s.rendered.%s" % (name, lang) in expando.keys():
						self.renderedValue[lang] = expando["%s.rendered.%s" % (name, lang)]
			elif "%s.rendered" % name in expando.keys():
				self.renderedValue = expando["%s.rendered" % name]

		return True

	def fromClient(self, name, data):
		def getFields(key):
			tpl = data[key]
			values = {}

			for field in self.getTemplateFieldNames(tpl):
				if self.languages:
					for lang in self.languages:
						values.update({"%s.%s" % (field, lang): data.get("%s.%s.%s" % (key, field, lang))})
				else:
					values.update({field: data.get("%s.%s" % (key, field))})

			return {"template": tpl, "values": values}

		if self.multiple:
			idx = 0
			res = []

			while "%s.%d" % (name, idx) in data.keys():
				key = "%s.%d" % (name, idx)
				res.append(getFields(key))

				idx += 1

			self.value = res
		elif name in data.keys():
			self.value = getFields(name)

		return True


