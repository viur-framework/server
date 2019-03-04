from server.render import html
from server.render import admin
from server.render import xml
from server.render import json

try:
	# The VI-Render will only be available if the "vi" folder is present
	from server.render import vi
except ImportError:
	import logging
	logging.error("VI NOT AVAIABLE")
	pass
