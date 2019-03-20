# -*- coding: utf-8 -*-
from server.render.baseRender import baseRender
from server.bones import *
from collections import OrderedDict
from xml.dom import minidom
from datetime import datetime, date, time

def serializeXML( data ):
	def recursiveSerializer( data, element ):
		if isinstance(data, dict):
			element.setAttribute('ViurDataType', 'dict')
			for key in data.keys():
				childElement = recursiveSerializer(data[key], doc.createElement(key) )
				element.appendChild( childElement )
		elif isinstance(data, (tuple, list)):
			element.setAttribute('ViurDataType', 'list')
			for value in data:
				childElement = recursiveSerializer(value, doc.createElement('entry') )
				element.appendChild( childElement )
		else:
			if isinstance(data ,  bool):
				element.setAttribute('ViurDataType', 'boolean')
			elif isinstance( data, float ) or isinstance( data, int ):
				element.setAttribute('ViurDataType', 'numeric')
			elif isinstance( data, str ) or isinstance( data, unicode ):
				element.setAttribute('ViurDataType', 'string')
			elif isinstance( data, datetime ) or isinstance( data, date ) or isinstance( data, time ):
				if isinstance( data, datetime ):
					element.setAttribute('ViurDataType', 'datetime')
				elif isinstance( data, date ):
					element.setAttribute('ViurDataType', 'date')
				else:
					element.setAttribute('ViurDataType', 'time')
				data = data.isoformat()
			elif data is None:
				element.setAttribute('ViurDataType', 'none')
				data = ""
			else:
				raise NotImplementedError("Type %s is not supported!" % type(data))
			element.appendChild( doc.createTextNode( unicode(data) ) )
		return element

	dom = minidom.getDOMImplementation()
	doc = dom.createDocument(None, u"ViurResult", None)
	elem = doc.childNodes[0]
	return( recursiveSerializer( data, elem ).toprettyxml(encoding="UTF-8") )

class DefaultRender( baseRender ):
	renderType = renderMaintype = "xml"

	def __init__(self, parent=None, *args, **kwargs ):
		super( DefaultRender,  self ).__init__( *args, **kwargs )

	def renderSkelStructure(self, skel):
		"""
		Dumps the structure of a :class:`server.db.skeleton.Skeleton`.

		:param skel: Skeleton which structure will be processed.
		:type skel: server.db.skeleton.Skeleton

		:returns: The rendered dictionary.
		:rtype: dict
		"""
		if isinstance(skel, dict):
			return None

		res = OrderedDict()

		for key, bone in skel.items():
			if "__" in key or not isinstance(bone, baseBone):
				continue

			res[key] = self.renderBoneStructure(bone)

			if key in skel.errors:
				res[key]["error"] = skel.errors[ key ]
			elif any( [x.startswith("%s." % key) for x in skel.errors.keys()]):
				res[key]["error"] = {k:v for k,v in skel.errors.items() if k.startswith("%s." % key )}
			else:
				res[key]["error"] = None

		return [(key, val) for key, val in res.items()]

	def renderTextExtension(self, ext ):
		e = ext()
		return( {"name": e.name,
				"descr": _( e.descr ),
				"skel": self.renderSkelStructure( e.dataSkel() ) } )

	def renderSkelValues(self, skel):
		"""
		Prepares values of one :class:`server.db.skeleton.Skeleton` or a list of skeletons for output.

		:param skel: Skeleton which contents will be processed.
		:type skel: server.db.skeleton.Skeleton

		:returns: A dictionary or list of dictionaries.
		:rtype: dict
		"""
		if skel is None:
			return None
		elif isinstance(skel, dict):
			return skel

		res = {}
		for key, bone in skel.items():
			res[key] = self.renderBoneValue(bone, skel, key)

		return res

	def renderEntry(self, skel, action, params = None):
		res = {
			"action": action,
			"params": params,
			"values": self.renderSkelValues(skel),
			"structure": self.renderSkelStructure(skel)
		}

		return serializeXML(res)

	def view( self, skel, action="view", params = None, *args, **kwargs):
		return self.renderEntry(skel, action, params)

	def add( self, skel, action="add", params = None, *args, **kwargs):
		return self.renderEntry(skel, action, params)

	def edit(self, skel, action="edit", params=None, *args, **kwargs):
		return self.renderEntry(skel, action, params)

	def list(self, skellist, action="list", tpl=None, params=None, **kwargs):
		res = {}
		skels = []

		for skel in skellist:
			skels.append( self.renderSkelValues( skel ) )

		res["skellist"] = skels

		if( len( skellist )>0 ):
			res["structure"] = self.renderSkelStructure( skellist[0] )
		else:
			res["structure"] = None

		res["action"] = action
		res["params"] = params
		res["cursor"] = skellist.cursor

		return serializeXML(res)

	def editItemSuccess(self, skel, params=None, **kwargs):
		return( serializeXML("OKAY") )

	def addItemSuccess(self, skel, params=None, **kwargs):
		return( serializeXML("OKAY") )
		
	def addDirSuccess(self, rootNode,  path, dirname, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )

	def renameSuccess(self, rootNode, path, src, dest, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )

	def copySuccess(self, srcrepo, srcpath, name, destrepo, destpath, type, deleteold, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )

	def deleteSuccess(self, skel, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )

	def reparentSuccess(self, obj, tpl=None, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )

	def setIndexSuccess(self, obj, tpl=None, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )

	def cloneSuccess(self, tpl=None, params=None, *args, **kwargs):
		return( serializeXML( "OKAY") )
