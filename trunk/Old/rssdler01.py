#!/usr/bin/python
# RSSDler - RSS Broadcatcher
# Copyright (C) 2007, lostnihilist
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; under version 2 of the license.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Contact:  lostnihilist <lostnihilist@gmail.com>

import feedparser, mechanize
from BitTorrent.bencode import bdecode
import time, os, socket, cgi, codecs, re, urllib, cookielib, mimetools, mimetypes
import pickle, copy, getopt, sys, ConfigParser
from UserDict import UserDict

# # # # #
# == Globals ==
# # # # #
_VERSION = "0.1"
USER_AGENT = "RSSDler %s" % _VERSION
_configInstance = None
_sharedData = None
action = None
runOnce = None
configFile = 'config.txt'
cj = None
UMASK = 0077
MAXFD = 1024
utfWriter = codecs.getwriter( "utf-8" )
sys.stdout = utfWriter( sys.stdout, "replace" )

helpMessage="""Command Line Options:
	--run/-r: run according to the configuration file
	--runonce/-o: run only once (overrides configuration file, if set to run forever)
	--daemon/-d: run in the background, according to the configuration file (Unix-like only)
	--kill/-k: kill the daemonized instance (Unix like only)
	--config/-c specify a config file (default config.txt).

Non-standard Python libraries used:
	mechanize: http://wwwsearch.sourceforge.net/mechanize/
	feedparser: http://www.feedparser.org/
	BitTorrent: http://www.bittorrent.com (the python reference client)
	For debian based distros: "sudo apt-get install python-feedparser python-mechanize bittorrent"
	
Security Note: There are several 'eval' statements in this program, which will allow running arbitrary code. Make sure only you have write permissions in the directory you run this from/what you set workingDir to. Also make sure only you have write permissions to your configuration file. This should be sufficient protection.

Configuration File:
	There are two types of sections: global and threads. There can be as many thread sections as you wish, but only one global section. global must be named "global." Threads can be named however you wish, except 'global,' and each name should be unique. First the format:
	
	[global]
	option = argument
	option2 = argument
	[feed1]
	option3 = argument
	....
	[feed2]
	....
	
Boolean Options: 'True' is indicated by "True", "yes", or "1". "False" is indicated by "False", "no", or "0" (without the quotes)
Integer Options: Just an integer. 1, 2, 10, 1000, 2348. Not 1.1, 2.0, 999.3 or 'a'.
String Options: any string, should make sense in terms of the option being provided (e.g. a valid file/directory on disk; url to rss feed)

Global Options:
	verbose: A boolean option, defaulting to True. Set to False to disable verbose output.
	downloadDir: A string option, Default is current directory. Set to a directory in which you have write permission where downloaded files will go.
	runOnce: A boolean option, default False. Set to True to force rssdler to exit after it has scanned the configured feeds.
	minSize: An integer option. Default None. Specify, in MB, the minimum size for a download to be. Files less than this size will not be saved to disk.
	maxSize: An integer option. Default None. Specify, in MB, the maximum size for a download to be. Files greater than this size will not be saved to disk.
	log: A boolean option. Default False. Will write to a log file (specified by logFile)
	logFile: A string option. Default downloads.log. Specify a file on disk to write the log to.
	saveFile: A string option. Default savedstate.dat. Specify a file on disk to write the saved state information to. This keeps track of previously downloaded files and other 'state' information necessary to keep the program running coherently, especially between shutdown/startup
	scanMins: An integer option. Default 15. Minimum 10. Values are in minutes. The number of minutes between scans. If a feed uses the <ttl> tag, it will be respected. That is, if you have scanMins set to 10 and the site sets <ttl>900</ttl> (900 seconds; 15 mins); then the feed will be scanned every other time. 
	lockPort: An integer option. Default 8023. The port on which the savedstate.dat file will be locked for writing. Necessary to maintain the integrity of the state information.
	cookieFile: A string option. Default 'cookies.txt'. The file on disk, in Netscape Format (requires headers) that has cookie information for whatever site(s) you have set that require it.
	workingDir: A string option. Default is current directory. Only needed with -d. Set to a directory on disk. Useful to make sure you don't run this from a partition that might get unmounted. If you use the -d switch (to run as a deamon) you must have this set or the program will die.
	daemonInfo: A string option. Default daemon.info. Only needed with -d. Set to a file on disk. Daemon info will be written there so that -k and such will work. (full path over rides workingDir) 
	rss: A python "dictionary" object. Default None. Setting this option properly (that's easy) allows you to create your own rss feed of the objects you have downloaded. It's a basic feed, likely to not include links to the original files. The keys are (all are required):
		length: An integer. How many entries should the RSS feed store before it starts dropping old items. 0 would literally mean to store no items
		title: A string. The title the rss feed will carry.
		link: A string: Where the rss feed can be located. Typically an http link.
		description: A string. A short description of what the feed contains.
		filename: A string. Where to store the feed on disk.
		Example (Note the ' around every 'string' except 20, which needs to be an integer. Only place in the config where quotes of strings are necessary.):
			rss = {'length': 20, 'title': 'Recent Downloads', 'link': 'http://example.com/downloads.xml', 'description': 'Files that have recently been downloaded automatically', 'filename': '/var/www/downloads.xml'}
			
Thread options:
	link: A string option. Link to the rss feed.
	active: A boolean option. Default is True, set to False to disable checking of that feed.
	maxSize: An integer option, in MB. default is None. A thread based maxSize like in global. If set to None, will default to global's maxSize. Other values override global, including 0 to indicate no maxSize.
	minSize: An integer opton, in MB. default is None. A thread based minSize, like in global. If set to None, will default to global's minSize. Other values override global, including 0 to indicate no minSize.
	noSave: A boolean option. Default to False. If true, will remember download objects for the save processor on first run, but does not download.
	directory: A string option. Default to None. If set, overrides global's downloadDir, directory to download download objects to.
	checkTime: A sequence of tuples of three integers. Specifies scan time. Will only scan thread during the time period specified. defaults to None, which means always. 0-6 : Monday-Sunday:: 0-23 : time. Give tuples in a sequence, specified with (), of day; start time, end time.put those in a sequence, specified with [].
		e.g.: check thread only on monday from 5p to 10p: [(0, 17, 22)]
		e.g.: check thread on wednesday from 10p to 11:59p and thursday from 12a to 3a: [(2,22,23),(3,0,3)]
	regExTrue: A string (regex) option. Default None. If specified, will only download if a regex search of the download name (title key in entry dictionary of feedparser instance) returns True. This will be converted to a python regex object. Use all lower case, as the name is converted to all lower case.
	regExTrueOptions: A string option. Default None. Options (like re.IGNORECASE) to go along with regExTrue when compiling the regex object. IGNORECASE is unnecessary however.
	regExFalse: A string (regex) option. Default None. If specified, will only download if a regex search of the download name returns False. This will be converted to a python regex object. Use all lower case, as the name is converted to all lower case.
	regExFalseOptions: A string option. Default None. Options (like re.IGNORECASE) to go along with regExFalse when compiling the regex object
	postDownloadFunction: A string option. Default None. The name of a function, stored in userFunctions.py found in the current working directory (with -d, workingDir, otherwise the directory the program is started from). Must accept the following arguments (of course they can be ignored): directory the file was stored in, the filename, and the feedparser entry for that object.
	"""
		
