#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import feedparser
try: from BitTorrent.bencode import bdecode
except: from bencode import bdecode
import time, os, socket, cgi, codecs, cookielib, re, urllib, urllib2, mimetypes, urlparse
import pickle, copy, getopt, sys, ConfigParser
from UserDict import UserDict

# # # # #
# == Globals ==
# # # # #
_VERSION = "0.2.4"
USER_AGENT = "RSSDler %s" % _VERSION
_configInstance = None
_sharedData = None
_log = None
action = None
downloader = None
runOnce = None
configFile = 'config.txt'
cj = None
rss = None
UMASK = 0077
MAXFD = 1024
utfWriter = codecs.getwriter( "utf-8" )
sys.stdoutUTF = utfWriter( sys.stdout, "replace" )
sys.stderrUTF = utfWriter( sys.stderr, "replace" )

commentConfig = """
# the only required section (though the program won't do much without others)
[global]
# download files to this directory. Defaults to the working directory.
downloadDir = /home/user/downloads
# makes this the 'working directory' of rssdler. anytime you specify a filename without a path or a relative path, it will be relative to this 
workingDir = /home/user/.rssdler

# each section represents a feed
[somesite]
# just link to the feed
link = http://somesite.com/rss.xml
# and specify downloads (or don't to grab everything)
download1 = somefile
"""

helpMessage="""RSSDler is a Python based RSS downloader aka RSS broadcatcher. It happens to work just fine for grabbing RSS feeds of torrents. I have also used it for podcasts and such. Though designed with rtorrent in mind, it should work with any torrenting program that can read torrent files written to a directory.

Effort has been put into keeping the program from crashing from random errors like bad links and such. However, some of the exceptions caught are too broad and keep users from knowing what is wrong with their configuration. Try to be careful when setting up your configuration file. If you are having problems, try to start with a very basic setup and slowly increase its complexity. You need to have a basic understanding of regular expressions to setup the regex and download<x> options. If you do not know what and/or how to use regular expressions, google is your friend. There are literally dozens of tutorials and documentation on the subject with a range of difficulty levels from beginner to expert. If you are having problems that you believe are rssdler's fault, feel free to email me at the below address. Please be sure to include as much information as you can.

Command Line Options:
	--run/-r: run according to the configuration file
	--runonce/-o: run only once (overrides configuration file, if set to run forever)
	--daemon/-d: run in the background, according to the configuration file (Unix-like only)
	--kill/-k: kill the daemonized instance (Unix like only)
	--config/-c: specify a config file (default config.txt).
	--failed/-f: Use to clear the failed download queue. Use when you have a download stuck (perhaps removed from the site or wrong url in RSS feed) and you no longer care about RSSDler attempting to grab it. Will be appended to the saved download list to prevent readdition to the failed queue.

Non-standard Python libraries used:
	mechanize: http://wwwsearch.sourceforge.net/mechanize/ (this can now be overridden by setting urllib = True in global options. See below for details.
	feedparser: http://www.feedparser.org/
	BitTorrent: http://www.bittorrent.com (the python reference client)
	instead of BitTorrent, you can also just save the module bencode in your python path as bencode.py (perhaps most conveniently  in your working directory aka where you store all your RSSDler related files). This seems to work best for Python 2.5 as many distros do not have BitTorrent in 2.5's path: http://cheeseshop.python.org/pypi/BitTorrent-bencode/
	For debian based distros: "sudo apt-get install python-feedparser python-mechanize bittorrent"
	
Security Note: Prior to 0.2.4, there were several 'eval' statements in this program, which allowed running arbitrary code. Although removed, there is an attempt to import 'userFunctions' if you specify a postDownloadFunction in your configuration. Make sure only you have write permissions in the directory you run this from/what you set workingDir to so that userFunctions cannot be setup to run arbitrary code that you do not want running. Also make sure only you have write permissions to your configuration file. It would be wise to make a file userFunctions.py in your working directory to which only you have write access. I've also had reports of users running this as root. PLEASE do not do that. You shouldn't even be logging into your system as root, much less running programs meant for userland, especially when they are Internet facing.

Configuration File:
	There are two types of sections: global and threads. There can be as many thread sections as you wish, but only one global section. global must be named "global." Threads can be named however you wish, except 'global,' and each name should be unique. With a couple of noted exceptions, there are three types of options:
	
Boolean Options: 'True' is indicated by "True", "yes", or "1". "False" is indicated by "False", "no", or "0" (without the quotes)
Integer Options: Just an integer. 1, 2, 10, 1000, 2348. Not 1.1, 2.0, 999.3 or 'a'.
String Options: any string, should make sense in terms of the option being provided (e.g. a valid file/directory on disk; url to rss feed)

Required indicates RSSDler will not work if the option is not set. 
Recommended indicates that the default is probably not what you want. 
Optional indicates that circumstances such as use pattern, type of feed, etc. determine if/how it should be set.

Global Options:
	downloadDir: [Recommended] A string option. Default is current directory. Set to a directory in which you have write permission where downloaded files will go.
	workingDir: [Recommended] A string option. Default is current directory. Only needed with -d. Set to a directory on disk. Useful to make sure you don't run this from a partition that might get unmounted. If you use the -d switch (to run as a deamon) you must have this set or the program will die.
	minSize: [Optional] An integer option. Default None. Specify, in MB, the minimum size for a download to be. Files less than this size will not be saved to disk.
	maxSize: [Optional] An integer option. Default None. Specify, in MB, the maximum size for a download to be. Files greater than this size will not be saved to disk.
	log: [Optional] A boolean option. Default False. Will write to a log file (specified by logFile)
	logFile: [Optional] A string option. Default downloads.log. Specify a file on disk to write the log to.
	verbose: [Optional] A boolean option, defaulting to True. Set to False to disable verbose output.
	error: [Optional]. Integer Option. Default 1. RSSDler is attempting to implement a more sane 'output' versus 'error output' notifcation mechanism. This option overrides 'verbose' and 'log' for error messages. Setting this to 0 means to not show ANY error messages (even if you have verbose and log turned on). 1 means to send error messages to stderr. 2 means to log error messages to the log file (default if none is specified). 3 is equal to 1+2. :D in all seriousness, 3 means to print the error message to stderr AND to log the message in the log file. Negative values will be interpreted as 0, values greater than 4 as 3.
	cookieFile: [Optional] A string option. Default 'cookies.txt'. The file on disk, in Netscape Format (requires headers) that has cookie information for whatever site(s) you have set that require it.
	scanMins: [Optional] An integer option. Default 15. Values are in minutes. The number of minutes between scans. If a feed uses the <ttl> tag, it will be respected. That is, if you have scanMins set to 10 and the site sets <ttl>900</ttl> (900 seconds; 15 mins); then the feed will be scanned every other time. 
	runOnce: [Optional] A boolean option, default False. Set to True to force rssdler to exit after it has scanned the configured feeds.
	urllib: [Optional]. Boolean Option. Default False. Setting this to true removes the dependency on mechanize for those platforms where mechanize may not be available or may work improperly. You lose several pieces of functionality, however. 1) Referers will no longer work. On most sites, this will not be a problem, but some sites require referers and will deny requests if the referer is not passed back to the site. 2) Some sites have various 'refresh' mechanisms that may redirect you around before actually giving you the file to download. Mechanize has the ability to follow these sites.
	rssFeed: [Optional] Boolean Option. Default False. Setting this option allows you to create your own rss feed of the objects you have downloaded. It's a basic feed, likely to not include links to the original files. The related rss items (all are required if this is set to True):
	rssLength: [Optional]  Integer. Default 20. An integer. How many entries should the RSS feed store before it starts dropping old items. 0 would literally mean to store no items
	rssTitle: [Optional] A string. Default "some RSS Title".  The title the rss feed will carry.
	rssLink: [Optional]   string: Default 'somelink.com/%%s' %% self['rssFilename']. Where the rss feed can be located. Typically an http link.
	rssDescription: [Optional] A string. Default "Some RSS Description". A short description of what the feed contains.
	rssFilename: [Optional] A string. Default 'rssdownloadfeed.xml'. Where to store the feed on disk.
	saveFile: [Optional] A string option. Default savedstate.dat. Specify a file on disk to write the saved state information to. This keeps track of previously downloaded files and other 'state' information necessary to keep the program running coherently, especially between shutdown/startup
	lockPort: [Optional] An integer option. Default 8023. The port on which the savedstate.dat file will be locked for writing. Necessary to maintain the integrity of the state information.
	daemonInfo: [Optional] A string option. Default daemon.info. Only needed with -d. Set to a file on disk. Daemon info will be written there so that -k and such will work. (full path over rides workingDir) 
	rss: DEPRECATED, will no longer be processed.

	
Thread options:
	link: [Required] A string option. Link to the rss feed.
	active:  [Optional] A boolean option. Default is True, set to False to disable checking of that feed.
	maxSize: [Optional] An integer option, in MB. default is None. A thread based maxSize like in global. If set to None, will default to global's maxSize. Other values override global, including 0 to indicate no maxSize.
	minSize: [Optional] An integer opton, in MB. default is None. A thread based minSize, like in global. If set to None, will default to global's minSize. Other values override global, including 0 to indicate no minSize.
	noSave: [Optional] A boolean option. Default to False. If true, will remember download objects for the save processor on first run, but does not download.
	directory: [Optional] A string option. Default to None. If set, overrides global's downloadDir, directory to download download objects to.
	checkTime<x>Day: [Optional] A string option. Either the standard 3 letter abbreviation of the day of the week, or the full name. One of Three options that will specify a scan time. the <x> is an integer. Will only scan the rss feed during the day specified. Can Further curtail scan time with Start and Stop (see next).
	checkTime<x>Start: [Optional] An integer option. Default: 0. The hour (0-23) at which to start scanning on correlated day. MUST specify checkTime<x>Day.
	checkTime<x>Stop: [Optional] An integer option. Default 23. The hour (0-23) at which to stop scanning on correlated day. MUST specify checkTime<x>Day.
	checkTime: DEPRECATED. Will no longer be processed.
	regExTrue: [Optional] A string (regex) option. Default None. If specified, will only download if a regex search of the download name (title key in entry dictionary of feedparser instance) returns True. This will be converted to a python regex object. Use all lower case, as the name is converted to all lower case.
	regExTrueOptions: [Optional] A string option. Default None. Options (like re.IGNORECASE) to go along with regExTrue when compiling the regex object. IGNORECASE is unnecessary however.
	regExFalse: [Optional] A string (regex) option. Default None. If specified, will only download if a regex search of the download name returns False. This will be converted to a python regex object. Use all lower case, as the name is converted to all lower case.
	regExFalseOptions: [Optional] A string option. Default None. Options (like re.IGNORECASE) to go along with regExFalse when compiling the regex object
	postDownloadFunction: [Optional] A string option. Default None. The name of a function, stored in userFunctions.py found in the current working directory (with -d, workingDir, otherwise the directory the program is started from). Must accept the following arguments (of course they can be ignored): directory the file was stored in, the filename, and the feedparser entry for that object.
	The following options are ignored if not set (obviously). But once set, they change the behavior of regExTrue (RET) and regExFalse (REF). Without specifying these options, if something matches RET and doesn't match REF, it is downloaded, i.e. RET and REF constitute sufficient conditions to download afile. Once these are specified, RET and REF become necessary (well, when download<x>(True|False) are set to True, or a string for False) but not sufficient conditions for any given download. If ou set RET/REF to None, they are of course ignored and fulfill their 'necessity.' You can specify these options as many times as you like, by just changing <x> to another number. 
	download<x>: [Optional] No default. where <x> is an integer, this is a 'positive' hit regex. This is required for download<x>true and download<x>false.
	download<x>False: [Optional] Default = True. However, this is not strictly a boolean option. True means you want to keep regExFalse against download<x>. If not, set to False, and there will be no 'negative' regex that will be checked against. You can also set this to a string (i.e. a regex) that will be a negative regex ONLY for the corresponding download<x>. Most strings are legal, however the following False/True/Yes/No/0/1 are reserved words when used alone and are interpreted, in a case insensitive manner as Boolean arguments. Requires a corresponding download<x> argument.
	download<x>True. [Optional] A Boolean option. default True. True checks against regExTrue. False ignores regExTrue. Requires a corresponding download<x> argument.
	download<x>Dir. [Optional] A String option. Default None. If specified, the first of the download<x> tuples to match up with the download name, downloads the file to the directory specified here. Full path is recommended.


A Netscape cookies file must have the proper header that looks like this:
# HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.
# To delete cookies, use the Cookie Manager.

cookiedata ....

Commented Config File:

%s

RSSDler - RSS Broadcatcher
Copyright (C) 2007, lostnihilist

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; under version 2 of the license.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

Contact:  lostnihilist <lostnihilist@gmail.com>
""" % commentConfig

