# -*- coding: utf-8 -*-
from server.render.baseRender import baseRender
import json
from collections import OrderedDict
from server import errors, request, bones
from server.skeleton import RefSkel, skeletonByKind
import logging

class DefaultRender(baseRender):
	renderType = renderMaintype = "json"

	def __init__(self, parent = None, *args, **kwargs):
		super(DefaultRender,  self).__init__(*args, **kwargs)
		self.parent = parent

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
			#if "__" in key or not isinstance(bone, bones.baseBone):
			#	continue

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

	def renderEntry(self, skel, actionName, params = None):
		if isinstance(skel, list):
			vals = [self.renderSkelValues(x) for x in skel]
			struct = self.renderSkelStructure(skel[0])
		else:
			vals = self.renderSkelValues(skel)
			struct = self.renderSkelStructure(skel)

		res = {
			"values": vals,
			"structure": struct,
			"action": actionName,
			"params": params
		}

		request.current.get().response.headers["Content-Type"] = "application/json"
		return json.dumps(res)

	def view(self, skel, action="view", params = None, *args, **kwargs):
		return self.renderEntry(skel, action, params)

	def add(self, skel, action = "add", params = None, **kwargs):
		return self.renderEntry(skel, action, params)

	def edit(self, skel, action = "edit", params=None, **kwargs):
		return self.renderEntry(skel, action, params)

	def list(self, skellist, action = "list", params=None, **kwargs):
		res = {}
		skels = []

		for skel in skellist:
			skels.append(self.renderSkelValues(skel))

		res["skellist"] = skels

		if skellist:
			res["structure"] = self.renderSkelStructure(skellist.baseSkel)
		else:
			res["structure"] = None

		res["cursor"] = skellist.cursor
		res["action"] = action
		res["params"] = params

		request.current.get().response.headers["Content-Type"] = "application/json"
		return json.dumps(res)

	def editItemSuccess(self, skel, params=None, **kwargs):
		return self.renderEntry(skel, "editSuccess", params)
		
	def addItemSuccess(self, skel, params=None, **kwargs):
		return self.renderEntry(skel, "addSuccess", params)
		
	def addDirSuccess(self, rootNode,  path, dirname, params=None, *args, **kwargs):
		return json.dumps("OKAY")

	def listRootNodes(self, rootNodes, tpl=None, params=None):
		return json.dumps(rootNodes)

	def listRootNodeContents(self, subdirs, entrys, tpl=None, params=None, **kwargs):
		res = {
			"subdirs": subdirs
		}

		skels = []

		for skel in entrys:
			skels.append( self.renderSkelValues( skel ) )

		res["entrys"] = skels
		return json.dumps(res)

	def renameSuccess(self, rootNode, path, src, dest, params=None, *args, **kwargs):
		return json.dumps("OKAY")

	def copySuccess(self, srcrepo, srcpath, name, destrepo, destpath, type, deleteold, params=None, *args, **kwargs):
		return json.dumps("OKAY")

	def deleteSuccess(self, skel, params=None, *args, **kwargs):
		return json.dumps("OKAY")

	def reparentSuccess(self, obj, tpl=None, params=None, *args, **kwargs):
		return json.dumps("OKAY")

	def setIndexSuccess(self, obj, tpl=None, params=None, *args, **kwargs):
		return json.dumps("OKAY")

	def cloneSuccess(self, tpl=None, params=None, *args, **kwargs):
		return json.dumps("OKAY")
