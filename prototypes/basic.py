#-*- coding: utf-8 -*-
from server import conf, errors, utils, exposed
from server.skeleton import MetaSkel, Skeleton, skeletonByKind

class BasicApplication(object):
	"""
	BasicApplication is a generic class serving as the base for the four BasicApplications.

	:ivar kindName: Name of the kind of data entities that are managed by the application. \
	This information is used to bind a specific :class:`server.skeleton.Skeleton`-class to the \
	application. For more information, refer to the function :func:`_resolveSkel`.
	:vartype kindName: str

	:ivar render: will be set to the appropriate render instance at runtime
	"""

	kindName = None  # The generic kindname for this module.

	adminInfo = None
	accessRights = None

	def __init__(self, moduleName, modulePath, *args, **kwargs):
		self.moduleName = moduleName
		self.modulePath = modulePath
		self.render = None

		if self.adminInfo and self.accessRights:
			for r in self.accessRights:
				rightName = "%s-%s" % (moduleName, r)

				if not rightName in conf["viur.accessRights"]:
					conf["viur.accessRights"].append(rightName)

	def _resolveSkelCls(self, *args, **kwargs):
		"""
		Retrieve the generally associated :class:`server.skeleton.Skeleton` that is used by
		the application.

		This is either be defined by the member variable *kindName* or by a Skeleton named like the
		application class in lower-case order.

		If this behavior is not wanted, it can be definitely overridden by defining module-specific
		:func:`viewSkel`,:func:`addSkel`, or :func:`editSkel` functions, or by overriding this
		function in general.

		:return: Returns a Skeleton instance that matches the application.
		:rtype: server.skeleton.Skeleton
		"""

		return skeletonByKind(self.kindName if self.kindName else unicode(type(self).__name__).lower())

	def canDesc(self, skel):
		"""
		Access control function for description permission.

		Checks if the current user has the permission to view the description of the underlying data model.

		The default behavior is:
		- If `skel` is not "_resolveSkelCls" or ends with "Skel".
		- If no user is logged in, description is generally refused.
		- If the user has "root" or "admin", description is generally allowed.

		It should be overridden for a module-specific behavior.

		.. seealso:: :func:`desc`

		:param skel: This is the name of the skeleton retrival function to be called for.
		:type skel: str

		:returns: True, if viewing the data model is allowed, False otherwise.
		:rtype: bool
		"""
		if not( skel == "_resolveSkelCls" or skel.endswith("Skel")):
			return False

		cuser = utils.getCurrentUser()
		return bool(cuser and ("root" in cuser["access"] or "admin" in cuser["access"]))

	@exposed
	def desc(self, skel = "_resolveSkelCls", subSkel = None, *args, **kwargs):
		"""
		Returns a description of the data model of the current module.
		By default, the _resolveSkelCls() function is triggered

		:param skel: Defines the skeleton retrival function, defaults to "viewSkel".

		:return:
		"""
		if not self.canDesc(skel):
			raise errors.Unauthorized()

		skel = getattr(self, skel)
		if skel is None or not callable(skel):
			raise errors.NotAcceptable()

		skel = skel()
		if isinstance(skel, MetaSkel):
			if subSkel:
				if subSkel not in skel.subSkels.keys():
					raise errors.NotAcceptable()

				skel = skel.subSkel(subSkel)
			else:
				skel = skel()

		if not isinstance(skel, Skeleton):
			raise errors.NotAcceptable()

		return self.render.desc(skel)