# # # # #
#Exceptions
# # # # #
class Fatal( Exception ): 
	def __init__(self, value="An error occurred and rssdler does not know how to react" ):
		self.value = value
	def __str__(self):
		return repr( self.value)
	
class Warning( Exception ):
	def __init__(self, value="""An error occurred, but no action needs to be taken by the user at this time.""" ):
		self.value = value
	def __str__(self):
		return repr( self.value)
	
class Locked( Exception ):
	def __init__(self, value="""An attempt was made to lock() the savefile while it was already locked.""" ):
		self.value = value
	def __str__(self):
		return repr( self.value)
	


# # # # #
#Downloading
# # # # #
def cookieHandler():
	global cj
	if cj == 1 or not getConfig()['global']['cookieFile']: return False
	if getConfig()['global']['urllib']:	
		if isinstance(cj, urllib2.cookielib.MozillaCookieJar): return True
		cj = urllib2.cookielib.MozillaCookieJar()
		try: cj.load(getConfig()['global']['cookieFile'])
		except (cookielib.LoadError, IOError), m:
			errorMsg( str(m) + ' disabling cookies. To re-enable cookies, stop RSSDler, correct the problem, and restart.')
			return False
	else: 
		if isinstance(cj, mechanize.MozillaCookieJar): return True
		cj = mechanize.MozillaCookieJar()
		try: cj.load(getConfig()['global']['cookieFile'])
		except (mechanize._clientcookie.LoadError, IOError), m:
			errorMsg( str(m) + ' disabling cookies. To re-enable cookies, stop rssdler, correct the problem, and restart.')
			return False
	return True

def isQuoted(aStr):
	"""technically, returns whether string literal % is in the string. This, in most cases, should tell us whether that string is percent encoded, though if there is a literal % in the url, that will report incorrectly as being quoted"""
	return '%' in aStr

