# -*- coding: utf-8 -*-
class baseRender(object):
	renderType = renderMaintype = None

	def renderBoneStructure( self, bone ):
		"""
		Renders the structure of a bone.

		This function is used by :func:`renderSkelStructure`.
		can be overridden and super-called from a custom renderer.

		:param bone: The bone which structure should be rendered.
		:type bone: Any bone that inherits from :class:`server.bones.base.baseBone`.

		:return: A dict containing the rendered attributes.
		:rtype: dict
		"""

		if self.renderType and self.renderType + "_renderBoneStructure" in dir( bone ):
			return getattr( bone, self.renderType + "_renderBoneStructure" )( self )

		return bone.renderBoneStructure( self )

	def renderBoneValue(self, bone, skel, key):
		"""
		Renders the value of a bone.

		This function is used by :func:`collectSkelData`.
		It can be overridden and super-called from a custom renderer.

		:param bone: The bone which value should be rendered.
		:type bone: Any bone that inherits from :class:`server.bones.base.baseBone`.

		:return: A dict containing the rendered attributes.
		:rtype: dict
		"""

		if self.renderType and self.renderType + "_renderBoneValue" in dir( bone ):
			return getattr( bone, self.renderType + "_renderBoneValue" )( self )

		return bone.renderBoneValue( skel, key, self )