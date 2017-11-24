#-*- coding: utf-8 -*-

class ListWrapper( list ):
	"""
		Monkey-Patching for lists.
		Allows collecting sub-properties by using []
		Example: [ {"key":"1"}, {"key":"2"} ]["key"] --> ["1","2"]
	"""
	def __init__( self, src ):
		"""
			Initializes this wrapper by copying the values from src
		"""
		super(ListWrapper, self).__init__()
		self.extend( src )

	def __getitem__( self, key ):
		if isinstance( key, int ):
			return( super( ListWrapper, self ).__getitem__( key ) )
		res = []
		for obj in self:
			if isinstance( obj, dict ) and key in obj:
				res.append( obj[ key ] )
			elif key in dir( obj ):
				res.append( getattr( obj, key ) )
		return( ListWrapper(res) )

class SkelListWrapper(ListWrapper):
	"""
		Like ListWrapper, but takes the additional properties
		of skellist into account - namely cursor and customQueryInfo.
	"""
	def __init__( self, src, origQuery=None ):
		super( SkelListWrapper, self ).__init__( src )
		if origQuery is not None:
			self.cursor = origQuery.cursor
			self.customQueryInfo = origQuery.customQueryInfo
		else:
			self.cursor = src.cursor
			self.customQueryInfo = src.customQueryInfo



class ThinWrapper(object):
	def __init__(self, skel, valuesCache, render):
		"""
			@param baseSkel: The baseclass for all entries in this list
		"""
		super(ThinWrapper, self).__init__()
		self.skel = skel
		self.valuesCache = valuesCache
		self.render = render
		self.cache = {}

	def __contains__(self, item):
		return item in self.skel

	def __getattr__(self, item):
		if item not in self.cache:
			if item not in self.skel:
				self.cache[item] = None
				return None
			self.skel.setValuesCache(self.valuesCache)
			val = self.render.renderBoneValue(getattr(self.skel, item), self.skel, item)
			self.cache[item] = val
			return val
		return self.cache[item]

	def __getitem__(self, item):
		return self.__getattr__(item)

	def keys(self):
		return self.skel.keys()