def encodeQuoteUrl( url ):
	"""take a url, split it up, percent encode everything but the hostname and protocol, recombine and return the resulting string"""
	try:	url = url.encode('ISO-8859-1')
	except UnicodeEncodeError, m: 
		errorMsg( str(m) + os.linesep + url )
		return None
	if not isQuoted(url):
		a = list(urlparse.urlparse( url ))
		for i in xrange( 2, len( a[2:] ) ):
			if a[i] and not isQuoted(a[i]): a[i] = urllib.quote( a[i] )
		url = urlparse.urlunparse( tuple( a ) )
	return url

def urllib2RetrievePage( url, txheaders=(('User-agent', USER_AGENT),)):
	"""URL is the full path to the resource we are retrieve/Posting
	txheaders is a sequence of (field,value) pairs of any extra headers you would like to add
	"""
	global cj, opener, config
	if url:		
		url = encodeQuoteUrl( url )
		if not url: return False
	headerDict = dict(txheaders)
	if cookieHandler():
		opener = urllib2.build_opener (urllib2.HTTPCookieProcessor(cj) )
		urllib2.install_opener(opener)
	else:
		opener = urllib2.build_opener( )
		urllib2.install_opener(opener)
		cj = 1
	request = urllib2.Request(url, headers=headerDict)
	return urllib2.urlopen( request )

def mechRetrievePage(url, txheaders=(('User-agent', USER_AGENT),), ):
	"""
		URL is the full path to the resource we are retrieve/Posting
		txheaders: sequence of tuples of header key, value to manually add to the request object
	"""
	# this could be improved dramatically
	global cj, opener, config, mechanize
	try: import mechanize
	except ImportError, msg:
		errorMsg( str(msg) )
		raise SystemExit
	if url:	
		url = encodeQuoteUrl( url )
		if not url: return False
	if cookieHandler():
		opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cj), mechanize.HTTPRefreshProcessor(), mechanize.HTTPRedirectHandler(), mechanize.HTTPEquivProcessor())
		mechanize.install_opener(opener)
	else:
		opener = mechanize.build_opener(mechanize.HTTPRefreshProcessor(), mechanize.HTTPRedirectHandler(), mechanize.HTTPEquivProcessor())
		mechanize.install_opener(opener)
		cj = 1
	request = mechanize.Request( url, headers=dict( txheaders ) )
	return mechanize.urlopen( request )

def getFileSize( info, data=None ):
	"""give me the HTTP headers (info) and, if you expect it to be a torrent file, the actual file, i'll return the filesize, of type None if not determined"""
	size = None
	if re.search("torrent", info['content-type']):
		# don't pretend we know the size when we don't
		if not data: return size
		tparse = bdecode(data)
		if tparse['info'].has_key('length'): size = int(tparse['info']['length'])
		elif tparse['info'].has_key('files'):
			size = int(0)
			for j in tparse['info']['files']:	size += int(j['length'])
	else:
		try: size = int(info['content-length'])
		except:	pass
	return size
	
def checkFileSize(size, threadName):
	if getConfig()['threads'][threadName]['maxSize'] != None: maxSize = getConfig()['threads'][threadName]['maxSize']
	elif getConfig()['global']['maxSize'] != None: maxSize = getConfig()['global']['maxSize']
	else: maxSize = None
	if getConfig()['threads'][threadName]['minSize'] != None: minSize = getConfig()['threads'][threadName]['minSize']
	elif getConfig()['global']['minSize'] != None: minSize = getConfig()['global']['minSize']
	else: minSize = None
	if maxSize:
		maxSize = maxSize * 1024 * 1024
		if size > maxSize: 
			return False
	if minSize:
		minSize = minSize * 1024 * 1024
		if size <  minSize:
			return False
	return True

def getFilenameFromHTTP(info, url):
	"""info is an http header from the download, url is the url to the downloaded file (responseObject.geturl() )"""
	filename = None
	if info.has_key('content-disposition'): 
		# what if there is a ';' in the filename?
		for i in [ x.strip() for x in info['content-disposition'].split(';') ]:
			if 'filename=' not in i: continue
			filename = '='.join(i.split('=')[1:])
			if filename.startswith('"') and  filename.endswith('"'): filename = filename[1:-1]
			break
	# not else because the search for a filename may have failed
	if not filename: 
		filenameTup = urlparse.urlparse(url)
		# Tup[2] is the path
		filename = urllib.unquote( filenameTup[2].split('/')[-1] )
	typeGuess = mimetypes.guess_type(filename)[0]
	if typeGuess and info.has_key('content-type') and ( info['content-type'] in typeGuess or typeGuess in info['content-type'] ): return filename
	else:
		if not info.has_key('content_type'):
			msg = "Proper file extension could not be determined for the downloaded file: %s you may need to add an extension to the file for it to work in some programs. It came from url %s. It may be correct, but I have no way of knowing due to insufficient information from the server." % (filename, url)
			errorMsg( msg )
		else:
			for i in [x.strip() for x in info['content-type'].split(';') ]:
				fileExt = mimetypes.guess_extension(i)
				if fileExt:
					if not filename: filename = str( int(time.time()) ) + fileExt
					else: filename += fileExt
					break
	if not filename: 
		errorMsg('Could not determine filename for torrent from %s' % url)
		raise Fatal
	return filename

def downloadFile(url, threadName, rssItemNode, downloadLDir):
	try: data = downloader(url)
	except (urllib2.HTTPError, urllib2.URLError), m: 
		errorMsg( str(m) + os.linesep + 'error grabbing url: %s%s' % (url, os.linesep) )
		return False
	if not data: return False
	dataPage = data.read()
	dataInfo = data.info()
	# could try to grab filename from ppage item title attribute, but this seems safer for file extension assurance
	filename = getFilenameFromHTTP(dataInfo, data.geturl())
	size = getFileSize(dataInfo, dataPage)
	# check size against configuration options
	if size:
		if not checkFileSize(size, threadName): 
			# size is outside range, don't need the data, but want to report that we succeeded in getting data
			del data, dataPage, dataInfo
			return True
	filename = unicode( filename, "utf-8", "replace" )
	if downloadLDir: directory = downloadLDir
	elif getConfig()['threads'][threadName]['directory']: directory = getConfig()['threads'][threadName]['directory']
	else: directory = getConfig()['global']['downloadDir']
	outfile = open( os.path.join(directory,  filename), "wb" )
	outfile.write( dataPage )
	outfile.close()
	logMsg( "\tFilename: %s%s\tDirectory: %s%s\tFrom Thread: %s%s" % ( filename, os.linesep, directory, os.linesep, threadName, os.linesep ) )
	if rss:
		if rssItemNode.has_key('description'): description = rssItemNode['description']
		else: description = None
		if rssItemNode.has_key('title'): title = rssItemNode['title']
		else: title = None
		pubdate = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
		itemLoad = {'title':title , 'description':description , 'pubDate':pubdate }
		rss.makeItemNode( itemAttr=itemLoad )
	if getConfig()['threads'][threadName]['postDownloadFunction']:
		try: 
			import userFunctions
			useFunct = userFunctions.__getattribute__( getConfig()['threads'][threadName]['postDownloadFunction'] )
			useFunct( directory, filename, rssItemNode )
			del userFunctions, useFunct
		except: pass
	status( "   * saved to file: %s" % filename)
	return True

def searchFailed(urlTest):
	for url, trash1, trash2, trash3 in saved.failedDown:
		if urlTest == url: return True
	return False

def checkRegExGTrue(ThreadLink, itemNode):
	"""return type True or False"""
	# [response from regExTrue, regExFalse, downloads, downloadFalse, downloadTrue]
	if ThreadLink['regExTrue']:
		if ThreadLink['regExTrueOptions']: regExSearch = re.compile(ThreadLink['regExTrue'], re.__getattribute__(ThreadLink['regExTrueOptions']) )
		else: regExSearch = re.compile(ThreadLink['regExTrue'])
		if regExSearch.search(itemNode['title'].lower()): return True
		else: return False
	else: return True