# # # # #
#Exceptions
# # # # #
class Fatal( Exception ): 
	"""An unrecoverable error occurred, the user will need to take some action before retrying."""
	
class Warning( Exception ):
	"""An error occurred, but no action needs to be taken by the user at this time."""
	
class Locked( Exception ):
	"""An attempt was made to lock() the savefile while it was already locked."""

# # # # #
#HTML/XML/HTTP
# # # # #
def mechRetrievePage(url=None, txdata=None, txheaders=[('User-agent', USER_AGENT)], file='', pageForm='' ):
	"""txdata are either 
			1) sequence of tuples of data to be encoded into a POST request in a raw form
			2) a dictionary, length 1, key being the name of the form we want to fill, the value being like 1);
				must supply a response object to pageForm with that name, or the data will not be transmitted
		txheaders: sequence of tuples of header key, value to manually add to the request object
		files: a file location to add to form response this is untested; submitting a file without a formname in txdata
			assumes the last form on the page is the form you want to fill
		pageForm: a response object containing the page with the form we want to fill in. url argument is ignored, the page will be "clicked'
			depending on which form you tell us to click on
	"""
	global cj, opener, config
	if not cj:
		cj = mechanize.MozillaCookieJar()
		cj.load(getConfig(filename=configFile)['global']['cookieFile'])
		opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cj), mechanize.HTTPRefreshProcessor(), mechanize.HTTPRedirectHandler(), mechanize.HTTPEquivProcessor())
		mechanize.install_opener(opener)
	if pageForm:
		forms = ClientForm.ParseResponse(pageForm, backwards_compat=False)
		if type(txdata) == type({}):
			formName = txdata.keys()[0]
			txdata = txdata[formName]
			for formTry in forms:
				if formTry.name == formName:	form = formTry
		else: form = forms[-1]
		if file: form.add_file(open(file))
		if txdata:
			for formElem in txdata:
				form[formElem[0]] = formElem[1]
		request = form.click()
		if txheaders:
			for header in txheaders: request.add_header(header[0], header[1])
	elif txdata: 
		txdata = urllib.urlencode(txdata)
		if txheaders: 
			request = mechanize.Request( url, txdata )
			for header in txheaders: request.add_header(header[0], header[1])
	else:
		request = mechanize.Request( url )
		if txheaders:
			for header in txheaders: request.add_header(header[0], header[1])
	response = mechanize.urlopen( request )
	return response

def getFileSize( info, data=None ):
	"""give me the HTTP headers (info) and, if you expect it to be a torrent file, the actual file, i'll return the filesize, of type None if not determined"""
	size = None
	if re.search("torrent", info['content-type']):
		tparse = bdecode(data)
		try: size = int(tparse['info']['length'])
		except:
			try:
				size = int(0)
				for j in tparse['info']['files']:
					size += int(j['length'])
			except: 
				size = None
	else:
		try: size = int(info['content-length'])
		except:	pass
	return size

def getFilenameFromHTTP(info, url):
	"""info is an http header from the download, url is the url to the downloaded file (responseObject.geturl() )"""
	try: filename = re.findall("filename=\"(.*)\"", info['content-disposition'])[0]
	except: 
		filename = re.findall(".*/(.*)", url )[0]
		try: filename = urllib.unquote(filename)
		except: pass
	typeGuess = mimetypes.guess_type(filename)[0]
	if typeGuess in info['content-type']: pass
	else:
		try: filename += mimetypes.guess_extenstion(re.findall("(.*);", info['content-type'])[0])
		except: status("Proper file extension could not be determined for the downloaded file: %s you may need to add an extension to the file for it to work in some programs." % filename )
	return filename

