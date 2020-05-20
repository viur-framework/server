# -*- coding: utf-8 -*-
import json
from datetime import datetime
from hashlib import sha256

from server import db


class IndexMannager:
	"""
		Allows efficient pagination for a small specified set of queries.
		This works *only* if the number of different querys is limited.
		Otherwise use the built-in page parameter for small result-sets and few pages.
		If you have lots of different querys and large result-sets you can only generate next/previous links on the fly.

		.. Note::

			The refreshAll Method is missing - intentionally. Whenever data changes you have to call
			refreshIndex for each affected Index. As long as you can name them, their number is
			limited and everything is fine :)

	"""

	_dbType = "viur_indexes"

	def __init__(self, pageSize=10, maxPages=100):
		"""
		:param pageSize: How many items per page
		:type pageSize: int
		:param maxPages: How many pages are build. Items become unreachable if the amount of items
			exceed pageSize*maxPages (ie. if a forum-thread has more than pageSize*maxPages Posts, Posts
			after that barrier won't show up).
		:type maxPages: int
		"""
		self.pageSize = pageSize
		self.maxPages = maxPages
		self._cache = {}

	def keyFromQuery(self, query):
		"""
			Derives a unique Database-Key from a given query.
			This Key is stable regardless in which order the filter have been applied

			:param query: Query to derive key from
			:type query: DB.Query
			:returns: str
		"""

		assert isinstance(query, db.Query)
		origFilter = [(x, y) for x, y in query.getFilter().items()]
		for k, v in query.getOrders():
			origFilter.append(("__%s =" % k, v))
		if query.amount:
			origFilter.append(("__pagesize =", self.pageSize))
		origFilter.sort(key=lambda sx: sx[0])
		filterKey = "".join([u"{0}{1}".format(x, y).encode("utf-8") for x, y in origFilter])
		return sha256(filterKey).hexdigest()

	def getOrBuildIndex(self, origQuery):
		"""
			Builds a specific index based on origQuery AND local variables (self.indexPage and self.indexMaxPage)
			Returns a list of starting-cursors for each page.
			You probably shouldn't call this directly. Use cursorForQuery.

			:param origQuery: Query to build the index for
			:type origQuery: db.Query
			:returns: []
		"""
		key = self.keyFromQuery(origQuery)
		if key in self._cache:  # We have it cached
			return self._cache[key]
		# We don't have it cached - try to load it from DB
		try:
			index = db.Get(db.Key.from_path(self._dbType, key))
			res = json.loads(index["data"])
			self._cache[key] = res
			return res
		except db.EntityNotFoundError:  # Its not in the datastore, too
			pass
		# We don't have this index yet.. Build it
		# Clone the original Query
		queryRes = origQuery.clone(keysOnly=True).datastoreQuery.Run(limit=self.maxPages * self.pageSize)
		# Build-Up the index
		res = list()
		previousCursor = None  # The first page dosnt have any cursor

		# enumerate is slightly faster than a manual loop counter
		for counter, discardedKey in enumerate(queryRes):
			if counter % self.pageSize == 0:
				res.append(previousCursor)
			if counter % self.pageSize == (self.pageSize - 1):
				previousCursor = str(queryRes.cursor().urlsafe())

		if not len(res):  # Ensure that the first page exists
			res.append(None)

		entry = db.Entity(self._dbType, name=key)
		entry["data"] = json.dumps(res)
		entry["creationdate"] = datetime.now()
		db.Put(entry)
		return res

	def cursorForQuery(self, query, page):
		"""Returns the starting-cursor for the given query and page using an index.

			.. WARNING:

				Make sure the maximum count of different querys are limited!
				If an attacker can choose the query freely, he can consume a lot
				datastore quota per request!

			:param query: Query to get the cursor for
			:type query: db.Query
			:param page: Page the user wants to retrieve
			:type page: int
			:returns: Cursor (type: str) or None if no cursor is applicable
		"""
		page = int(page)
		pages = self.getOrBuildIndex(query)
		if 0 < page < len(pages):
			return db.Cursor(urlsafe=pages[page])
		else:
			return None

	def getPages(self, query):
		"""
			Returns a list of all starting-cursors for this query.
			The first element is always None as the first page doesn't
			have any start-cursor
		"""
		return self.getOrBuildIndex(query)

	def refreshIndex(self, query):
		"""
			Refreshes the Index for the given query
			(Actually it removes it from the db so it gets rebuild on next use)

			:param query: Query for which the index should be refreshed
			:type query: db.Query
		"""
		key = self.keyFromQuery(query)
		try:
			db.Delete(db.Key.from_path(self._dbType, key))
		except db.EntityNotFoundError:
			pass

		# try/except is faster than if clause
		try:
			del self._cache[key]
		except:
			pass