def checkRegExGFalse(ThreadLink, itemNode):
	"""return type True or False"""
	if ThreadLink['regExFalse']:
		if ThreadLink['regExFalseOptions']: regExSearch = re.compile(ThreadLink['regExFalse'], re.__getattribute__(ThreadLink['regExFalseOptions']) )
		else: regExSearch = re.compile(ThreadLink['regExFalse'])
		if regExSearch.search(itemNode['title'].lower()):	return False
		else: return True
	else: return True

def checkRegEx(ThreadLink, itemNode):
	if ThreadLink['downloads']:
		# save this as a type. It will return a tuple. Check against tuple[0], return the tuple
		LDown = checkRegExDown(ThreadLink, itemNode)
		if LDown[0] == True: 			return (True, LDown[1])
		else: 			return (False, None)
	elif checkRegExGFalse(ThreadLink, itemNode) and checkRegExGTrue(ThreadLink, itemNode): 		return (True, None)
	else: 	return (False, None)
		

def checkRegExDown(ThreadLink, itemNode):
	# Also, it's incredibly inefficient
	# for every x rss entries and y download items, it runs this xy times.
	# ( local true, 
	for downloadTup in ThreadLink['downloads']:
		if ThreadLink['regExTrueOptions']: LTrue = re.compile( downloadTup[0], re.__getattribute__(ThreadLink['regExTrueOptions']) )
		else: LTrue = re.compile(downloadTup[0])
		if not LTrue.search(itemNode['title'].lower()): continue
		if type(downloadTup[1]) == type(''):
			if ThreadLink['regExFalseOptions']: LFalse = re.compile(downloadTup[1], re.__getattribute__(ThreadLink['regExFalseOptions']))
			else: LFalse = re.compile(downloadTup[1])
			if LFalse.search(itemNode['title'].lower()): continue
		elif downloadTup[1] == False: pass
		elif downloadTup[1] == True:
			if not checkRegExGFalse(ThreadLink, itemNode): continue
		if downloadTup[2] == True:
			if not checkRegExGTrue(ThreadLink, itemNode): continue
		elif downloadTup[2] == False: pass
		return (True, downloadTup[3])
	return (False, None)
	
def rssparse(thread, threadName):
	"""Give me a ThreadLink object, including an rss url to a thread, I'll 
	give you back an updated ThreadLink object, and download the appropriate torrents
	based on the configuration.
	assumes feed parser will create the following attributes:
		['entries'][x]['link']
		['entries'][x]['title']
	"""
	ThreadLink = copy.deepcopy(thread)
	try: page = downloader(ThreadLink['link'])
	except (urllib2.HTTPError, urllib2.URLError), m:	
		errorMsg( str(m) + os.linesep + 'error grabbing url %s%s' % (ThreadLink['link'], os.linesep) )
		return ThreadLink
	if not page: return ThreadLink
	ppage = feedparser.parse(page.read())
	if ppage['feed'].has_key('ttl') and ppage['feed']['ttl'] != '':
		saved.minScanTime[threadName] = (time.time(), int(ppage['feed']['ttl']) )
	for i in range(len(ppage['entries'])):
		#if we have downloaded before, just skip (but what about e.g. multiple rips of about same size/type we might download multiple times)
		if ppage['entries'][i]['link'] in saved.downloads: continue
		# if it failed before, no reason to believe it will work now, plus it's already queued up
		if searchFailed( ppage['entries'][i]['link'] ): continue
		# make sure it matches what we want
		dirTuple = checkRegEx(ThreadLink, ppage['entries'][i])
		if not dirTuple[0]: continue
		# if we matched above, but don't want to download, register as downloaded, and then move on
		if ThreadLink['noSave']:  
			saved.downloads.append(ppage['entries'][i]['link'] )
			continue
		if downloadFile(ppage['entries'][i]['link'], threadName, ppage['entries'][i], dirTuple[1]):
			saved.downloads.append( ppage['entries'][i]['link'] )
		else:
			saved.failedDown.append( (ppage['entries'][i]['link'], threadName, ppage['entries'][i], dirTuple[1]) )
		ThreadLink['noSave'] = False
	return ThreadLink