def downloadFile(url, threadName, rssItemNode):
	try: data = mechRetrievePage(url)
	except: 
		return False
	dataPage = data.read()
	dataInfo = data.info()
	# could try to grab filename from ppage item title attribute, but this seems safer for file extension assurance
	filename = getFilenameFromHTTP(dataInfo, data.geturl())
	size = getFileSize(dataInfo, dataPage)
	# check size against configuration options
	if size:
		if getConfig(filename=configFile)['threads'][threadName]['maxSize'] != None: maxSize = getConfig(filename=configFile)['threads'][threadName]['maxSize']
		elif getConfig(filename=configFile)['global']['maxSize'] != None: maxSize = getConfig(filename=configFile)['global']['maxSize']
		else: maxSize = None
		if getConfig(filename=configFile)['threads'][threadName]['minSize'] != None: minSize = getConfig(filename=configFile)['threads'][threadName]['minSize']
		elif getConfig(filename=configFile)['global']['minSize'] != None: minSize = getConfig(filename=configFile)['global']['minSize']
		else: minSize = None
		if maxSize:
			maxSize = maxSize * 1024 * 1024
			if size > maxSize: 
				return True
		if minSize:
			minSize = minSize * 1024 * 1024
			if size <  minSize:
				return True
	filename = str(filename)
	filename = unicode( filename, "utf-8", "replace" )
	if getConfig(filename=configFile)['threads'][threadName]['directory']: directory = getConfig(filename=configFile)['threads'][threadName]['directory']
	else: directory = getConfig(filename=configFile)['global']['downloadDir']
	outfile = open( os.path.join(directory,  filename), "wb" )
	outfile.write( dataPage )
	outfile.close()
	if	getConfig(filename=configFile)['global']['log']:
		try: oldLog = open(getConfig(filename=configFile)['global']['logFile'], 'r').read()
		except: oldLog = ''
		timeCode = "[%4d%02d%02d.%02d:%02d]" % time.localtime()[:5]
		oldLog += "%s%s" % (timeCode, os.linesep)
		oldLog += "\tFilename: %s%s" % (filename, os.linesep)
		oldLog += "\tDirectory: %s%s" % (directory, os.linesep)
		oldLog += "\tFrom Thread: %s%s" % (threadName, os.linesep)
		open(getConfig(filename=configFile)['global']['logFile'], 'w').write(oldLog)
	if rss:
		if rssItemNode.has_key('description'): description = rssItemNode['description']
		else: description = None
		if rssItemNode.has_key('title'): title = rssItemNode['title']
		else: title = None
		pubdate = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
		itemLoad = {'title':title , 'description':description , 'pubDate':pubdate }
		rss.makeItemNode( itemAttr=itemLoad )
	if getConfig(filename=configFile)['threads'][threadName]['postDownloadFunction']:
		try: eval("""userFunctions.%s("%s", "%s", %s)""" % (getConfig(filename=configFile)['threads'][threadName]['postDownloadFunction'], directory, filename, rssItemNode))
		except: pass
	status( "   * saved to file: %s" % filename)
	return True
	
	
def rssparse(thread, threadName):
	"""Give me a ThreadLink object, including an rss url to a thread, I'll 
	give you back an updated ThreadLink object, and download the appropriate torrents
	based on the configuration.
	assumes feed parser will create the following attributes:
		['entries'][x]['link']
		['entries'][x]['title']
	"""
	#['link']
	ThreadLink = copy.deepcopy(thread)
	try: page = mechRetrievePage(ThreadLink['link'])
	except:	return ThreadLink
	ppage = feedparser.parse(page.read())
	if ppage['feed'].has_key('ttl') and ppage['feed']['ttl'] != '':
		saved.minScanTime[threadName] = (time.time(), int(ppage['feed']['ttl']) )
	for i in range(len(ppage['entries'])):
		#if we have downloaded before, just skip (but what about e.g. multiple rips of about same size/type we might download multiple times)
		if ppage['entries'][i]['link'] in saved.downloads: 
			continue
		# make sure it matches what we want
		if ThreadLink['regExTrue']:
			if ThreadLink['regExTrueOptions']: regExSearch = re.compile(ThreadLink['regExTrue'], eval(ThreadLink['regExTrueOptions']))
			else: regExSearch = re.compile(ThreadLink['regExTrue'])
			if not regExSearch.search(ppage['entries'][i]['title'].lower()):
				continue
		# make sure it doesn't match what we don't want
		if ThreadLink['regExFalse']:
			if ThreadLink['regExFalseOptions']: regExSearch = re.compile(ThreadLink['regExFalse'], eval(ThreadLink['regExFalseOptions']))
			else: regExSearch = re.compile(ThreadLink['regExFalse'])
			if regExSearch.search(ppage['entries'][i]['title'].lower()):
				continue
		# if we matched above, but don't want to download, register as downloaded, and then move on
		if ThreadLink['noSave']:  
			saved.downloads.append(ppage['entries'][i]['link'] )
			continue
		#nonglobaldata: ppage, 
		#make this an if/then
		if downloadFile(ppage['entries'][i]['link'], threadName, ppage['entries'][i]):
			saved.downloads.append( ppage['entries'][i]['link'] )
		else:
			saved.failedDown.append( (ppage['entries'][i]['link'], threadName, ppage['entries'][i]) )
		ThreadLink['nosave'] = False
	return ThreadLink