# # # # #
#Persistence
# # # # #
class MakeRss:
	"""returns an xml document  in line with the rss2.0 specification.
	rss = MakeRss()
	rss......
	rss.appendItemNodes()
	rss.close()
	rss.write()
	"""
	def __init__(self, channelMeta={}, parse=False, filename=None):
		global PrettyPrint, minidom
		try:
			if minidom: pass
		except: from xml.dom import minidom
		self.chanMetOpt = ['title', 'description', 'link', 'language', 'copyright', 'managingEditor', 'webMaster', 'pubDate', 'lastBuildDate', 'category', 'generator', 'docs', 'cloud', 'ttl', 'image', 'rating', 'textInput', 'skipHours', 'skipDays']
		self.itemMeta = ['title', 'link', 'description', 'author', 'category', 'comments', 'enclosure', 'guid', 'pubDate', 'source']
		self.feed = minidom.Document()
		self.rss = self.feed.createElement('rss')
		self.rss.setAttribute('version', '2.0')
		self.channel = self.feed.createElement('channel')
		self.channelMeta = channelMeta
		self.filename = filename
		self.items = []
		if parse == True: self.parse()
	def loadChanOpt(self):
		if not self.channelMeta.has_key('title') or not self.channelMeta.has_key('description') or not self.channelMeta.has_key('link'):
			raise Exception, "channelMeta must specify at least 'title', 'description', and 'link' according to RSS2.0 spec. these are case sensitive"
		for key in self.chanMetOpt:
			if self.channelMeta.has_key(key):
				chanMet = self.makeTextNode(key, self.channelMeta[key])
				self.channel.appendChild(chanMet)
	def makeTextNode(self, nodeName, nodeText, nodeAttributes=[]):
		"""returns an xml text element node, with input being the name of the node, text, and optionally node attributes as a sequence
		of tuple pairs (attributeName, attributeValue)
		"""
		node = self.feed.createElement(nodeName)
		text = self.feed.createTextNode(str(nodeText))
		node.appendChild(text)
		if nodeAttributes:
			for attribute, value in nodeAttributes: 
				node.setAttribute(attribute, value)
		return node
	def makeItemNode(self, itemAttr={}, action='insert'):
		"""action: 
			insert: put at 0th position in list
			append: tack on to the end of list
			return: do not attach to self.items at all, just return the XML object.
		"""
		global time, random
		try:
			if time: pass
		except: import time
		try:
			if random: pass
		except:
			import random
		"""should have an item "child" we will be adding to that"""
		if 'title' in itemAttr.keys() or 'description' in itemAttr.keys(): pass
		else:	raise Exception, "must provide at least a title OR description for each item"
		if 'pubdate' not in itemAttr.keys() and 'pubDate' not in itemAttr.keys():
			if itemAttr.has_key('updated_parsed'): 
				itemAttr['pubDate'] = itemAttr['pubdate'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", itemAttr['updated_parsed'])
			elif itemAttr.has_key('updated'): itemAttr['pubDate'] = itemAttr['pubdate'] = itemAttr['updated']
			else: itemAttr['pubDate'] = itemAttr['pubdate'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
		if not itemAttr.has_key('guid'):
			if itemAttr.has_key('link'): itemAttr['guid'] = itemAttr['link']
			else: itemAttr['guid'] = random.randint(0,9000000000)
		item = self.feed.createElement('item')
		for key in self.itemMeta:
			if itemAttr.has_key(key):
				itemNode = self.makeTextNode(key, itemAttr[key])
				item.appendChild(itemNode)
		if action.lower() == 'insert':	self.items.insert(0, item)
		elif action.lower() == 'append': self.items.append(item)
		elif action.lower() == 'return': return item
		else: raise Exception, "Illegal value for action, must be insert, append, or return"
	def appendItemNodes(self, length=20, pop=False):
		"""adds the items in self.items to self.channel. if pop is True, each item is removed as it is added to channel. starts at the front of the list"""
		if pop:
			del self.items[length:]
			while self.items:	self.channel.appendChild( self.items.pop(0) )
		else:
			appendItems = self.items[:length]
			for item in appendItems: self.channel.appendChild( item )
	def close(self, length=20, pop=False):
		self.loadChanOpt()
		self.appendItemNodes(length=length, pop=pop)
		self.rss.appendChild(self.channel)
		self.feed.appendChild(self.rss)
	def parse(self, filename=None, rawfeed=None, parsedfeed=None, itemsonly=False):
		"""give parse a raw feed (just the xml/rss file, unparsed) and it will fill in the class attributes, and allow you to modify the feed.
		Or give me a feedparser.parsed feed (parsedfeed) and I'll do the same"""
		global feedparser, time
		try:
			if time: pass
		except: import time
		try:
			if feedparser: pass
		except: import feedparser
		if filename:
			filedata = codecs.open(filename, 'r', 'utf-8')
			p = feedparser.parse(filedata.read())
			filedata.close()
		elif rawfeed:	p = feedparser.parse(rawfeed)
		elif parsedfeed: p = parsedfeed
		elif self.filename:
			filedata = codecs.open(self.filename, 'r', 'utf-8')
			p = feedparser.parse(filedata.read())
			filedata.close()
		else: raise Exception, "Must give either a rawfeed, filename, set self.filename, or parsedfeed"
		if not itemsonly:
			if p['feed'].has_key('updated'): p['feed']['pubDate'] = p['feed']['pubdate']  = p['feed']['updated']
			elif p['feed'].has_key('updated_parsed'): 
				p['feed']['pubDate'] = p['feed']['pubdate']  = time.strftime("%a, %d %b %Y %H:%M:%S GMT", p['feed']['updated_parsed'])
			self.channelMeta = p['feed']
##					self.channel.appendChild(self.makeTextNode(key, p['feed'][key.lower()]))
		for entry in p['entries']:	self.makeItemNode(itemAttr=entry, action='append')
	def write(self, filename=None, file=None):
		"""if fed filename, will write and close self.feed to file at filename.
		if fed file, will write to file, but closing it is up to you"""
		global PrettyPrint
		try:
			if PrettyPrint: pass
		except: from xml.dom.ext import PrettyPrint
		if file: PrettyPrint(self.feed, file)
		elif filename:
			outfile = codecs.open(filename, 'w', 'utf-8')
			PrettyPrint(self.feed, outfile)
			outfile.close()
		else:
			outfile = codecs.open(self.filename, 'w', 'utf-8')
			PrettyPrint(self.feed, outfile)
			outfile.close()

class GlobalOptions(UserDict):
	"""Represents the options for running the program as a dictionary. See helpMessage for appropriate defaults"""
	def __init__(self):
		UserDict.__init__(self)
		self['verbose'] = True
		self['downloadDir'] = os.getcwd()
		self['runOnce'] = False
		self['maxSize'] = None
		self['minSize'] = None
		self['log'] = False
		self['logFile'] = 'downloads.log'
		self['saveFile'] = 'savedstate.dat'
		self['scanMins'] = 15
		self['lockPort'] = 8023
		self['cookieFile'] = None
		self['workingDir'] = os.getcwd()
		self['daemonInfo'] = 'daemon.info'
		self['rssFeed'] = False
		self['rssDescription'] = "Some RSS Description"
		self['rssFilename'] = 'rssdownloadfeed.xml'
		self['rssLength'] = 20
		self['rssLink'] = 'somelink.com/%s' % self['rssFilename']
		self['rssTitle'] = "some RSS Title"
		self['urllib'] = False
		self['error'] = 1

class ThreadLink(UserDict):
	"""See helpMessage for details of attributes.
	Attributes:
		Programmers Note: downloads should be a sequence of tuples of (download<x>, download<x>False, download<x>True, download<x>Dir)
		
	"""
	def __init__(self, name=None, link=None, active=True, maxSize=None, minSize=None, noSave=False, directory=None, checkTime=(), regExTrue=None, regExTrueOptions=None, regExFalse=None, regExFalseOptions=None, postDownloadFunction=None, downloads=()):
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
		self['downloads'] = downloads
class SaveInfo(UserDict):
	def __init__(self, lastChecked=0, downloads=[]):
		UserDict.__init__(self)
		self['lastChecked'] = lastChecked
		self['downloads'] = downloads
		self['minScanTime'] = {}
		self['failedDown'] = []

class SaveProcessor:
	def __init__(self, saveFileName="savedstate.dat"):
		"""saveFileName: location where we store persistence data
		lastChecked: seconds since epoch when we last checked the threads
		downloads: a list of download links, so that we do not repeat ourselves
		minScanTime: a dictionary, keyed by rss link aka thread name, with values of tuples (x,y) where x=last scan time for that thread,
			y=min scan time in minutes, only set if ttl is set in rss feed, otherwise respect checkTime and lastChecked
		failedDown: a list of tuples (item link, threadname, rssItemNode, localized directory to download to (None if to use global) ). 
		(ppage['entries'][i]['link'], threadName, ppage['entries'][i], dirTuple[1]) 
		This means that the regex, at the time of parsing, identified this file as worthy of downloading, but there was some failure in the retrieval process. Size will be checked against the configuration state at the time of the redownload attempt, not the size configuration at the time of the initial download attempt (if there is a difference)
		"""
		self.saveFileName = saveFileName
		self.lastChecked = 0
		self.downloads = []
		self.failedDown = []
		self.minScanTime = {}
		self.lockSock = None
	def save(self):
		saveFile = SaveInfo()
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
			self.lockSock.bind( ('127.0.0.1', getConfig()['global']['lockPort']) )
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
		self.dayList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', '0', '1', '2', '3', '4', '5', '6']
		self.filename = filename
		if not os.path.isfile( filename ): 
			errorMsg( msg="Configuration File could not be found, exiting...", noconfig=True)
			raise SystemExit
		self.read(filename)
		self['global'] = GlobalOptions()
		self['threads'] = {}
		self.parse()
		self.check()
	def parse(self):
		boolOptionsGlobal = ['verbose', 'runOnce', 'log', 'active', 'rssFeed', 'urllib']
		boolOptionsThread = ['active', 'noSave']
		stringOptionsGlobal = ['downloadDir', 'saveFile', 'cookieFile', 'logFile', 'workingDir', 'daemonInfo', 'rssFilename', 'rssLink', 'rssDescription', 'rssTitle']
		stringOptionsThread = ['link', 'directory', 'postDownloadFunction', 'regExTrue', 'regExTrueOptions', 'regExFalse', 'regExFalseOptions']	
		intOptionsGlobal = ['maxSize', 'minSize', 'lockPort', 'scanMins', 'rssLength', 'error']
		intOptionsThread = ['maxSize', 'minSize']
		for option in boolOptionsGlobal:
			try: 
				if option.lower() in self.options('global'): 
					try: self['global'][option] = self.getboolean('global', option)
					except: pass
			except ConfigParser.NoSectionError, m:
				errorMsg( str(m), noconfig=True)
				raise SystemExit
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
		threads = self.sections()
		del threads[threads.index('global')]
		for thread in threads:
			self['threads'][thread] = ThreadLink()
			for option in boolOptionsThread:
				if option.lower() in self.options(thread):
					try: self['threads'][thread][option] = self.getboolean(thread, option)
					except: pass
			for option in stringOptionsThread:
				if option.lower() in self.options(thread):
					self['threads'][thread][option] = self.get(thread, option)
					if self['threads'][thread][option] == '' or self['threads'][thread][option].lower() == 'none': self['threads'][thread][option] = None
			for option in intOptionsThread:
				if option.lower() in self.options(thread):
					try: self['threads'][thread][option] = self.getint(thread, option)
					except: pass
			#populate thread.downloads
			downList = []
			for threadOption in self.options(thread):
				if threadOption.startswith('download'): downList.append(threadOption)
			downList.sort()
			downTuple = []
			for i in downList:
				optionDown = self.get(thread, i)
				if i.endswith('false'): 
					if optionDown.lower() == 'false' or optionDown.lower() == '0' or optionDown.lower() == 'no':
						downTuple[-1][1]  = False
					elif optionDown.lower() =='true' or optionDown.lower() == '1' or optionDown.lower() == 'yes':
						downTuple[-1][1] = True
					else: downTuple[-1][1] = optionDown
				elif i.endswith('true'): 
					if optionDown.lower() == 'false' or optionDown.lower() == '0' or optionDown.lower() == 'no':
						downTuple[-1][2]  = False
					elif optionDown.lower() =='true' or optionDown.lower() == '1' or optionDown.lower() == 'yes':
						downTuple[-1][2] = True
					else: downTuple[-1][2] = optionDown
				elif i.endswith('dir'):
					if optionDown.lower() == 'none': downTuple[-1][3] = None
					else: downTuple[-1][3] = optionDown
				# default downloads options set here
				# should we double check that this isn't equal to something else?
				else: downTuple.append( [optionDown, True, True, None] )
				#make immutable, b/c this shouldn't change again
			downTuple2 = []
			for regExPair in downTuple: 
				downTuple2.append(tuple(regExPair))
			if downTuple2: self['threads'][thread]['downloads'] = tuple(downTuple2)
			# populate checkTime
			checkList = []
			for threadOption in self.options(thread):
				if threadOption.startswith('checktime'): checkList.append(threadOption)
			checkList.sort()
			checkTuple = []
			for j in checkList:
				optionCheck = self.get(thread, j)
				if j.endswith('day'):
					if self.dayList.count(optionCheck.capitalize()): 
						checkTuple.append( [self.dayList.index(optionCheck.capitalize()) % 7 , 0, 23] )
					else:
						raise Exception, "Could not identify valid day of the week for %s" % optionCheck
				elif j.endswith('start'): 
					checkTuple[-1][1] = int(optionCheck)
					if checkTuple[-1][1] > 23: checkTuple[-1][1] = 23
					elif checkTuple[-1][1] < 0: checkTuple[-1][1] = 0
				elif j.endswith('stop'): 
					checkTuple[-1][2] = int(optionCheck)
					if checkTuple[-1][2] > 23: checkTuple[-1][2] = 23
					elif checkTuple[-1][2] < 0: checkTuple[-1][2] = 0
			checkTuple2 = []
			for checkPair in checkTuple: checkTuple2.append( tuple(checkPair))
			if checkTuple2: self['threads'][thread]['checkTime'] = tuple(checkTuple2)
	def check(self):
		if not self['global'].has_key('saveFile') or self['global']['saveFile'] == None:
			self['global']['saveFile'] = 'savedstate.dat'
		if not self['global'].has_key('downloadDir') or self['global']['downloadDir'] == None:
			raise Exception, "Must specify downloadDir in [global] config"
		if not self['global'].has_key('runOnce') or self['global']['runOnce'] == None:
			self['global']['runOnce'] = False
		if not self['global'].has_key('scanMins') or self['global']['scanMins'] == None:
			self['global']['scanMins'] = 15
##		if self['global'].has_key('scanMins') and self['global']['scanMins'] < 10: self['global']['scanMins'] = 15
		if self['global']['cookieFile'] == '':
			self['global']['cookieFile'] = None
		if not self['global'].has_key('lockPort') or self['global']['lockPort'] == None:
			self['global']['lockPort'] = 8023
		if self['global'].has_key('log') and self['global']['log']:
			if not self['global'].has_key('logFile') or self['global']['logFile'] == None:
				self['global']['logFile'] = 'downloads.log'
		# check all directories to make sure they exist. Ask for creation?
		if self['global']['downloadDir']:
			if not os.path.isdir( os.path.join(self['global']['workingDir'], self['global']['downloadDir']) ):
				try: os.mkdir( os.path.join(self['global']['workingDir'], self['global']['downloadDir']) )
				except Exception, m: errorMsg( str(m) + os.linesep + "Could not find path %s and could not make a directory there. Please make sure this path is correct and try creating the folder with proper permissions for me" % os.path.join(self['global']['workingDir'], self['global']['downloadDir']), noconfig=True )
		for thread in self['threads']:
			if self['threads'][thread]['directory']:
				if not os.path.isdir( os.path.join(self['global']['workingDir'], self['threads'][thread]['directory']) ):
					try: os.mkdir( os.path.join(self['global']['workingDir'], self['threads'][thread]['directory']) )
					except Exception, m: 
						errorMsg( str(m) + os.linesep + "Could not find path %s and could not make a directory there. Please make sure this path is correct and try creating the folder with proper permissions for me" % os.path.join(self['global']['workingDir'], self['threads'][thread]['directory']), noconfig=True)
						raise SystemExit
			if len(self['threads'][thread]['downloads']) != 0: 
				for downTup in self['threads'][thread]['downloads']:
					if downTup[3]:
						if not os.path.isdir( os.path.join(self['global']['workingDir'], downTup[3] ) ):
							try: os.mkdir( os.path.join(self['global']['workingDir'], downTup[3] ) )
							except Exception, m:
								errorMsg( str(m) + os.linesep + "Could not find path %s and could not make a directory there. Please make sure this path is correct and try creating the folder with proper permissions for me" % os.path.join(self['global']['workingDir'], downTup[3] ), noconfig=True)
								raise SystemExit
	def save(self):
		fd = codecs.open(self.filename, 'w', 'utf-8')
		fd.write("%s%s" %('[global]', os.linesep))
		keys = self['global'].keys()
		keys.sort()
		for key in keys:
			# rss option deprecated
			if key == 'rss': continue
			fd.write("%s = %s%s" % (key, str(self['global'][key]), os.linesep))
		fd.write(os.linesep)
		threads = self['threads'].keys()
		threads.sort()
		for thread in threads:
			fd.write("[%s]%s" % (thread, os.linesep))
			threadKeys = self['threads'][thread].keys()
			threadKeys.sort()
			for threadKey in threadKeys:
				downNum = 1
				checkNum = 1
				if 'download' in threadKey:
					if len(self['threads'][thread][threadKey]) == 0 : continue
					for downTup in self['threads'][thread][threadKey]:
						fd.write('download%s = %s%s' % (downNum, str(downTup[0]), os.linesep))
						fd.write('download%sDir = %s%s' % (downNum, str(downTup[3]), os.linesep))
						fd.write('download%sFalse = %s%s' % (downNum, str(downTup[1]), os.linesep))
						fd.write('download%sTrue = %s%s' % (downNum, str(downTup[2]), os.linesep))
						downNum += 1
				elif 'checkTime' == threadKey:
					if len(self['threads'][thread][threadKey]) == 0: continue
					for checkTup in self['threads'][thread][threadKey]:
						# checkNum is the item number we started on
						fd.write('checkTime%sDay = %s%s' % (checkNum, self.dayList[checkTup[0]], os.linesep))
						fd.write('checkTime%sStart = %s%s' % (checkNum, str(checkTup[1]), os.linesep))
						fd.write('checkTime%sStop = %s%s' % (checkNum, str(checkTup[2]), os.linesep))
						checkNum += 1
				else:
					fd.write('%s = %s%s' % (threadKey, str(self['threads'][thread][threadKey]), os.linesep))
			fd.write(os.linesep)
		fd.close()



# # # # #
# User/InterProcess Communication
# # # # #
class reFormatString:
	def __init__(self, inputstring=None, filename=None, linesep=os.linesep, lineLength=None, indent=' '*4, comment=None):
		if not inputstring and not filename: raise Exception, "must provide at least a filename or inputstring"
		elif inputstring and filename: raise Exception, "cannot provide a filename and inputstring, only one or the other"
		if inputstring: self.inputstring = inputstring
		elif file:
			fd = codecs.open(filename, 'r', 'utf-8')
			self.inputstring= fd.read()
			fd.close()
			del fd
		else: self.inputstring = None
		self.linesep = linesep
		#try:	self.lineLength = int( os.popen( 'tput cols').read() )
		try: self.lineLength = int(os.popen('stty size').read().split()[1])
		except: self.lineLength = 80
		self.indent= indent
		self.comment = None
		lines = self.inputstring.splitlines()
		outList = []
		for line in lines:
			lineText = line.lstrip()
			indentLine = self.getIndent( line )
			indentNum = self.getNumIndent( indentLine, indent=self.indent )
			newLines = self.produceLinesWithOutIndents( lineText, indentNum, len(self.indent), lineLength=self.lineLength )
			outList.extend( self.addIndentToLines(newLines, self.indent, indentNum ) )
		self.outString = self.linesep.join(outList)
	def __str__(self):
		return self.outString
	def delString(self, string, start, stop=None):
		"""feed me a string and an index number, with an optional stop number, and i will return with those."""
		if stop == None: stop = start +1
		retStr = string[:start]
		retStr += string[stop:]
		return retStr
	def getIndent(self, aStr ):
		indentLine = ''
		for i in xrange( len(aStr) ):
			if aStr[i].isspace(): 	indentLine += aStr[i]
			else: break
		return indentLine
	def getNumIndent(self, indentLine, indent=' '*4 ):
		indentNum = 0
		if not indentLine: return indentNum
		indentNum = indentLine.count('\t')
		for i in xrange(indentLine.count('\t')):
			indentLine = self.delString(indentLine, indentLine.index('\t') )
		while indentLine:
			if indentLine.startswith(indent):
				indentNum += 1
				indentLine = self.delString( indentLine, 0, len(indent) )
			# string still exists, no tabs, no newlines (we got rid of those with the splitlines), and not enough spaces to form a full indent, so assume one exists and add it, then break out of the loop
			else:
				indentNum += 1
				break
		return indentNum
	def produceLinesWithOutIndents(self, lineText, indentNum, indentLength, lineLength=80 ):
		TextAllowed = lineLength - ( indentNum*indentLength )
		if len(lineText) < TextAllowed: 
			return [ lineText ]
		newLines = []
		firstRunBreak = True
		while lineText:
			if len(lineText) < TextAllowed: 
				newLines.append( lineText )
				break
			for pos in xrange(TextAllowed, -1, -1):
				if lineText[pos] != ' ': continue
				lineBreakNum = pos
				break
			else: lineBreakNum = TextAllowed
			newLines.append( lineText[:lineBreakNum] )
			lineText = lineText[lineBreakNum:]
			if firstRunBreak: 
				TextAllowed -= indentLength
				firstRunBreak = False
		return newLines
	def addIndentToLines(self, lineList, indent, indentNum):
		returnList = []
		firstRunBuild = True
		for addLine in lineList:
			if firstRunBuild:
				returnList.append( indent*indentNum + addLine )
				firstRunBuild = False
				continue
			returnList.append( indent*(indentNum + 1 ) + addLine )
		return returnList
class Log:
	def __init__(self):
##		if not getConfig()['global']['log']: return None
		self.fd = codecs.open( getConfig()['global']['logFile'], 'a', 'utf-8')
	def write(self, message):
		timeCode = "[%4d%02d%02d.%02d:%02d]" % time.localtime()[:5]
		message = timeCode + os.linesep + message + os.linesep
		self.fd.write( unicode( message ) )
	def flush(self):
		self.fd.flush()

def logMsg( msg='', close=False, error=False ):
	"""Do not call directly with error=True. Use errorMsg for that """
	global _log
	if not getConfig()['global']['log'] and not error: return None
	if not _log: _log = Log()
	if msg: _log.write(  msg  )
	if close: 
		_log.flush()
		_log = None
		return None

def logStatusMsg( msg ):
	logMsg( msg )
	status( msg )

def errorMsg( msg, noconfig=False ):
	if noconfig:	
		sys.stderrUTF.write( str(reFormatString( inputstring=msg)) + os.linesep )
		return None
	if getConfig()['global']['error'] <= 0: return None
	if getConfig()['global']['error'] == 1 or getConfig()['global']['error'] >=3: status( msg, error=True )
	if getConfig()['global']['error'] == 2 or getConfig()['global']['error'] >= 3: logMsg( msg, error=True )

class SharedData:
	"""Mechanism for sharing data. Do not instantiate directly,
	use getSharedData() instead."""
	def __init__( self ):
		self.scanning = False	# True when scan in progress
		self.scanoutput = ""	# output of last scan
		self.exitNow = False	# should exit immediatley if this is set

def getSharedData():
	"""Return a shared instance of SharedData(), creating one if neccessary. Truncates if necessary."""
	global _sharedData
	if not _sharedData:
		_sharedData = SharedData()
	if len(_sharedData.scanoutput) > 2000:
		# don't want to just keep adding to this. Make a cutoff at somepoint. This seems reasonable. Think about this more.
		maxLength = len(_sharedData.scanoutput) - 1500
		_sharedData.scanoutput = _sharedData.scanoutput[maxLength : ]
	return _sharedData

def status( message, error=False ):
	"""Log status information, writing to stdout if config 'verbose' option is set. Do not call with error=True. Use errorMsg() to do that."""
	sharedData = getSharedData()
	if error: 
		sys.stderrUTF.write( str( reFormatString(message) ) + os.linesep )
		sys.stderrUTF.flush()
	elif getConfig()['global']['verbose']:
		sys.stdoutUTF.write( str( reFormatString(message) )  + os.linesep )
		sys.stdoutUTF.flush()
	sharedData.scanoutput += message + os.linesep

def getVersion():
        global _VERSION
        return _VERSION

def killDaemon( pid ):
	while True:
		saved = SaveProcessor()
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
##			 os.chdir(getConfig()['global']['workingDir'])
			# we should already be here...
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
	
	try: codecs.open( os.path.join(getConfig()['global']['workingDir'], getConfig()['global']['daemonInfo']), 'w', 'utf-8').write(procParams + "\n")
	except Exception, m: 
		errorMsg( str(m) + os.linesep + "Could not write to, or not set, daemonInfo" )
		raise SystemExit

def signal_handler(signal, frame):
	while True:
		s = SaveProcessor()
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
	global saved, config, rss, downloader
	config = getConfig(filename=configFile, reload=True)
	if getConfig()['global']['urllib']: downloader  = urllib2RetrievePage
	else: downloader = mechRetrievePage
	saved = SaveProcessor(getConfig()['global']['saveFile'])
	try:
		saved.lock()
	except Locked:
		raise Warning, "Savefile is currently in use."
	try: saved.load()
	except Exception, m: errorMsg(str(m) + os.linesep + "didn't load SaveProcessor")
	if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): os.chdir(getConfig()['global']['workingDir'])
	if getConfig()['global']['runOnce']:
		if saved.lastChecked > ( int(time.time()) - (getConfig()['global']['scanMins']*60) ):
			raise Warning, "Threads have already been scanned."
	if saved.failedDown:
		status("Scanning previously failed downloads")
		for i in  xrange( len( saved.failedDown) - 1, -1, -1 ):
			status("  Attempting to download %s" % saved.failedDown[i][0] )
			if downloadFile( *saved.failedDown[i] ):
				status("  Success!")
				del saved.failedDown[ i ]
				saved.save()
			else:
				status("  Failure")
	status( "Scanning threads" )
	if getConfig()['global']['rssFeed']:
		if getConfig()['global']['rssFilename']:
			loadRss ={}
			loadRss['title'] = getConfig()['global']['rssTitle']
			loadRss['description'] = getConfig()['global']['rssDescription']
			loadRss['link'] = getConfig()['global']['rssLink']
			if os.path.isfile( getConfig()['global']['rssFilename'] ):
				rss = MakeRss(filename=getConfig()['global']['rssFilename'], parse=True)
				if rss.channelMeta['title'] != loadRss['title']: rss.channelMeta['title'] = loadRss['title']
				if rss.channelMeta['description'] != loadRss['description']: rss.channelMeta['description'] = loadRss['description']
				if rss.channelMeta['link'] != loadRss['link']: rss.channelMeta['link'] = loadRss['link']
			else:
				#is there a good reason to not just do this above?
				rss = MakeRss(channelMeta=loadRss)
	timeTuple = time.localtime().tm_wday, time.localtime().tm_hour
	for key in getConfig()['threads'].keys():
		if getConfig()['threads'][key]['active'] == False:	continue	# ignore inactive threads
		# if they specified a checkTime value, make sure we are in the specified range
		if len(getConfig()['threads'][key]['checkTime']) != 0:
			toContinue = True
			for timeCheck in getConfig()['threads'][key]['checkTime']:
				timeLess = timeCheck[0], timeCheck[1]
				timeMore = timeCheck[0], timeCheck[2]
				if timeLess <= timeTuple <= timeMore:
					toContinue = False
					break
			if toContinue: continue
		if saved.minScanTime.has_key(key) and saved.minScanTime[key][0]  > ( int(time.time()) - saved.minScanTime[key][1]*60 ):
				status("""RSS feed "%s" has indicated that we should wait greater than the scan time you have set in your configuration. Will try again at next configured scantime""" % key)
				continue
		status( "   * finding new downloads in thread %s" % key )
		if getConfig()['threads'][key]['noSave'] == True:
			status( "     (not saving to disk)")
		try: config['threads'][key] = rssparse(getConfig()['threads'][key], threadName=key)	
		except IOError, ioe: raise Fatal, "%s: %s" % (ioe.strerror, ioe.filename)
	if rss:
		rss.close(length=getConfig()['global']['rssLength'])
		rss.write(filename=getConfig()['global']['rssFilename'])
	saved.lastChecked = int(time.time()) -30
	saved.save()
	saved.unlock()
	logMsg(close=1)

def main( runOnce=False ):
	config = getConfig(filename=configFile)
	sharedData = getSharedData()
	sharedData.scanoutput = ""
	if not runOnce:
		runOnce = getConfig()['global']['runOnce']
	while True:
		try:
			sharedData.scanoutput += os.linesep * 2
			sharedData.scanning = True
			status( "[Waking up] %s" % time.asctime() )
			startTime = time.time()
			run()
			status( "Processing took %d seconds" % (time.time() - startTime) )
		except Warning, message:
			errorMsg( u"Warning: %s" % str(message) )
		except Fatal, message:
			errorMsg( u"Error: %s" % str(message) )
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
		if  getConfig()['global']['scanMins'] * 60 < time.time() - saved.lastChecked: checkSleep ( getConfig()['global']['scanMins'] * 60 - elapsed )
		else: checkSleep( getConfig()['global']['scanMins'] * 60 )
	
	

#if we lock saved before calling kill, it will be locked and we will never get to an unlock state which is our indicator that it is ok to kill.
if __name__ == '__main__':
	try: 
		(argp, rest) =  getopt.gnu_getopt(sys.argv[1:], "drokc:hf", longopts=["daemon", "run", "runonce", "kill", "config=", "help", "failed"])
	except	getopt.GetoptError:
			sys.stderrUTF.write(helpMessage)
			sys.exit(1)
	
	for param, argum in argp:
		if param == "--daemon" or param == "-d":	action = "daemon"		
		elif param == "--run" or param == "-r": action = "run"
		elif param == "--runonce" or param == "-o":
			action = "run"
			runOnce = True
		elif param == "--kill" or param == "-k":
			action = "kill"
		elif param == "--config" or param == "-c": configFile = argum
		elif param == "--failed" or param == "-f": action="failed"
		elif param == "--help" or param == "-h": 
			print reFormatString(inputstring=helpMessage)
			sys.exit()
	
	if action == "kill":
		config = getConfig(filename=configFile, reload=True)
		killData = codecs.open(os.path.join(getConfig()['global']['workingDir'], getConfig()['global']['daemonInfo']), 'r', 'utf-8')
		for pidWanted in killData.readlines():
			pidWanted = pidWanted.strip()
			if pidWanted.startswith('process ID ='):
				pid = int(pidWanted.split('=')[-1].strip())
				break
		killDaemon(pid)
		codecs.open(os.path.join(getConfig()['global']['workingDir'], getConfig()['global']['daemonInfo']), 'w', 'utf-8').write('')
		sys.exit()
	if action == "run":
		config = getConfig(filename=configFile, reload=True)
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): os.chdir(getConfig()['global']['workingDir'])
		status( "--- RssDler %s" % getVersion() )
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
		config = getConfig(filename=configFile, reload=True)
		status( "--- RssDler %s" % getVersion() )
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): os.chdir(getConfig()['global']['workingDir'])
		callDaemon()
	##	import signal
	##	signal.signal(signal.SIGINT, signal_handler)
		main()
	elif action == "failed":
		config = getConfig(filename=configFile, reload=True)
		while 1:
			saved = SaveProcessor( getConfig()['global']['saveFile'] )
			try: 
				saved.lock()
				saved.load()
			except: 
				del saved
				time.sleep(3)
				continue
			while saved.failedDown:
				saved.downloads.append( saved.failedDown.pop()[0] )
				failMessage = 'removed %s from failed queue' % saved.downloads[-1]
				logMsg( failMessage )
				status( failMessage )
			break
		saved.save()
		saved.unlock()
		sys.exit()