# # # # #
#Persistence
# # # # #
class makeRss:
	"""returns an xml document (approximately?) in line with the rss2.0 specification
	Give me a channelMeta dictionary with keys in chanMetOpt list
	goes into a dictionary, called channelMeta, that is accessed with keys being the xml element (e.g. "language" in <language>)
	and values being the text for the node. It is up to you to provide legitimate text values
	"""
	def __init__(self, channelMeta={}, load=True):
		global PrettyPrint, minidom
		try:
			if minidom: pass
		except: from xml.dom import minidom
		try:
			if PrettyPrint: pass
		except: from xml.dom.ext import PrettyPrint
		self.chanMetOpt = ['title', 'description', 'link', 'language', 'copyright', 'managingEditor', 'webMaster', 'pubDate', 'lastBuildDate', 'category', 'generator', 'docs', 'cloud', 'ttl', 'image', 'rating', 'textInput', 'skipHours', 'skipDays']
		self.itemMeta = ['title', 'link', 'description', 'author', 'category', 'comments', 'enclosure', 'guid', 'pubDate', 'source']
		self.feed = minidom.Document()
		self.rss = self.feed.createElement('rss')
		self.rss.setAttribute('version', '2.0')
		self.channel = self.feed.createElement('channel')
		self.channelMeta = channelMeta
		self.items = []
		if load == True: self.loadChanOpt()

	def loadChanOpt(self):
		keys = self.channelMeta.keys()
		if 'title' not in keys or 'description' not in keys or 'link' not in keys:
			raise Exception, "channelMeta must specify at least 'title', 'description', and 'link' according to RSS2.0 spec. these are case sensitive"
		for key, value in self.channelMeta.iteritems():
			if key in self.chanMetOpt:
				chanMet = self.makeTextNode(key, value)
				self.channel.appendChild(chanMet)
	
	def makeTextNode(self, nodeName, nodeText, nodeAttributes=[]):
		"""returns an xml text element node, with input being the name of the node, text, and optionally node attributes as a sequence
		of tuple pairs (attributeName, attributeValue)
		"""
		node = self.feed.createElement(nodeName)
		text = self.feed.createTextNode(nodeText)
		node.appendChild(text)
		if nodeAttributes:
			for attribute, value in nodeAttributes: 
				node.setAttribute(attribute, value)
		return node

	def makeItemNode(self, itemAttr={}):
		"""should have an item "child" we will be adding to that"""
		if 'title' in itemAttr.keys() or 'link' in itemAttr.keys(): pass
		else:	raise Exception, "must provide at least a title OR link for each item"
		item = self.feed.createElement('item')
		for key in self.itemMeta:
			if itemAttr.has_key(key):
				itemNode = self.makeTextNode(key, itemAttr[key])
				item.appendChild(itemNode)
		self.items.append(item)
	
	def appendItemNodes(self, pop=False):
		"""adds the items in self.items to self.channel. if pop is True, each item is removed as it is added to channel. starts at the front of the list"""
		if pop:
			while self.items: self.channel.appendChild( self.items.pop(0) )
		else:
			for item in self.items: self.channel.appendChild( item )
	
	def closeFeed(self):
		self.rss.appendChild(self.channel)
		self.feed.appendChild(self.rss)
	
	def parse(self, rawfeed=None, parsedfeed=None):
		"""give parse a raw feed (just the xml/rss file, unparsed) and it will fill in the class attributes, and allow you to modify the feed.
		Or give me a feedparser.parsed feed (parsedfeed) and I'll do the same"""
		global feedparser, time
		try:
			if time: pass
		except: import time
		try:
			if feedparser: pass
		except: import feedparser
		if rawfeed:	p = feedparser.parse(rawfeed)
		elif parsedfeed: p = parsedfeed
		else: raise Exception, "Must give either a rawfeed or parsedfeed"
		# try to make feedparser have the same dictionary items as rss item list (i.e. valid tags for RSS2.0)
		# pubdate turns into updated_parsed / updated
		if p['feed'].has_key('updated'): p['feed']['pubDate'] = p['feed']['pubdate']  = p['feed']['updated']
		elif p['feed'].has_key('updated_parsed'): 
			p['feed']['pubDate'] = p['feed']['pubdate']  = time.strftime("%a, %d %b %Y %H:%M:%S GMT", p['feed']['updated_parsed'])
		for entry in p['entries']:
			if entry.has_key('updated'): entry['pubDate'] = entry['pubdate'] = entry['updated']
			elif entry.has_key('updated_parsed'): 
				entry['pubDate'] = entry['pubdate'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", entry['updated_parsed'])
			# source, comments don't have a feed (offhand) that has these entries in them, as far as I can tell., that's ok
		for key in self.chanMetOpt:
			# annoyingly, feedparser presents the dictionary with all lower case instead of the standard camelCase.
			if p['feed'].has_key(key.lower()):
				#if key = image, we need to parse this more smartly, this will NOT work
				self.channel.appendChild(self.makeTextNode(key, p['feed'][key.lower()]))
		for entry in p['entries']:	self.makeItemNode(entry)
		
	def write(self, filename=None, file=None):
		"""if fed filename, will write and close self.feed to file at filename.
		if fed file, will write to file, but closing it is up to you"""
		global PrettyPrint
		try:
			if PrettyPrint: pass
		except: from xml.dom.ext import PrettyPrint
		if filename:
			outfile = open(filename, 'w')
			PrettyPrint(self.feed, outfile)
			outfile.close()
		if file:
			PrettyPrint(self.feed, file)

class GlobalOptions(UserDict):
	"""Represents the options for running the program as a dictionary. See helpMessage for appropriate defaults"""
	def __init__(self, verbose=True, downloadDir=os.getcwd(), runOnce=False, minSize=None, maxSize=None, log=False, logFile='downloads.log', saveFile='savedstate.dat', scanMins=15, lockPort=8023, cookieFile='cookies.txt', workingDir=os.getcwd(), daemonInfo = 'daemon.info', rss=None):
		UserDict.__init__(self)
		self['verbose'] = verbose
		self['downloadDir'] = downloadDir
		self['runOnce'] = runOnce
		self['minSize'] = minSize
		self['log'] = log
		self['logFile'] = logFile
		self['saveFile'] = saveFile
		self['scanMins'] = scanMins
		self['lockPort'] = lockPort
		self['cookieFile'] = cookieFile
		self['workingDir'] = workingDir
		self['daemonInfo'] = daemonInfo
		self['rss'] = rss
class ThreadLink(UserDict):
	"""Represents a link to an rss thread and related content. 
	Attributes:
		link: Link to the rss feed. This is the primary tool used to categorize, access threads
		active: default is True, set to False to disable thread checking
		maxSize: default is None, initializer sets to site max
		minSize: default is None, initializer sets to site min
		noSave: remember download objects for the save processor on first run, but do not download
			defaults to False
		directory: directory to download download objects to, default to None, initializer sets to site default
		checkTime: Specifies scan time. Will only scan thread during the time period specified. defaults to None, which means always. 0-6 : Monday-Sunday:: 0-23 : time. Give tuples in a sequence, specified with (), of day; start time, end time.put those in a sequence, specified with [].
			e.g.: check thread only on monday from 5p to 10p: [(0, 17, 22)]
			e.g.: check thread on wednesday from 10p to 11:59p and thursday from 12a to 3a: [(2,22,23),(3,0,3)]
		regExTrue: if specified, will only download if a regex search of the download name returns true. This will be converted to a python regex object
		regExTrueOptions: options (like re.IGNORECASE) to go along with regExTrue when compiling the regex object
		regExFalse: if specified, will only download if a regex search of the download name returns false. This will be converted to a python regex object
		regExFalseOptions: options (like re.IGNORECASE) to go along with regExFalse when compiling the regex object
		postDownloadFunction: the name of a function, stored in userFunctions.py in the installation to be called after download
		
	"""
	def __init__(self, name=None, link=None, active=True, maxSize=None, minSize=None, noSave=False, directory=None, checkTime=None, regExTrue=None, regExTrueOptions=None, regExFalse=None, regExFalseOptions=None, postDownloadFunction=None):
		UserDict.__init__(self)
		self['link'] = link
		self['active'] = active
		self['maxSize'] = maxSize
		self['minSize'] = minSize
		self['noSave'] = noSave
		self['directory'] = directory
		self['checkTime'] = checkTime
		self['regExTrue'] = regExTrue
		self['regExTrueOptions'] = regExTrueOptions
		self['regExFalse'] = regExFalse
		self['regExFalseOptions'] = regExFalseOptions
		self['postDownloadFunction'] = postDownloadFunction

class saveInfo(UserDict):
	def __init__(self, lastChecked=0, downloads=[]):
		UserDict.__init__(self)
		self['lastChecked'] = lastChecked
		self['downloads'] = downloads
		self['minScanTime'] = {}
		self['failedDown'] = []

class saveProcessor:
	def __init__(self, saveFileName="savedstate.dat"):
		"""saveFileName: location where we store persistence data
		lastChecked: seconds since epoch when we last checked the threads
		downloads: a list of download links, so that we do not repeat ourselves
		minScanTime: a dictionary, keyed by rss link aka thread name, with values of tuples (x,y) where x=last scan time for that thread,
			y=min scan time in minutes, only set if ttl is set in rss feed, otherwise respect checkTime and lastChecked
		failedDown: a list of tuples (threadname, link to download). This means that the regex, at the time of parsing, identified this file as worthy of downloading, but there was some failure in the retrieval process. Size will be checked against the configuration state at the time of the redownload attempt, not the size configuration at the time of the initial download attempt (if there is a difference)
		"""
		self.saveFileName = saveFileName
		self.lastChecked = 0
		self.downloads = []
		self.failedDown = []
		self.minScanTime = {}
		self.lockSock = None
	def save(self):
		saveFile = saveInfo()
		saveFile['lastChecked'] = self.lastChecked
		saveFile['downloads'] = self.downloads
		saveFile['minScanTime'] = self.minScanTime
		saveFile['failedDown'] = self.failedDown
		f = open(self.saveFileName, 'wb')
		pickle.dump(saveFile, f, -1)
	def load(self):
		f = open(self.saveFileName, 'rb')
		saveFile = pickle.load(f)
		self.lastChecked = saveFile['lastChecked']
		self.downloads = saveFile['downloads']
		self.minScanTime = saveFile['minScanTime']
		self.failedDown = saveFile['failedDown']
		del saveFile
	def lock( self ):
		"""Portable locking mechanism. Binds to 'lockPort' as defined in config on
		127.0.0.1.
		Raises btrsslib.Locked if a lock already exists.
		"""
		if self.lockSock:
			raise Locked
		try:
			self.lockSock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			self.lockSock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
			self.lockSock.bind( ('127.0.0.1', getConfig(filename=configFile)['global']['lockPort']) )
		except socket.error:
			raise Locked
	def unlock( self ):
		"""Remove an existing lock()."""
		try: self.lockSock.close()
		except socket.error: pass

def getConfig(reload=False, filename='config.txt'):
	"""Return a shared instance of the Config class (creating one if neccessary)"""
	global _configInstance
	if reload: _configInstance = None
	if not _configInstance:
		_configInstance = Config(filename)
	return _configInstance

class Config(ConfigParser.RawConfigParser, UserDict):
	def __init__(self, filename='config.txt'):
		"""
		see helpMessage
		"""
		ConfigParser.RawConfigParser.__init__(self)
		UserDict.__init__(self)
		self.read(filename)
		self['filename'] = filename
		self['global'] = GlobalOptions()
		self['threads'] = {}
		self.parse()
		self.check()
	def parse(self):
		boolOptionsGlobal = ['verbose', 'runOnce', 'log', 'active']
		boolOptionsThread = ['active', 'noSave']
		stringOptionsGlobal = ['downloadDir', 'saveFile', 'cookieFile', 'logFile', 'workingDir', 'daemonInfo']
		stringOptionsThread = ['link', 'directory', 'postDownloadFunction', 'regExTrue', 'regExTrueOptions', 'regExFalse', 'regExFalseOptions']	
		intOptionsGlobal = ['maxSize', 'minSize', 'lockPort', 'scanMins']
		intOptionsThread = ['maxSize', 'minSize']
		for option in boolOptionsGlobal:
			if option.lower() in self.options('global'): 
				try: self['global'][option] = self.getboolean('global', option)
				except: pass
				# now set by GlobalOptions()
				#except: self['global'][option] = None
		for option in stringOptionsGlobal:
			if option.lower() in self.options('global'):
				self['global'][option] = self.get('global', option)
				if self['global'][option] == '' or self['global'][option].lower() == 'none' : self['global'][option] = None
		for option in intOptionsGlobal:
			if option.lower() in self.options('global'):
				try: self['global'][option] = self.getint('global', option)
				except: pass
		if 'rss' in self.options('global'):
			try:
				rss = eval(self.get('global', 'rss') )
				if type(rss) == type( {} ): self['global']['rss'] = rss
			except: pass
		threads = self.sections()
		del threads[threads.index('global')]
		for thread in threads:
			#maybe make UserDict object here instead, so that they don't have to specify non-default values....yes, let's do that
			self['threads'][thread] = ThreadLink()
			for option in boolOptionsThread:
				if option.lower() in self.options(thread):
					try: self['threads'][thread][option] = self.getboolean(thread, option)
					except: pass
					#this is not necessary, because we set our defaults with ThreadLink()
					#except: self['threads'][thread][option] = None
			for option in stringOptionsThread:
				if option.lower() in self.options(thread):
					self['threads'][thread][option] = self.get(thread, option)
					if self['threads'][thread][option] == '' or self['threads'][thread][option].lower() == 'none': self['threads'][thread][option] = None
			for option in intOptionsThread:
				if option.lower() in self.options(thread):
					try: self['threads'][thread][option] = self.getint(thread, option)
					except: pass
					# defaults set by ThreadLink()
					#except: self['threads'][thread][option] = None
			try: 
				if 'checkTime'.lower() in self.options(thread):
					checktimepy = eval(self.get(thread, 'checkTime'))
					if type(checktimepy) == type([]) and type(checktimepy[0]) == type( () ):
						self['threads'][thread]['checkTime'] = checktimepy
			except: pass
	def check(self):
		if not self['global'].has_key('saveFile') or self['global']['saveFile'] == None:
			self['global']['saveFile'] = 'savedstate.dat'
		if not self['global'].has_key('downloadDir') or self['global']['downloadDir'] == None:
			raise Exception, "Must specify downloadDir in [global] config"
		if action == 'daemon':
			if not self['global'].has_key('workingDir') or self['global']['workingDir'] == None:
				raise Exception, "Must specify workingDir in [global] config for daemon"
		if not self['global'].has_key('runOnce') or self['global']['runOnce'] == None:
			self['global']['runOnce'] = False
		if not self['global'].has_key('scanMins') or self['global']['scanMins'] == None:
			self['global']['scanMins'] = 15
		if self['global'].has_key('scanMins') and self['global']['scanMins'] < 10: self['global']['scanMins'] = 15
		if not self['global'].has_key('cookieFile') or self['global']['cookieFile'] == None or self['global']['cookieFile'] == '':
			self['global']['cookieFile'] = 'cookies.txt'
		if not self['global'].has_key('lockPort') or self['global']['lockPort'] == None:
			self['global']['lockPort'] = 8023
		if self['global'].has_key('log') and self['global']['log']:
			if not self['global'].has_key('logFile') or self['global']['logFile'] == None:
				self['global']['logFile'] = 'downloads.log'
	def save(self):
		for key, value in self['global'].iteritems():
			self.set('global', key, value)
		for thread in self['threads'].keys():
			for key, value in self['threads'][thread].iteritems():
				self.set(thread, key, value)
		fd = open(self['filename'], 'w')
		self.write(fd)
		fd.close()



# # # # #
# User/InterProcess Communication
# # # # #
class SharedData:
	"""Mechanism for sharing data. Do not instantiate directly,
	use getSharedData() instead."""
	def __init__( self ):
		self.scanning = False	# True when scan in progress
		self.scanoutput = ""	# output of last scan
		self.exitNow = False	# should exit immediatley if this is set

def getSharedData():
	"""Return a shared instance of SharedData(), creating one if neccessary."""
	global _sharedData
	if not _sharedData:
		_sharedData = SharedData()
	return _sharedData

def getVersion():
        global _VERSION
        return _VERSION

def status( message ):
	"""Log status information, writing to stdout if config 'verbose' option is set."""
	sharedData = getSharedData()
	if getConfig(filename=configFile)['global']['verbose']:
		utfWriter = codecs.getwriter( "utf-8" )
		out = utfWriter( sys.stdout, "replace" )		
		out.write( message )
		out.write( os.linesep )
		out.flush()
	sharedData.scanoutput += message + os.linesep

def killDaemon( pid ):
	while True:
		saved = saveProcessor()
		try:
			saved.lock()
			saved.unlock()
			break
		except:
			del saved
			print "Save Processor is in use, waiting for it to unlock"
			time.sleep(2)
	os.kill(pid,9)

# # # # #
#Daemon
# # # # #
def createDaemon():
	"""Detach a process from the controlling terminal and run it in the
	background as a daemon.
	"""
	try:		pid = os.fork()
	except OSError, e:
		raise Exception, "%s [%d]" % (e.strerror, e.errno)

	if (pid == 0):	# The first child.
		os.setsid()
		try:
			pid = os.fork()	# Fork a second child.
		except OSError, e:
			raise Exception, "%s [%d]" % (e.strerror, e.errno)

		if (pid == 0):	# The second child.
			 os.chdir(getConfig(filename=configFile)['global']['workingDir'])
			 os.umask(UMASK)
		else:
			# exit() or _exit()?  See below.
			 os._exit(0)	# Exit parent (the first child) of the second child.
	else:
		os._exit(0)	
	import resource		# Resource usage information.
	maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	if (maxfd == resource.RLIM_INFINITY):
		maxfd = MAXFD
   # Iterate through and close all file descriptors.
	for fd in range(0, maxfd):
		try:
			 os.close(fd)
		except OSError:	# ERROR, fd wasn't open to begin with (ignored)
			pass
	os.open(REDIRECT_TO, os.O_RDWR)	# standard input (0)
	os.dup2(0, 1)			# standard output (1)
	os.dup2(0, 2)			# standard error (2)
	return(0)

def callDaemon():
	retCode = createDaemon()
	
	# The code, as is, will create a new file in the root directory, when
	# executed with superuser privileges.  The file will contain the following
	# daemon related process parameters: return code, process ID, parent
	# process group ID, session ID, user ID, effective user ID, real group ID,
	# and the effective group ID.  Notice the relationship between the daemon's 
	# process ID, process group ID, and its parent's process ID.
	
	procParams = """
return code = %s
process ID = %s
parent process ID = %s
process group ID = %s
session ID = %s
user ID = %s
effective user ID = %s
real group ID = %s
effective group ID = %s
""" % (retCode, os.getpid(), os.getppid(), os.getpgrp(), os.getsid(0),
	os.getuid(), os.geteuid(), os.getgid(), os.getegid())
	
	try: open( os.path.join(getConfig(filename=configFile)['global']['workingDir'], getConfig(filename=configFile)['global']['daemonInfo']), 'w').write(procParams + "\n")
	except: raise Exception, "Could not write to, or not set, daemonInfo"

def signal_handler(signal, frame):
	while True:
		s = saveProcessor()
		try:
			s.lock()
			s.unlock()
			break
		except:
			del s
			status("Save Processor is in use, waiting for it to unlock")
			time.sleep(1)
	sys.exit()

# # # # #
#Running
# # # # #
def checkSleep( totalTime ):
	sharedData = getSharedData()
	steps = totalTime / 10
	for n in xrange( 0, steps ):
		time.sleep( 10 )
		if sharedData.exitNow:
			raise SystemExit

def run():
	"""Provides main functionality -- scans threads."""
	global saved, config, rss
	config = getConfig(filename=configFile, reload=True)
	saved = saveProcessor(getConfig(filename=configFile)['global']['saveFile'])
	try:
		saved.lock()
	except Locked:
		raise Warning, "Savefile is currently in use."
	try: saved.load()
	except: print "didn't load saveProcessor"
	if getConfig(filename=configFile)['global']['runOnce']:
		if saved.lastChecked > ( int(time.time()) - (60*10) ):
			raise Warning, "Minimum 10 minutes between thread scans."
	else:
		if saved.lastChecked > ( int(time.time()) - (getConfig(filename=configFile)['global']['scanMins']*60) ):
			raise Warning, "Threads have already been scanned."
	if saved.failedDown:
		status("Scanning previously failed downloads")
		for failureUrl, failureName, failureRss in  saved.failedDown:
			status("  Attempting to download %s" % failureUrl)
			if downloadFile(failureUrl, failureName, failureRss):
				status("  Success!")
				del saved.failedDown.index[ (failureUrl, failureName, failureRss) ]
			else:
				status("  Failure" % failureUrl)
	status( "Scanning threads" )
	# (dayOfWeek, hour)
	timeTuple = time.localtime().tm_wday, time.localtime().tm_hour
	rss = None
	if getConfig(filename=configFile)['global']['rss']:
		if getConfig(filename=configFile)['global']['rss']['filename']:
			if os.path.isfile( getConfig(filename=configFile)['global']['rss']['filename'] ):
				rss = makeRss(load=False)
				rssDataFile = open( getConfig(filename=configFile)['global']['rss']['filename'], 'r')
				rssData = rssDataFile.read()
				rssDataFile.close()
				rss.parse(rawfeed=rssData)
			else:
				loadRss ={}
				for key, value in getConfig(filename=configFile)['global']['rss'].iteritems():
					if key == 'title' or key == 'description' or key == 'link':
						loadRss[key] = value
				rss = makeRss(channelMeta=loadRss, load=True)
	for key in getConfig(filename=configFile)['threads'].keys():
		if getConfig(filename=configFile)['threads'][key]['active'] == False:	continue	# ignore inactive threads
		# if they specified a checkTime value, make sure we are in the specified range
		if getConfig(filename=configFile)['threads'][key]['checkTime'] != None:
			toContinue = True
			for timeCheck in getConfig(filename=configFile)['threads'][key]['checkTime']:
				timeLess = timeCheck[0], timeCheck[1]
				timeMore = timeCheck[0], timeCheck[2]
				if timeLess <= timeTuple <= timeMore:
					toContinue = False
					break
			if toContinue: continue
		if saved.minScanTime.has_key(key) and saved.minScanTime[key][0]  > ( int(time.time()) - saved.minScanTime[key][1]*60 ):
				status("RSS feed has indicated that we should wait greater than the scan time you have set in your configuration. Will try again at next configured scantime")
				continue
		status( "   * finding new downloads in thread %s" % key )
		if getConfig(filename=configFile)['threads'][key]['noSave'] == True:
			status( "     (not saving to disk)")
		try: config['threads'][key] = rssparse(getConfig(filename=configFile)['threads'][key], threadName=key)	
		except IOError, ioe: raise Fatal, "%s: %s" % (ioe.strerror, ioe.filename)
	if rss:
		while len(rss.items) > int(getConfig(filename=configFile)['global']['rss']['length']):
			rss.items.pop(0)
		rss.appendItemNodes()
		rss.closeFeed()
		rss.write(filename=getConfig(filename=configFile)['global']['rss']['filename'])
	saved.lastChecked = int(time.time()) -30
	saved.save()
	saved.unlock()
	config.save()

def main( runOnce=False ):
	config = getConfig(filename=configFile)
	sharedData = getSharedData()
	sharedData.scanoutput = ""
	if not runOnce:
		runOnce = getConfig(filename=configFile)['global']['runOnce']
	while True:
		try:
			sharedData.scanoutput += os.linesep * 2
			sharedData.scanning = True
			status( "[Waking up] %s" % time.asctime() )
			startTime = time.time()
			run()
			status( "Processing took %d seconds" % (time.time() - startTime) )
		except Warning, (message,):
			status( u"Warning: %s" % message )
		except Fatal, (message,):
			status( u"Error: %s" % message )
			sharedData.scanning = False
			raise SystemExit
		sharedData.scanning = False
		if runOnce:
			status( "[Complete] %s" % time.asctime() )
			break
		status( "[Sleeping] %s" % time.asctime() )
		elapsed = time.time() - saved.lastChecked
		#checkSleep has a 10 second resolution, let's sleep for 9, just to be on the safe side
		time.sleep(9)
		if  getConfig(filename=configFile)['global']['scanMins'] * 60 < time.time() - saved.lastChecked: checkSleep ( getConfig(filename=configFile)['global']['scanMins'] * 60 - elapsed )
		else: checkSleep( getConfig(filename=configFile)['global']['scanMins'] * 60 )
	
	

#if we lock saved before calling kill, it will be locked and we will never get to an unlock state which is our indicator that it is ok to kill.
try: 
	(argp, list) =  getopt.gnu_getopt(sys.argv[1:], "drokc:h", longopts=["daemon", "run", "runonce", "kill", "config=", "help"])
except	getopt.GetoptError:
		sys.stderr.write(helpMessage)
		sys.exit(1)

for param, argum in argp:
	if param == "--daemon" or param == "-d":	action = "daemon"		
	elif param == "--run" or param == "-r": action = "run"
	elif param == "--runonce" or param == "-o":
		action = "run"
		runOnce = True
	elif param == "--kill" or param == "-k":
		action = "kill"
		killData = open(os.path.join(getConfig(filename=configFile)['global']['workingDir'], getConfig(filename=configFile)['global']['daemonInfo']), 'r')
		for pidWanted in killData.readlines():
			pidWanted = pidWanted.strip()
			if pidWanted.startswith('process ID ='):
				pid = int(pidWanted.split('=')[-1].strip())
				break
		killDaemon(pid)
		open(os.path.join(getConfig(filename=configFile)['global']['workingDir'], getConfig(filename=configFile)['global']['daemonInfo']), 'w').write('')
		sys.exit()
	elif param == "--config" or param == "-c": configFile = argum
	elif param == "--help" or param == "-h": print helpMessage


if action == "run":
	status( "--- RssDler %s" % getVersion() )
	if os.getcwd() != getConfig(filename=configFile)['global']['workingDir']: os.chdir(getConfig(filename=configFile)['global']['workingDir'])
	try: import userFunctions
	except: userFunctions = None
	#this just isn't working quite right. PROBABLY (maybe?) has something to do with the "run twice" problem that i understand not at all.
##	import signal
##	signal.signal(signal.SIGINT, signal_handler)
	if runOnce != None:
		main(runOnce)
	else: main()
elif action == "daemon":
	#call daemon
	if (hasattr(os, "devnull")):
		REDIRECT_TO = os.devnull
	else:
		REDIRECT_TO = "/dev/null"
	config = getConfig(filename=configFile)
	status( "--- RssDler %s" % getVersion() )
	if os.getcwd() != getConfig(filename=configFile)['global']['workingDir']: os.chdir(getConfig(filename=configFile)['global']['workingDir'])
	callDaemon()
	try: import userFunctions
	except: userFunctions = None
##	import signal
##	signal.signal(signal.SIGINT, signal_handler)
	main()
