#!/usr/bin/env python
# -*- coding: utf-8 -*-

copyright = u"""RSSDler - RSS Broadcatcher
Copyright (C) 2007, lostnihilist

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; under version 2 of the license.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details."""

import feedparser
try: from BitTorrent.bencode import bdecode
except ImportError: from bencode import bdecode
import time, os, socket, cgi, codecs, cookielib, re, urllib, urllib2, mimetypes, urlparse, httplib
import pickle, copy, getopt, sys, ConfigParser
from UserDict import UserDict
# fixes import error when symlink to RSSDler is used.
if not sys.path.count(''): sys.path.insert(0, '')

# # # # #
# == Globals ==
# # # # #
downloader = None
mechanize = None
minidom = None
PrettyPrint = None
userFunctions = None
_VERSION = u"0.3.1"
_USER_AGENT = u"RSSDler %s" % _VERSION
_configInstance = None
_sharedData = None
_log = None
_action = None
_runOnce = None
configFile = u"""config.txt"""
cj = None
rss = None
saved = None
opener = None
config = None
UMASK = 0077
MAXFD = 1024
utfWriter = codecs.getwriter( "utf-8" )
sys.stdoutUTF = utfWriter( sys.stdout, "replace" )
sys.stderrUTF = utfWriter( sys.stderr, "replace" )
percentQuoteDict = {u'!': u'%21', u' ': u'%20', u'#': u'%23', u'%': u'%25', u'$': u'%24', u"'": u'%27', u'&': u'%26', u')': u'%29', u'(': u'%28', u'+': u'%2B', u'*': u'%2A', u',': u'%2C', u'=': u'%3D', u'@': u'%40', u';': u'%3B', u':': u'%3A', u']': u'%5D', u'[': u'%5B', u'?': u'%3F'}
percentunQuoteDict = dict(map(lambda x: (x[1],x[0]), percentQuoteDict.iteritems() ))

commentConfig = u"""# lines (like this one) starting with # are comments and will be ignored by the config parser
# the only required section (though the program won't do much without others)
# sections are denoted by a line starting with [
# then the name of the section, then ending with ]
# so this is the global section
[global]
# download files to this directory. Defaults to the working directory.
downloadDir = /home/user/downloads

# makes this the 'working directory' of RSSDler. anytime you specify a filename without an absolute path, it will be relative to this 
workingDir = /home/user/.rssdler

# if a file is smaller than this, it will not be downloaded. if filesize cannot be determined, this is ignored. 
# Specified in MB. Remember 1024 MB == 1GB
# 0 means no minimum, as does "None" (w/o the quotes)
minSize = 10

# if a file is larger than this, it will not be downloaded.  Default is None
# though this line is ignored because it starts with a #
# maxSize = None

# write messages to a log file. 0 is off, 1 is just error messages, 3 is quite wordy, 5 is very, very wordy. (default = 0)
log = 0
# where to write those log messages (default 'downloads.log')
logFile = downloads.log

# like log, only prints to the screen (errors to stderr, other to stdout)
# default 3
verbose = 3

# the place where a cookie file can be found. Default None.
cookieFile = /home/user/.mozilla/firefox/user/cookies.txt

# type of cookie file to be found at above location. default MozillaCookieJar
cookieType = MozillaCookieJar
# other possible types are:
# cookieType = LWPCookieJar
# only works if urllib = False
# cookieType = MSIECookieJar

#how long to wait between checking feeds (in minutes). Default 15.
scanMins = 10

# how long to wait between http requests (in seconds). Default 0
sleepTime = 2

# to exit after scanning all the feeds, or to keep looping. Default False.
runOnce = True

# set to true to avoid having to install mechanize. side effects described in help. Default False.
urllib = True

# the rest of the global options are described in the help, let's move on to a thread

###################
# each section represents a feed, except for the one called global. 
# this is the thread: somesite
###################
[somesite]
# just link to the feed
link = http://somesite.com/rss.xml

# Default None, defers to maxSize in global, otherwise,
# files larger than this size (in MB) will not be downloaded
# only applies to the specific thread
# if set to 0, means no maximum and overrides global option
maxSize = 2048

# like maxSize, only file smaller than this will not be downloaded
# if set to 0, means no minimum, like maxSize. in MB.
minSize = 10

# if specified, will download files in this thread to this directory
directory = /home/user/someotherfiles

# if you do not know what regular expressions are, stop now, do not pass go, do not collect USD200 (CAN195)
# google "regular expressions tutorial" and find one that suits your reading level
# one with an emphasis on Python may be to your advantage

# Now, without any of the download<x> or regEx options (detailed below)
# every item in the rss feed will be downloaded, provided that it has not previously been downloaded
# all the regular expression should be specified in lower case 
# (except for character classes and other special regular expression characters, if you know what that means)
# as the string that it is searched against is set to lower case.
# Starting with regExTrue (RET)
# let's say we want to make sure there are two numbers, separated by something not a number
# for everything we download in this thread.
regExTrue = \d[^\d]+\d
# the default value, None, makes RET ignored
# regExTrue = None

# but we want to make sure we don't download anything with nrg in the name or ccd
# because those are undesirable formats, but we want to make sure to not match
# a name that may have those as a substring e.g. enrgy 
# (ok, not a great example, come up with something better and I'll include it)
# REF from now on (\b indicates a word boundary)
regExFalse = (\bnrg\b|\bccd\b)
# the default value, which means it will be ignored
# regExFalse = None

# at this point, as long as the file gets a positive hit in RET and no hit in REF, the file will be downloaded
# equivalently said, RET and REF are necessary and sufficient conditions for a download.
# lengthy expressions can be constructed to deal with every combination of things you want, but there is 
# a looping facility to allow us to get more fine grained control over the items we want to grab
# without having to have hundreds of characters on a single line, which of course gets rather unreadable

# making use of this looping facility makes RET and REF neccessary (though that can be bypassed too, more later) conditions
# however, they are no longer sufficient....
# download<x> is like regExTrue, but begins the definition of an 'item' and we can associate further actions with it
# if we so choose
# put a non-negative integer where <x> goes
download1 = ubuntu
# but say we love ubuntu, and want to always grab everything that mentions it
# so we want to ignore regExTrue, this 'bypasses' RET when set to False. Default True.
download1True = False

# we could also bypass REF. but we really don't like nrg, but we'll deal with ccd's, just for ubuntu
# to be clear, download<x>False is a mixed type option, taking both True, False for dealing with the global REF 
# or a string (like here) to specify what amounts to a 'localized REF', which effectively says False to the global REF
# while at the same time specifying the local REF
download1False = \bnrg\b

# we don't want to download things like howto, md5 files, etc, so we can set a minSize (MB)
# this overrides the global/thread minSize when not set to None
# Default None. works like thread-based minSize. a maxSize option is also available
download1MinSize = 10
download1MaxSize = 750

# and finally, we can put our ubuntu stuff in a special folder, if we choose
download1Dir = /home/user/ubuntustuff

# note that the numbers are not important, as long as the options correspond to each other
# thas ,s, there is no download2, and that is ok.
download3 = fedora

# you have to have the base setting to have the other options
# will not work b/c download3 is not specified
# download4Dir = /home/user/something
"""
configFileNotes = u"""There are two types of sections: global and threads. There can be as many thread sections as you wish, but only one global section. global must be named "global." Threads can be named however you wish, except 'global,' and each name should be unique. With a couple of noted exceptions, there are three types of options:
	
Boolean Options: 'True' is indicated by "True", "yes", or "1". "False" is indicated by "False", "no", or "0" (without the quotes)
Integer Options: Just an integer. 1, 2, 10, 1000, 2348. Not 1.1, 2.0, 999.3 or 'a'.
String Options: any string, should make sense in terms of the option being provided (e.g. a valid file/directory on disk; url to rss feed)

Required indicates RSSDler will not work if the option is not set. 
Recommended indicates that the default is probably not what you want. 
Optional indicates that circumstances such as use pattern, type of feed, etc. determine if/how it should be set.

Run with --comment-config to see what a configuration file would look like, comments and all."""
cliOptions = u"""Command Line Options:
	--config/-c can be used with all the options except --comment-config, --help, and --set-default-config. Otherwise, do not mix and match options
	--comment-config: Prints a commented config file to stdout. (hint: rssdler.py --comment-config > myConfigToEdit.txt)
	--help/-h: print the help message
	--run/-r: run according to the configuration file
	--runonce/-o: run only once then exit, otherwise according to the configuration file.
	--daemon/-d: run in the background, according to the configuration file (except sets verbose = 0, a note if you invoke Config.save in postDownloadFunction ) (Unix-like only)
	--kill/-k: kill the daemonized instance (Unix like only)
	--config/-c: specify a config file (default %s).
	--list-failed: Will list the urls of all the failed downloads
	--purge-failed: Use to clear the failed download queue. Use when you have a download stuck (perhaps removed from the site or wrong url in RSS feed) and you no longer care about RSSDler attempting to grab it. Will be appended to the saved download list to prevent readdition to the failed queue. Should be used alone or with -c/--config. Exits after completion.
	--list-saved: Will list everything that has been registered as downloaded
	--purge-saved: Clear the list of saved downloads
	--set-default-config: Edits rssdler.py to reset the default config to the path you specify. will have to reset after upgrading/overwriting the file. helps to not have to specify -c/--config each time you run. Advised only for single user systems/installs. Should be used alone. Exits after completion.
""" % configFile
contact = u"""lostnihilist <lostnihilist@gmail.com> or "lostnihilist" on #libtorrent@irc.worldforge.org"""
nonCoreDependencies = u"""Non-standard Python libraries used:
	mechanize: http://wwwsearch.sourceforge.net/mechanize/ (this can now be overridden by setting urllib = True in global options. See below for details.
	feedparser: http://www.feedparser.org/
	BitTorrent: http://www.bittorrent.com (the python reference client)
	instead of BitTorrent, you can also just save the module bencode in your python path as bencode.py (perhaps most conveniently  in your working directory aka where you store all your RSSDler related files). This seems to work best for Python 2.5 as many distros do not have BitTorrent in 2.5's path: http://cheeseshop.python.org/pypi/BitTorrent-bencode/
	For debian based distros: "sudo apt-get install python-feedparser python-mechanize bittorrent" """
securityIssues = u"""Security Note: 
	Prior to 0.2.4, there were several 'eval' statements in this program, which allowed running arbitrary code. Although removed, there is an attempt to import 'userFunctions' if you specify a postDownloadFunction in your configuration. Make sure only you have write permissions in the directory you run this from/what you set workingDir to so that userFunctions cannot be setup to run arbitrary code that you do not want running. Also make sure only you have write permissions to your configuration file. It would be wise to make a file userFunctions.py in your working directory to which only you have write access. I've also had reports of users running this as root. PLEASE do not do that. You shouldn't even be logging into your system as root, much less running programs meant for userland, especially when they are Internet facing."""


# # # # #
#Exceptions
# # # # #
class Fatal( Exception ): 
	def __init__(self, value=u"An error occurred and RSSDler does not know how to react" ):
		self.value = value
	def __str__(self):
		return repr( self.value)
	
class Warning( Exception ):
	def __init__(self, value=u"""An error occurred, but no action needs to be taken by the user at this time.""" ):
		self.value = value
	def __str__(self):
		return repr( self.value)
	
class Locked( Exception ):
	def __init__(self, value=u"""An attempt was made to lock() the savefile while it was already locked.""" ):
		self.value = value
	def __str__(self):
		return repr( self.value)

# # # # #
#Downloading
# # # # #
def xmlUnEscape( sStr, percent=1, percentunQuoteDict=percentunQuoteDict ):
	u"""xml unescape a string, by default also checking for percent encoded characters. set percent=0 to ignore percent encoding. 
	can specify your own percent quote dict (key, value) pairs are of (search, replace) ordering with percentunQuoteDict.
	Unicode safe"""
	if percent:	return feedparser.xml.sax.saxutils.unescape( sStr, percentunQuoteDict )
	else: return feedparser.xml.sax.saxutils.unescape( sStr )
	
def xmlEscape( sStr, percent=1, percentQuoteDict=percentQuoteDict ):
	u"""this does not function perfectly with percent=1 aka also doing percent encoding. trailing ; get converted to %3B. perhaps they should be? but not likely. 
	can specify your own percent quote dict (key, value) pairs are of (search, replace) ordering with percentQuoteDict.
	Unicode Safe."""
	if percent: return feedparser.xml.sax.saxutils.escape( sStr, percentQuoteDict )
	else: return feedparser.xml.sax.saxutils.escape( sStr )

def percentIsQuoted(sStr, testCases=percentQuoteDict.values()):
	u"""does not include query string or page marker (#) in detection. these seem to cause the most problems.
	Specify your own test values with testCases
	Unicode Safe
	Test cases:
	should return False
	http://www.google.com/search?num=50&hl=en&c2coff=1&safe=off&q=*nrg*&btnG=Search
	should return True
	http://links.jstor.org/sici?sici=0364-765X(198102)6%3A1%3C58%3AOAD%3E2.0.CO%3B2-C
	should return False
	%ab
	Original version worked mostly well: return '%' in aStr
	
	"""
	b = testCases
	for i in b:
		if sStr.count(i): return True
	else: return False

def percentNeedsQuoted(sStr, testCases=percentQuoteDict.keys()):
	u"""check to see if there is a character in the path part of the url that is 'reserved'
	Unicode Safe"""
	c = testCases
	# this is much more questionable
	for aStr in urlparse.urlparse(sStr)[:4]:
		for i in c:
			if aStr.count(i): return True
	else: return False

def percentUnQuote( sStr, percentunQuoteDict=percentunQuoteDict ):
	u"""percent unquote a string. will also unescape xml entities. should maybe just unquote the path? 
	Unicode Safe"""
	return feedparser.xml.sax.saxutils.unescape( sStr, percentunQuoteDict)

#NOT (necessarily) UNICODE SAFE in default mode
def percentQuote(sStr, urlPart=(2,), unicode=0, percentQuoteDict=percentQuoteDict):
	u"""quote the path part of the url. urlPart is a sequence of parts of the urlunparsed entries to quote
	NOT UNICODE SAFE?"""
	if unicode:
		return percentQuoteCustom( sStr, urlPart, percentQuoteDict )
	urlList = list( urlparse.urlparse(sStr) )
	for i in urlPart:
		urlList[i] = urllib.quote( urlList[i].encode('utf-8') )
	# unicode type, probably the join with the other unicode parts handles it
	return urlparse.urlunparse( urlList )

def percentQuoteCustom(sStr, urlPart=(2,), percentQuoteDict=percentQuoteDict ):
	u"""quote the path part of he url. urlPart is a sequence of parts of the urlunparsed entries to quote. should maintain unicodedness. maybe not as robust as urllib.quote. can specify your own percent quote dict (key, value) pairs are of (search, replace) ordering with percentQuoteDict
	Unicode Safe"""
	urlList = list( urlparse.urlparse(sStr) )
	for i in urlPart:
		aList = list( urlList[i] )
		for search, replace in percentQuoteDict.iteritems():
			index = 0
			for eachAppearance in xrange( aList.count(search) ):
				pos = aList.index(search, index)
				index = pos + 1
				aList[pos] = replace
		urlList[i] = u''.join(aList)
	return urlparse.urlunparse( urlList )

# uses percentQuote, make with unicode=1
def unQuoteReQuote( url, quote=1, unicode=0 ):
	u"""fix urls from feedparser. they are not always properly unquoted then unescaped. will requote by default"""
	logStatusMsg(u"unQuoteReQuote %s" % url, 5)
	if percentIsQuoted(url):		url = xmlUnEscape( url, 1 )
	else:	url = xmlUnEscape( url, 0 ) 
	if quote and not unicode: url = percentQuote( url )
	elif quote and unicode: url = percentQuote( url, unicode=1 )
	return url

# NOT UNICODE SAFE, pretty much b/c it is designed to encode to utf-8 for httplib
def encodeQuoteUrl( url, encoding='utf-8', unicode=0 ):
	u"""take a url, percent quote it, if necessary and encode the string to encoding, default utf-8"""
	logStatusMsg( u"encoding url %s" % url, 5)
	if not percentIsQuoted(url) and percentNeedsQuoted(url):
		logStatusMsg( u"quoting url: %s" % url, 5)
		url = percentQuote( url, unicode=unicode )
	try: url = url.encode(encoding)
	except UnicodeEncodeError, m: 
		logStatusMsg( unicode(m) + os.linesep + url, 1 )
		return None
	return url
	
def cookieHandler():
	u"""returns 0 if no cookie configured, 1 if cookie configured, 2 if cookie already configured (even if it is for a null value)
	I think Unicode Safe"""
	global cj
	returnValue = 2
	logStatusMsg(u"""testing cookieFile settings""", 5)
	if cj == 1: pass
	elif cj == None and not getConfig()['global']['cookieFile']: 
		logStatusMsg(u"""no cookies set""", 5)
		returnValue = 0
	elif getConfig()['global']['urllib'] and not isinstance(cj, (urllib2.cookielib.MozillaCookieJar, urllib2.cookielib.LWPCookieJar) ):
		logStatusMsg(u"""attempting to load cookie type: %s """ % getConfig()['global']['cookieType'], 5)
		cj = urllib2.cookielib.__getattribute__( getConfig()['global']['cookieType'] )()
		try: 
			cj.load(getConfig()['global']['cookieFile'])
			returnValue = 1
			logStatusMsg(u"""cookies loaded""", 5)
		except (cookielib.LoadError, IOError), m:
			logStatusMsg( unicode(m) + u' disabling cookies. To re-enable cookies, stop RSSDler, correct the problem, and restart.', 1)
			returnValue = 0
	elif not getConfig()['global']['urllib'] and not isinstance(cj, (mechanize.MozillaCookieJar, mechanize.LWPCookieJar, mechanize.MSIECookieJar) ):
		logStatusMsg(u"""attempting to load cookie type: %s """ % getConfig()['global']['cookieType'], 5)
		cj = mechanize.__getattribute__( getConfig()['global']['cookieType'] )()
		try: 
			cj.load(getConfig()['global']['cookieFile'])
			returnValue = 1
			logStatusMsg(u"""cookies loaded""", 5)
		except (mechanize._clientcookie.LoadError, IOError), m:
			logStatusMsg( unicode(m) + u' disabling cookies. To re-enable cookies, stop RSSDler, correct the problem, and restart.', 1)
			returnValue = 0
	return returnValue

def urllib2RetrievePage( url, txheaders=((u'User-agent', _USER_AGENT),)):
	u"""URL is the full path to the resource we are retrieve/Posting
	txheaders is a sequence of (field,value) pairs of any extra headers you would like to add
	"""
	global cj, opener
	txheadersEncoded = tuple( (x.encode('utf-8'), y.encode('utf-8') ) for x,y in txheaders )
	urlNotEncoded = url
	time.sleep( getConfig()['global']['sleepTime'] )
	url = encodeQuoteUrl( url , encoding='utf-8', unicode=0)
	if not url: 
		logStatusMsg(u"utf encoding and quoting url failed, returning false", 1 )
		return False
	cjR = cookieHandler()
	if cjR == 1:
		logStatusMsg(u"building and installing urllib opener with cookiefile", 5)
		opener = urllib2.build_opener (urllib2.HTTPCookieProcessor(cj) )
		urllib2.install_opener(opener)
	elif cjR == 0:
		logStatusMsg(u"building and installing urllib opener without cookiefile", 5)
		opener = urllib2.build_opener( )
		urllib2.install_opener(opener)
		cj = 1
	logStatusMsg(u"grabbing page at url %s" % urlNotEncoded, 5)
	return urllib2.urlopen( urllib2.Request(url, headers=dict(txheadersEncoded)) )

def mechRetrievePage(url, txheaders=(('User-agent', _USER_AGENT),), ):
	u"""URL is the full path to the resource we are retrieve/Posting
	txheaders: sequence of tuples of header key, value to manually add to the request object
	"""
	# this could be improved dramatically
	global cj, opener, mechanize
	try:
		if not mechanize: import mechanize
	except ImportError, msg:
		logStatusMsg( unicode(msg), 1 )
		raise SystemExit
	urlNotEncoded = url
	txheadersEncoded = tuple( (x.encode('utf-8'), y.encode('utf-8') ) for x,y in txheaders )
	time.sleep( getConfig()['global']['sleepTime'] )
	url = encodeQuoteUrl( url, encoding='utf-8', unicode=0 )
	if not url: 
		logStatusMsg(u"utf encoding and quoting url failed, returning false", 1 )
		return False
	cjR =  cookieHandler()
	if cjR == 1:
		logStatusMsg(u"building and installing mechanize opener with cookiefile", 5)
		opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cj), mechanize.HTTPRefreshProcessor(), mechanize.HTTPRedirectHandler(), mechanize.HTTPEquivProcessor())
		mechanize.install_opener(opener)
	elif cjR == 0:
		logStatusMsg(u"building and installing mechanize opener without cookiefile", 5)
		opener = mechanize.build_opener(mechanize.HTTPRefreshProcessor(), mechanize.HTTPRedirectHandler(), mechanize.HTTPEquivProcessor())
		mechanize.install_opener(opener)
		cj = 1
	logStatusMsg(u"grabbing page at url %s" % urlNotEncoded, 5)
	return mechanize.urlopen( mechanize.Request( url, headers=dict( txheadersEncoded ) ) )

def getFileSize( info, data=None ):
	u"""give me the HTTP headers (info) and, if you expect it to be a torrent file, the actual file, i'll return the filesize, of type None if not determined
	Unicode Safe"""
	logStatusMsg(u"determining size of file", 5)
	size = None
	if 'torrent' in info.gettype():
		# don't pretend we know the size when we don't, data separated so that we don't go to else when it is of type 'torrent'
		if data:
			try: tparse = bdecode(data)
			except ValueError, m:
				logStatusMsg( unicode( m ) + u"File was supposed to be torrent data, but could not be bdecoded, indicates it is not torrent data", 1 )
				raise Warning
			if tparse['info'].has_key('length'): size = int(tparse['info']['length'])
			elif tparse['info'].has_key('files'):
				size = int(0)
				for j in tparse['info']['files']:	size += int(j['length'])
	else:
		try: 
			if info.has_key('content-length'): size = int(info['content-length'])
		except ValueError:	pass # don't know it, out of options, just return None
	logStatusMsg(u"filesize seems to be %s" % size, 5)
	return size
	
def checkFileSize(size, threadName, downloadDict):
	u"""returns True if size is within size constraints specified by config file. False if not.
	takes the size (determined by getFileSize?) in bytes, threadName (to look in config), and downloadDict (parsed download<x> options).
	Unicode Safe"""
	returnValue = True
	logStatusMsg(u"checking file size", 5)
	if downloadDict['maxSize'] != None: maxSize = downloadDict['maxSize']
	elif getConfig()['threads'][threadName]['maxSize'] != None: maxSize = getConfig()['threads'][threadName]['maxSize']
	elif getConfig()['global']['maxSize'] != None: maxSize = getConfig()['global']['maxSize']
	else: maxSize = None
	if downloadDict['minSize'] != None: minSize = downloadDict['minSize']
	elif getConfig()['threads'][threadName]['minSize'] != None: minSize = getConfig()['threads'][threadName]['minSize']
	elif getConfig()['global']['minSize'] != None: minSize = getConfig()['global']['minSize']
	else: minSize = None
	if maxSize:
		maxSize = maxSize * 1024 * 1024
		if size > maxSize: 
			returnValue = False
	if minSize:
		minSize = minSize * 1024 * 1024
		if size <  minSize:
			returnValue = False
	if returnValue: logStatusMsg(u"size within parameters", 5)
	else: logStatusMsg(u"size outside parameters", 5)
	return returnValue

def getFilenameFromHTTP(info, url):
	u"""info is an http header from the download, url is the url to the downloaded file (responseObject.geturl() ). or not. the response object is not unicode, and we like unicode. So the original, unicode url may be passed.
	Unsure of Unicode Fitness"""
	filename = None
	logStatusMsg(u"determining filename", 5)
	if info.has_key('content-disposition') and info['content-disposition'].count('filename='):
			logStatusMsg(u"filename from content-disposition header", 5)
			# 10 = len(filename=")
			filename = info['content-disposition'][ info['content-disposition'].index('filename=') + 10:-1]
	if not filename: 
		logStatusMsg(u"filename from url", 5)
		# Tup[2] is the path
		filename = percentUnQuote( urlparse.urlparse( url )[2].split('/')[-1] )
	# get the file extension
	try: typeGuess = info.gettype()
	except: typeGuess = None
	typeGuess1 = mimetypes.guess_type(filename)[0]
	if typeGuess and typeGuess1 and typeGuess == typeGuess1: pass # we're good
	# trust server content-type over filename
	elif typeGuess:
		logStatusMsg(u"getting extension from content-type header", 5)
		fileExt = mimetypes.guess_extension(typeGuess)
		if fileExt:
			# sloppy filename guess, probably will never get hit
			if not filename: 
				logStatusMsg(u"never guessed filename, just setting it to the time", 5)
				filename = unicode( int(time.time()) ) + fileExt
			else: filename += fileExt
	# we don't really ever drop down to the typeGuess1 ( from the filename )
	# that's because if it exists, it's already in the filename and we don't need to add the extension
	elif not info.has_key('content_type'):
			msg = u"Proper file extension could not be determined for the downloaded file: %s you may need to add an extension to the file for it to work in some programs. It came from url %s. It may be correct, but I have no way of knowing due to insufficient information from the server." % (filename, url)
			logStatusMsg( msg, 1 )
	if not filename: 
		logStatusMsg('Could not determine filename for torrent from %s' % url, 1)
		return None
	return unicode( filename )

def downloadFile(url, threadName, rssItemNode, downloadDict):
	u"""tries to download data at URL. returns None if it was not supposed to, False if it failed, and a tuple of arguments for userFunct
	Seems to be Unicode Safe"""
	try: data = downloader(url)
	except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException), m: 
		logStatusMsg( unicode(m) + os.linesep + u'error grabbing url: %s' % url, 1 )
		return False
	dataPage = data.read()
	dataInfo = data.info()
	dataUrl = data.geturl()
	# could try to grab filename from ppage item title attribute, but this seems safer for file extension assurance
	# could use url from attempted grab, but it won't be properly encoded. when python network stuff works properly with unicode
	# use dataUrl here
	filename = getFilenameFromHTTP(dataInfo, url)
	if not filename: return False
	size = getFileSize(dataInfo, dataPage)
	# check size against configuration options
	if size and not checkFileSize(size, threadName, downloadDict): 
		# size is outside range, don't need the data, but want to report that we succeeded in getting data
		del data, dataPage, dataInfo
		return None
	if downloadDict['Dir']: directory = downloadDict['Dir']
	elif getConfig()['threads'][threadName]['directory']: directory = getConfig()['threads'][threadName]['directory']
	else: directory = getConfig()['global']['downloadDir']
	try: filename = writeNewFile( filename, directory, dataPage )
	except IOError: 
		logStatusMsg( u"write to disk failed", 1 )
		return False
	logStatusMsg( u"\tFilename: %s%s\tDirectory: %s%s\tFrom Thread: %s%s" % ( filename, os.linesep, directory, os.linesep, threadName, os.linesep ), 3 )
	if rss:
		logStatusMsg( u"generating rss item", 5)
		if rssItemNode.has_key('description'): description = rssItemNode['description']
		else: description = None
		if rssItemNode.has_key('title'): title = rssItemNode['title']
		else: title = None
		pubdate = time.strftime(u"%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
		itemLoad = {'title':title , 'description':description , 'pubDate':pubdate }
		rss.makeItemNode( itemAttr=itemLoad )
	userFunctArgs = directory, filename, rssItemNode, dataUrl, downloadDict, threadName 
	return userFunctArgs

def searchFailed(urlTest):
	u"""see if url is in saved.failedDown list
	Unicode safe"""
	global saved
	for failedItem in saved.failedDown:
		if urlTest == failedItem['link']: return True
	return False

def checkRegExGTrue(ThreadLink, itemNode):
	u"""return type True or False if search matches or no, respectively.
	Unicode Safe"""
	# [response from regExTrue, regExFalse, downloads, downloadFalse, downloadTrue]
	if ThreadLink['regExTrue']:
		logStatusMsg(u"checking regExTrue on %s" % itemNode['title'].lower(), 5)
		if ThreadLink['regExTrueOptions']: regExSearch = re.compile(ThreadLink['regExTrue'], re.__getattribute__(ThreadLink['regExTrueOptions']) )
		else: regExSearch = re.compile(ThreadLink['regExTrue'])
		if regExSearch.search(itemNode['title'].lower()): return True
		else: return False
	else: return True

def checkRegExGFalse(ThreadLink, itemNode):
	u"""return type True or False if search doesn't match or does, respectively.
	Unicode Safe"""
	if ThreadLink['regExFalse']:
		logStatusMsg(u"checking regExFalse on %s" % itemNode['title'].lower(), 5)
		if ThreadLink['regExFalseOptions']: regExSearch = re.compile(ThreadLink['regExFalse'], re.__getattribute__(ThreadLink['regExFalseOptions']) )
		else: regExSearch = re.compile(ThreadLink['regExFalse'])
		if regExSearch.search(itemNode['title'].lower()):	return False
		else: return True
	else: return True

def checkRegEx(ThreadLink, itemNode):
	u"""goes through regEx* and download<x> options to see if any of them provide a positive match. Returns False if Not. Returns a DownloadItemConfig dictionary if so
	Unicode Safe"""
	if ThreadLink['downloads']:
		# save this as a type. It will return a tuple. Check against tuple[0], return the tuple
		LDown = checkRegExDown(ThreadLink, itemNode)
		if LDown: 			return LDown
		else: 			return False
	elif checkRegExGFalse(ThreadLink, itemNode) and checkRegExGTrue(ThreadLink, itemNode): 		return DownloadItemConfig()
	else: 	return False

def checkRegExDown(ThreadLink, itemNode):
	u"""returns false if nothing found in download<x> to match itemNode. returns DownloadItemConfig instance otherwise
	Unicode Safe"""
	# Also, it's incredibly inefficient
	# for every x rss entries and y download items, it runs this xy times.
	# ( local true, 
	logStatusMsg(u"checking download<x>", 5)
	for downloadDict in ThreadLink['downloads']:
		if ThreadLink['regExTrueOptions']: LTrue = re.compile( downloadDict['localTrue'], re.__getattribute__(ThreadLink['regExTrueOptions']) )
		else: LTrue = re.compile(downloadDict['localTrue'])
		if not LTrue.search(itemNode['title'].lower()): continue
		if type(downloadDict['False']) == type(''):
			if ThreadLink['regExFalseOptions']: LFalse = re.compile(downloadDict['False'], re.__getattribute__(ThreadLink['regExFalseOptions']))
			else: LFalse = re.compile(downloadDict['False'])
			if LFalse.search(itemNode['title'].lower()): continue
		elif downloadDict['False'] == False: pass
		elif downloadDict['False'] == True:
			if not checkRegExGFalse(ThreadLink, itemNode): continue
		if downloadDict['True'] == True:
			if not checkRegExGTrue(ThreadLink, itemNode): continue
		elif downloadDict['True'] == False: pass
		return downloadDict
	return False

def rssparse(thread, threadName):
	u"""loops through the rss feed, searching for downloadable files"""
	ThreadLink = copy.deepcopy(thread)
	page = None
	try: page = downloader(ThreadLink['link'])
	except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException, ), m:	
		logStatusMsg( unicode(m) + os.linesep + u'error grabbing url %s' % ThreadLink['link'] , 1)
		return ThreadLink
	if not page: 
		logStatusMsg( u"failed to grab url %s" % ThreadLink['link'], 1)
		return ThreadLink
	try: ppage = feedparser.parse(page.read())
	# feedparser does not seem to throw exceptions properly, is a dictionary of some kind
	except Exception, m:
		logStatusMsg( unicode(m) + os.linesep + u"page grabbed was not a parseable rss feed", 1)
	if ppage['feed'].has_key('ttl') and ppage['feed']['ttl'] != '':
		logStatusMsg(u"setting ttl", 5)
		saved.minScanTime[threadName] = (time.time(), int(ppage['feed']['ttl']) )
	for i in range(len(ppage['entries'])):
		# deals with feedparser bug with not properly uri unquoting/xml unescaping links from some feeds
		ppage['entries'][i]['oldlink'] = ppage['entries'][i]['link']
		ppage['entries'][i]['link'] = unQuoteReQuote( ppage['entries'][i]['link'] )
		#if we have downloaded before, just skip (but what about e.g. multiple rips of about same size/type we might download multiple times)
		if ppage['entries'][i]['link'] in saved.downloads: 
			logStatusMsg(u"already downloaded %s" % ppage['entries'][i]['link'], 5)
			continue
		# if it failed before, no reason to believe it will work now, plus it's already queued up
		if searchFailed( ppage['entries'][i]['link'] ): 
			logStatusMsg(u"link was in failedDown", 5)
			continue
		# make sure it matches what we want
		dirDict = checkRegEx(ThreadLink, ppage['entries'][i])
		if not dirDict: continue
		# if we matched above, but don't want to download, register as downloaded, and then move on
		if ThreadLink['noSave']:  
			logStatusMsg( u"noSave triggered for %s" % ppage['entries'][i]['link'] , 5)
			saved.downloads.append(ppage['entries'][i]['link'] )
			continue
		userFunctArgs = downloadFile(ppage['entries'][i]['link'], threadName, ppage['entries'][i], dirDict)
		# size was inappropriate == None
		if userFunctArgs == None: continue
		# was supposed to download, but failed
		elif userFunctArgs == False:
			logStatusMsg(u"adding to failedDown: %s" % ppage['entries'][i]['link'] , 5)
			saved.failedDown.append( FailedItem(ppage['entries'][i]['link'], threadName, ppage['entries'][i], dirDict) )
		# should have succeeded
		elif userFunctArgs:
			logStatusMsg(u"adding to saved downloads: %s" % ppage['entries'][i]['link'] , 5)
			saved.downloads.append( ppage['entries'][i]['link'] )
			if getConfig()['threads'][threadName]['postDownloadFunction']: 
				callUserFunction( getConfig()['threads'][threadName]['postDownloadFunction'], *userFunctArgs )
		ThreadLink['noSave'] = False
	return ThreadLink

def writeNewFile(filename, directory, data):
	u"""write a file to disk at location. won't clobber, depending on config. writes to .__filename.tmp first, then moves to filename
	Unicode Safe"""
	# would be nice to scan filename for illegal characters, only that is file system dependent and rather sketchy
	if getConfig()['global']['noClobber']: 
		directory, filename = findNewFile( filename, directory)
		tmpPath = os.path.join( *findNewFile( u'.__' + filename + u'.tmp', directory) )
	else: tmpPath = os.path.join(directory, u'.__' +  filename + u'.tmp')
	realPath = os.path.join(directory, filename)
	try:
		logStatusMsg(u'opening %s' % tmpPath, 5)
		# open should handle unicode path automagically
		fd = open( tmpPath, 'wb')
		fd.write(data)
		fd.flush()
		fd.close()
	except IOError, m: 
		# should we only do this if noClobber is True?, should be pretty safe though..
		if os.path.isfile( tmpPath ): os.unlink(tmpPath)
		logStatusMsg( unicode(m) + u'Failed to write file %s in directory %s' % (filename, directory) , 1)
		raise IOError
	logStatusMsg(u'moving to %s' % realPath, 5)
	os.rename(tmpPath, realPath)
	return filename

def findNewFile(filename, directory):
	u"""find a filename in the given directory that isn't already taken. adds '.1' before the file extension, or just .1 on the end if no file extension
	Unicode Safe"""
	if os.path.isfile( os.path.join(directory, filename) ):
		logStatusMsg(u"filename already taken, looking for another: %s" % filename, 2)
		filenameList = filename.split('.')
		if len( filenameList ) >1: 
			try: 
				num = '.' + unicode( int( filenameList[-2] ) +1)
				del filenameList[-2]
				filename = '.'.join( filenameList[:-1] ) + num + '.' + filenameList[-1]
			except (ValueError, IndexError, UnicodeEncodeError): 
				try: 
					num = '.' + unicode( int( filenameList[-1] ) + 1 )
					del filenameList[-1]
					filename = '.'.join( filenameList ) + num
				except (ValueError, IndexError, UnicodeEncodeError) : 
					num = '.' + unicode( 1 )
					filename = '.'.join( filenameList[:-1] ) + num + '.' + filenameList[-1]
		else: filename += u'.1'
		return findNewFile( filename, directory )
	else: return directory, filename

# # # # #
#Persistence
# # # # #
class FailedItem(UserDict):
	u"""represents an item that we tried to download, but failed, either due to IOError, HTTPError, or some such"""
	def __init__(self, link, threadName, rssItemNode, downItemConfig):
		u"""upgrade note: [0] = link, [1] = threadName, [2] = itemNode, [3] = downloadLDir"""
		UserDict.__init__(self)
		self['link'] = link
		self['threadName'] = threadName
		self['rssItemNode'] = rssItemNode
		self['downItemConfig'] = downItemConfig
	def returnTuple(self):
		u"""allows us to be sure the ordering is proper .values() won't do that. """
		return ( self['link'], self['threadName'], self['rssItemNode'], self['downItemConfig'] )
		
class DownloadItemConfig(UserDict):
	u"""downloadDict: a dictionary representing the download<x> options. keys are: 'localTrue' (corresponding to download<x>) ; 'False' ; 'True' ; 'Dir' ; 'minSize' ; and 'maxSize' corresponding to their analogues in download<x>.
	Unicode Safe"""
	def __init__(self, regextrue=None, dFalse=True, dTrue=True, dir=None, minSize=None, maxSize=None):
		u"was [0] = localTrue, [1] = False, [2] = True, [3] = dir"
		UserDict.__init__(self)
		self['localTrue'] = regextrue
		self['False'] = dFalse
		self['True'] = dTrue
		self['Dir'] = dir
		self['minSize'] = minSize
		self['maxSize'] = maxSize

class MakeRss:
	u"""returns an xml document  in line with the rss2.0 specification.
	rss = MakeRss()
	rss......
	rss.appendItemNodes()
	rss.close()
	rss.write()
	"""
	def __init__(self, channelMeta={}, parse=False, filename=None):
		global PrettyPrint, minidom
		try:
			if not minidom: from xml.dom import minidom
		except ImportError, m:
			logStatusMsg(unicode(m), 1 )
			raise ImportError
		try:
			if not PrettyPrint: from xml.dom.ext import PrettyPrint
		except ImportError: PrettyPrint = self._write
		self.chanMetOpt = ['title', 'description', 'link', 'language', 'copyright', 'managingEditor', 'webMaster', 'pubDate', 'lastBuildDate', 'category', 'generator', 'docs', 'cloud', 'ttl', 'image', 'rating', 'textInput', 'skipHours', 'skipDays']
		self.itemMeta = ['title', 'link', 'description', 'author', 'category', 'comments', 'enclosure', 'guid', 'pubDate', 'source']
		self.feed = minidom.Document()
		self.rss = self.feed.createElement('rss')
		self.rss.setAttribute(u'version', u'2.0')
		self.channel = self.feed.createElement('channel')
		self.channelMeta = channelMeta
		self.filename = filename
		self.items = []
		if parse == True: self.parse()
	def loadChanOpt(self):
		if not self.channelMeta.has_key('title') or not self.channelMeta.has_key('description') or not self.channelMeta.has_key('link'):
			raise Exception, u"channelMeta must specify at least 'title', 'description', and 'link' according to RSS2.0 spec. these are case sensitive"
		for key in self.chanMetOpt:
			if self.channelMeta.has_key(key):
				chanMet = self.makeTextNode(key, self.channelMeta[key])
				self.channel.appendChild(chanMet)
	def makeTextNode(self, nodeName, nodeText, nodeAttributes=[]):
		u"""returns an xml text element node, with input being the name of the node, text, and optionally node attributes as a sequence
		of tuple pairs (attributeName, attributeValue)
		"""
		node = self.feed.createElement(nodeName)
		text = self.feed.createTextNode(unicode(nodeText))
		node.appendChild(text)
		if nodeAttributes:
			for attribute, value in nodeAttributes: 
				node.setAttribute(attribute, value)
		return node
	def makeItemNode(self, itemAttr={}, action='insert'):
		u"""action: 
			insert: put at 0th position in list
			append: tack on to the end of list
			return: do not attach to self.items at all, just return the XML object.
		"""
		global time, random
		try:
			if time: pass
		except NameError: import time
		try:
			if random: pass
		except NameError:
			import random
		u"""should have an item "child" we will be adding to that"""
		if 'title' in itemAttr.keys() or 'description' in itemAttr.keys(): pass
		else:	raise Exception, u"must provide at least a title OR description for each item"
		if 'pubdate' not in itemAttr.keys() and 'pubDate' not in itemAttr.keys():
			if itemAttr.has_key('updated_parsed'): 
				itemAttr['pubDate'] = itemAttr['pubdate'] = time.strftime(u"%a, %d %b %Y %H:%M:%S GMT", itemAttr['updated_parsed'])
			elif itemAttr.has_key('updated'): itemAttr['pubDate'] = itemAttr['pubdate'] = itemAttr['updated']
			else: itemAttr['pubDate'] = itemAttr['pubdate'] = time.strftime(u"%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
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
		else: raise Exception, u"Illegal value for action, must be insert, append, or return"
	def appendItemNodes(self, length=20, pop=False):
		u"""adds the items in self.items to self.channel. if pop is True, each item is removed as it is added to channel. starts at the front of the list"""
		if pop:
			if length: del self.items[length:]
			while self.items:	self.channel.appendChild( self.items.pop(0) )
		else:
			if length: appendItems = self.items[:length]
			else: appendItems = self.items
			for item in appendItems: self.channel.appendChild( item )
	def close(self, length=20, pop=False):
		self.loadChanOpt()
		self.appendItemNodes(length=length, pop=pop)
		self.rss.appendChild(self.channel)
		self.feed.appendChild(self.rss)
	def parse(self, filename=None, rawfeed=None, parsedfeed=None, itemsonly=False):
		u"""give parse a raw feed (just the xml/rss file, unparsed) and it will fill in the class attributes, and allow you to modify the feed.
		Or give me a feedparser.parsed feed (parsedfeed) and I'll do the same"""
		global feedparser, time
		try:
			if time: pass
		except NameError: import time
		try:
			if feedparser: pass
		except NameError: import feedparser
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
		else: raise Exception, u"Must give either a rawfeed, filename, set self.filename, or parsedfeed"
		if not itemsonly:
			if p['feed'].has_key('updated'): p['feed']['pubDate'] = p['feed']['pubdate']  = p['feed']['updated']
			elif p['feed'].has_key('updated_parsed'): 
				p['feed']['pubDate'] = p['feed']['pubdate']  = time.strftime(u"%a, %d %b %Y %H:%M:%S GMT", p['feed']['updated_parsed'])
			self.channelMeta = p['feed']
		for entry in p['entries']:	self.makeItemNode(itemAttr=entry, action='append')
	def _write(self, data, fd):
		fd.write( data.toprettyxml() )
		fd.flush()
	def write(self, filename=None, file=None):
		u"""if fed filename, will write and close self.feed to file at filename.
		if fed file, will write to file, but closing it is up to you"""
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
	u"""	downloadDir: [Recommended] A string option. Default is current directory. Set to a directory in which you have write permission where downloaded files will go.
	workingDir: [Recommended] A string option. Default is current directory. Only needed with -d. Set to a directory on disk. Useful to make sure you don't run this from a partition that might get unmounted. If you use the -d switch (to run as a deamon) you must have this set or the program will die.
	minSize: [Optional] An integer option. Default None. Specify, in MB, the minimum size for a download to be. Files less than this size will not be saved to disk.
	maxSize: [Optional] An integer option. Default None. Specify, in MB, the maximum size for a download to be. Files greater than this size will not be saved to disk.
	log: [Optional] An integer option. Default 0. Will write meassages a log file (specified by logFile). See verbose for what options mean.
	logFile: [Optional] A string option. Default downloads.log. Specify a file on disk to write the log to.
	verbose: [Optional] An integer option, defaulting to 3. Lower numbers mean less output. 5 is absurdly verbose, 1 is major errors only. Set to 0 to disable all output.  Errors go to stderr, others go to stdout.
	cookieFile: [Optional] A string option. Default 'None'. The file on disk, in Netscape Format (requires headers) that has cookie information for whatever site(s) you have set that require it.
	cookieType: [Optional] A string option. Default 'MozillaCookieJar.' Possible values (case sensitive): 'MozillaCookieJar', 'LWPCookieJar', 'MSIECookieJar'. only mechanize supports MSIECookieJar. Program will exit with error if you try to use urllib=True and MSIECookieJar.
	scanMins: [Optional] An integer option. Default 15. Values are in minutes. The number of minutes between scans. If a feed uses the <ttl> tag, it will be respected. That is, if you have scanMins set to 10 and the site sets <ttl>900</ttl> (900 seconds; 15 mins); then the feed will be scanned every other time. 
	sleepTime: [Optional] An integer option. Default 0. Values are in seconds. Amount of time to pause between fetches of urls. Some servers do not like when they are hit too quickly, causing weird errors (e.g. inexplicable logouts). Setting this to 1 or 2 can sometimes help prevent such errors.
	runOnce: [Optional] A boolean option, default False. Set to True to force RSSDler to exit after it has scanned the configured feeds.
	urllib: [Optional]. Boolean Option. Default False. Setting this to true removes the dependency on mechanize for those platforms where mechanize may not be available or may work improperly. You lose several pieces of functionality, however. 1) Referers will no longer work. On most sites, this will not be a problem, but some sites require referers and will deny requests if the referer is not passed back to the site. 2) Some sites have various 'refresh' mechanisms that may redirect you around before actually giving you the file to download. Mechanize has the ability to follow these sites.
	noClobber: [Optional]. Boolean. Default True. Setting this to False means that files downloaded with the same name/directory as a previous file, the previous file will get overwritten. When True, a number (starting with 1, if that's taken, then 2..) will be added at the end of the name before the extension. If no extension, appended to the end of the file.
	rssFeed: [Optional] Boolean Option. Default False. Setting this option allows you to create your own rss feed of the objects you have downloaded. It's a basic feed, likely to not include links to the original files. The related rss items (all are required if this is set to True):
	rssLength: [Optional]  Integer. Default 20. An integer. How many entries should the RSS feed store before it starts dropping old items. 0 means that the feed will never be truncated.
	rssTitle: [Optional] A string. Default "some RSS Title".  The title the rss feed will carry.
	rssLink: [Optional]   string: Default 'somelink.com/%%s' %% self['rssFilename']. Where the rss feed can be located. Typically an http link.
	rssDescription: [Optional] A string. Default "Some RSS Description". A short description of what the feed contains.
	rssFilename: [Optional] A string. Default 'rssdownloadfeed.xml'. Where to store the feed on disk.
	saveFile: [Optional] A string option. Default savedstate.dat. Specify a file on disk to write the saved state information to. This keeps track of previously downloaded files and other 'state' information necessary to keep the program running coherently, especially between shutdown/startup
	lockPort: [Optional] An integer option. Default 8023. The port on which the savedstate.dat file will be locked for writing. Necessary to maintain the integrity of the state information.
	daemonInfo: [Optional] A string option. Default daemon.info. Only needed with -d. Set to a file on disk. Daemon info will be written there so that -k and such will work.
	rss: DEPRECATED, will no longer be processed.
	error: DEPRECATED, wil no longer be processed. (yes, already)"""
	def __init__(self):
		UserDict.__init__(self)
		self['verbose'] = 3
		self['downloadDir'] = os.getcwd()
		self['runOnce'] = False
		self['maxSize'] = None
		self['minSize'] = None
		self['log'] = 0
		self['logFile'] = u'downloads.log'
		self['saveFile'] = u'savedstate.dat'
		self['scanMins'] = 15
		self['lockPort'] = 8023
		self['cookieFile'] = None
		self['workingDir'] = os.getcwd()
		self['daemonInfo'] = u'daemon.info'
		self['rssFeed'] = False
		self['rssDescription'] = u"Some RSS Description"
		self['rssFilename'] = u'rssdownloadfeed.xml'
		self['rssLength'] = 20
		self['rssLink'] = u'somelink.com/%s' % self['rssFilename']
		self['rssTitle'] = u"some RSS Title"
		self['urllib'] = False
		self['cookieType'] = 'MozillaCookieJar'
		self['sleepTime'] = 0
		self['noClobber'] = True

class ThreadLink(UserDict):
	u"""	link: [Required] A string option. Link to the rss feed.
	active:  [Optional] A boolean option. Default is True, set to False to disable checking of that feed.
	maxSize: [Optional] An integer option, in MB. default is None. A thread based maxSize like in global. If set to None, will default to global's maxSize. Other values override global, including 0 to indicate no maxSize.
	minSize: [Optional] An integer opton, in MB. default is None. A thread based minSize, like in global. If set to None, will default to global's minSize. Other values override global, including 0 to indicate no minSize.
	noSave: [Optional] A boolean option. Default to False. If true, will remember download objects for the save processor on run, but does not download. If set to True, Must be set to False manually.
	directory: [Optional] A string option. Default to None. If set, overrides global's downloadDir, directory to download download objects to.
	checkTime<x>Day: [Optional] A string option. Either the standard 3 letter abbreviation of the day of the week, or the full name. One of Three options that will specify a scan time. the <x> is an integer. Will only scan the rss feed during the day specified. Can Further curtail scan time with Start and Stop (see next).
	checkTime<x>Start: [Optional] An integer option. Default: 0. The hour (0-23) at which to start scanning on correlated day. MUST specify checkTime<x>Day.
	checkTime<x>Stop: [Optional] An integer option. Default 23. The hour (0-23) at which to stop scanning on correlated day. MUST specify checkTime<x>Day.
	regExTrue: [Optional] A string (regex) option. Default None. If specified, will only download if a regex search of the download name (title key in entry dictionary of feedparser instance) returns True. This will be converted to a python regex object. Use all lower case, as the name is converted to all lower case.
	regExTrueOptions: [Optional] A string option. Default None. Options (like re.IGNORECASE) to go along with regExTrue when compiling the regex object. IGNORECASE is unnecessary however.
	regExFalse: [Optional] A string (regex) option. Default None. If specified, will only download if a regex search of the download name returns False. This will be converted to a python regex object. Use all lower case, as the name is converted to all lower case.
	regExFalseOptions: [Optional] A string option. Default None. Options (like re.IGNORECASE) to go along with regExFalse when compiling the regex object
	postDownloadFunction: [Optional] A string option. Default None. The name of a function, stored in userFunctions.py found in the current working directory. Any changes to this requires a restart of RSSDler. calls the named function in userFunctions with arguments: directory, filename, rssItemNode, retrievedLink, downloadDict, threadName. Exception handling is up to the function, no exceptions are caught. Check docstrings (or source) of userFunctHandling and callUserFunction to see reserved words/access to RSSDler functions/classes/methods.
	The following options are ignored if not set (obviously). But once set, they change the behavior of regExTrue (RET) and regExFalse (REF). Without specifying these options, if something matches RET and doesn't match REF, it is downloaded, i.e. RET and REF constitute sufficient conditions to download a file. Once these are specified, RET and REF become necessary (well, when download<x>(True|False) are set to True, or a string for False) but not sufficient conditions for any given download. If you set RET/REF to None, they are of course ignored and fulfill their 'necessity.' You can specify these options as many times as you like, by just changing <x> to another number. 
	download<x>: [Optional] No default. This apparently  where <x> is an integer, this is a 'positive' hit regex. This is required for download<x>true and download<x>false.
	download<x>False: [Optional] Default = True. However, this is not strictly a boolean option. True means you want to keep regExFalse against download<x>. If not, set to False, and there will be no 'negative' regex that will be checked against. You can also set this to a string (i.e. a regex) that will be a negative regex ONLY for the corresponding download<x>. Most strings are legal, however the following False/True/Yes/No/0/1 are reserved words when used alone and are interpreted, in a case insensitive manner as Boolean arguments. Requires a corresponding download<x> argument.
	download<x>True. [Optional] A Boolean option. default True. True checks against regExTrue. False ignores regExTrue. Requires a corresponding download<x> argument.
	download<x>Dir. [Optional] A String option. Default None. If specified, the first of the download<x> tuples to match up with the download name, downloads the file to the directory specified here. Full path is recommended.
	download<x>MinSize. [Optional]. An Integer option. Default None. Analogous to minSize.
	download<x>MaxSize. [Optional]. An integer option. Default None. Analogous to maxSize.
	checkTime: DEPRECATED. Will no longer be processed.
	Programmers Note: 
		download<x>* stored in a DownloadItemConfig() Dict in .downloads. 
		checkTime* stored as tuple of (DoW, startHour, endHour)
	""" 
	def __init__(self, name=None, link=None, active=True, maxSize=None, minSize=None, noSave=False, directory=None, regExTrue=None, regExTrueOptions=None, regExFalse=None, regExFalseOptions=None, postDownloadFunction=None):
		UserDict.__init__(self)
		self['link'] = link
		self['active'] = active
		self['maxSize'] = maxSize
		self['minSize'] = minSize
		self['noSave'] = noSave
		self['directory'] = directory
		self['checkTime'] = []
		self['regExTrue'] = regExTrue
		self['regExTrueOptions'] = regExTrueOptions
		self['regExFalse'] = regExFalse
		self['regExFalseOptions'] = regExFalseOptions
		self['postDownloadFunction'] = postDownloadFunction
		self['downloads'] = []

class SaveInfo(UserDict):
	u"""lastChecked: when we last checked the rss feeds
downloads: list of urls to downloads that we have grabbed
minScanTime: if feed has <ttl>, we register that fact here in a dictionary with threadName as key, and scanTime information as values
failedDown: list of FailedItem instances to be re-attempted to download
version: specifies which version of the program this was made with"""
	def __init__(self, lastChecked=0, downloads=[]):
		UserDict.__init__(self)
		self['lastChecked'] = lastChecked
		self['downloads'] = downloads
		self['minScanTime'] = {}
		self['failedDown'] = []
		self['version'] = getVersion()

class SaveProcessor:
	def __init__(self, saveFileName=None):
		u"""saveFileName: location where we store persistence data
		lastChecked: seconds since epoch when we last checked the threads
		downloads: a list of download links, so that we do not repeat ourselves
		minScanTime: a dictionary, keyed by rss link aka thread name, with values of tuples (x,y) where x=last scan time for that thread,
			y=min scan time in minutes, only set if ttl is set in rss feed, otherwise respect checkTime and lastChecked
		failedDown: a list of tuples (item link, threadname, rssItemNode, localized directory to download to (None if to use global) ). 
		(ppage['entries'][i]['link'], threadName, ppage['entries'][i], dirTuple[1]) 
		This means that the regex, at the time of parsing, identified this file as worthy of downloading, but there was some failure in the retrieval process. Size will be checked against the configuration state at the time of the redownload attempt, not the size configuration at the time of the initial download attempt (if there is a difference)
		"""
		if saveFileName:	self.saveFileName = saveFileName
		else: self.saveFileName = getConfig()['global']['saveFile']
		self.lastChecked = 0
		self.downloads = []
		self.failedDown = []
		self.minScanTime = {}
		self.version = None
		self.lockSock = None
		self.lockedState = False
	def save(self):
		saveFile = SaveInfo()
		saveFile['lastChecked'] = self.lastChecked
		saveFile['downloads'] = self.downloads
		saveFile['minScanTime'] = self.minScanTime
		saveFile['failedDown'] = self.failedDown
		saveFile['version'] = self.version
		f = open(self.saveFileName, 'wb')
		pickle.dump(saveFile, f, -1)
	def load(self):
		u"""take care of conversion from older versions here, then call save to store updates, then continue with loading."""
		f = open(self.saveFileName, 'rb')
		saveFile = pickle.load(f)
		if not saveFile.has_key('version'): self.version = u'0.2.4'
		else: self.version = saveFile['version']
		self.lastChecked = saveFile['lastChecked']
		self.downloads = saveFile['downloads']
		self.minScanTime = saveFile['minScanTime']
		if self.version <= u'0.2.4':
			#upgrade from old versions routines here
			if len(saveFile['failedDown']) > 0 and not isinstance(saveFile['failedDown'][0], FailedItem):
				for link, threadName, itemNode, LDir  in saveFile['failedDown']:
					failureDownDict = DownloadItemConfig(None, None, None, LDir)
					self.failedDown.append( FailedItem( link, threadName, itemNode, failureDownDict ) )
				self.version = getVersion()
				self.save()
			# just here to be explicit about what we are doing
			if len(saveFile['failedDown']) > 0 and isinstance(saveFile['failedDown'][0], FailedItem):
				self.version = getVersion()
				self.save()
			elif len(saveFile['failedDown']) == 0:
				self.version = getVersion()
				self.save()
		elif self.version <= u'0.3.0':
			# forgot to include self in returnTuple function in 0.3.0 (and early releases of 0.3.1 ) on failedDown, will cause crash when calling it
			for eachFailed in saveFile['failedDown']:
				newFailed = FailedItem()
				for key, value in eachFailed.iteritems():	newFailed[key] = value
				self.failedDown.append( newFailed )
		else: self.failedDown = saveFile['failedDown']
		del saveFile
		# upgrade process should be complete, set to current version
		self.version = getVersion()
	def lock( self ):
		u"""Portable locking mechanism. Binds to 'lockPort' as defined in config on
		127.0.0.1.
		Raises btrsslib.Locked if a lock already exists.
		"""
		if self.lockSock:
			raise Locked
		try:
			self.lockSock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			self.lockSock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
			self.lockSock.bind( ('127.0.0.1', getConfig()['global']['lockPort']) )
			self.lockedState = True
		except socket.error:
			raise Locked
	def unlock( self ):
		u"""Remove an existing lock()."""
		try: 
			self.lockSock.close()
			self.lockedState = False
		except socket.error: pass

def getConfig(reload=False, filename=None):
	u"""Return a shared instance of the Config class (creating one if neccessary)"""
	global _configInstance
	if reload: _configInstance = None
	if not _configInstance:
		_configInstance = Config(filename)
	return _configInstance

class Config(ConfigParser.RawConfigParser, UserDict):
	def __init__(self, filename=None):
		u"""
		see helpMessage
		"""
		ConfigParser.RawConfigParser.__init__(self)
		UserDict.__init__(self)
		self.dayList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', '0', '1', '2', '3', '4', '5', '6']
		self.boolOptionsGlobal = ['runOnce', 'active', 'rssFeed', 'urllib', 'noClobber']
		self.boolOptionsThread = ['active', 'noSave']
		self.stringOptionsGlobal = ['downloadDir', 'saveFile', 'cookieFile', 'cookieType', 'logFile', 'workingDir', 'daemonInfo', 'rssFilename', 'rssLink', 'rssDescription', 'rssTitle']
		self.stringOptionsThread = ['link', 'directory', 'postDownloadFunction', 'regExTrue', 'regExTrueOptions', 'regExFalse', 'regExFalseOptions']	
		self.intOptionsGlobal = ['maxSize', 'minSize', 'lockPort', 'scanMins', 'rssLength', 'sleepTime', 'verbose', 'log']
		self.intOptionsThread = ['maxSize', 'minSize']
		if filename: self.filename = filename
		else:
			global configFile
			self.filename = configFile
		if not os.path.isfile( self.filename ): 
			logStatusMsg( u"Configuration File could not be found, exiting...", 1, config=False)
			raise SystemExit
		a = self.read(self.filename)
		if not a:
			logStatusMsg(u'a config file was not parsed. exiting...', 1)
			raise SystemExit
		self['global'] = GlobalOptions()
		self['threads'] = {}
		self.parse()
		self.check()
	def parse(self):
		for option in self.boolOptionsGlobal:
			try: 
				if option.lower() in self.options('global'): 
					try: self['global'][option] = self.getboolean('global', option)
					except ValueError: logStatusMsg(u'failed to parse option %s in global' % option, 1, config=False)
			except ConfigParser.NoSectionError, m:
				logStatusMsg( unicode(m), 1 , False)
				raise SystemExit
				# now set by GlobalOptions()
				#except: self['global'][option] = None
		for option in self.stringOptionsGlobal:
			if option.lower() in self.options('global'):
				self['global'][option] = self.get('global', option)
				if self['global'][option] == '' or self['global'][option].lower() == 'none' : self['global'][option] = None
		for option in self.intOptionsGlobal:
			if option.lower() in self.options('global'):
				try: self['global'][option] = self.getint('global', option)
				except ValueError: logStatusMsg(u'failed to parse option %s in global' % option, 1, config=False)
		threads = self.sections()
		del threads[threads.index('global')]
		for thread in threads:
			self['threads'][thread] = ThreadLink()
			for option in self.boolOptionsThread:
				if option.lower() in self.options(thread):
					try: self['threads'][thread][option] = self.getboolean(thread, option)
					except ValueError: logStatusMsg(u'failed to parse option %s in thread %s' % (option, thread), 1, config=False)
			for option in self.stringOptionsThread:
				if option.lower() in self.options(thread):
					self['threads'][thread][option] = self.get(thread, option)
					if self['threads'][thread][option] == '' or self['threads'][thread][option].lower() == 'none': self['threads'][thread][option] = None
			for option in self.intOptionsThread:
				if option.lower() in self.options(thread):
					try: self['threads'][thread][option] = self.getint(thread, option)
					except ValueError: logStatusMsg(u'failed to parse option %s in thread %s' % (option, thread), 1, config=False)
			#populate thread.downloads
			downList = []
			for threadOption in self.options(thread):
				if threadOption.startswith('download'): downList.append(threadOption)
			downList.sort()
			for i in downList:
				if i.lower().endswith('false'): 
					optionDown = self.get(thread, i)
					if optionDown.lower() == 'false' or optionDown.lower() == '0' or optionDown.lower() == 'no':
						self['threads'][thread]['downloads'][-1]['False']  = False
					elif optionDown.lower() =='true' or optionDown.lower() == '1' or optionDown.lower() == 'yes':
						self['threads'][thread]['downloads'][-1]['False'] = True
					else: self['threads'][thread]['downloads'][-1]['False'] = optionDown
				elif i.lower().endswith('true'): 
					try: self['threads'][thread]['downloads'][-1]['True'] = self.getboolean(thread, i)
					except ValueError: pass
				elif i.lower().endswith('dir'):
					optionDown = self.get(thread, i)
					if optionDown.lower() != 'none': self['threads'][thread]['downloads'][-1]['Dir'] = optionDown
				elif i.lower().endswith('maxsize'):
					try: self['threads'][thread]['downloads'][-1]['maxSize'] = self.getint(thread, i)
					except ValueError: pass
				elif i.lower().endswith('minsize'):
					try: self['threads'][thread]['downloads'][-1]['minSize'] = self.getint(thread, i)
					except ValueError: pass
				else: self['threads'][thread]['downloads'].append( DownloadItemConfig( self.get(thread, i) ) )
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
						raise Exception, u"Could not identify valid day of the week for %s" % optionCheck
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
			self['global']['saveFile'] = u'savedstate.dat'
		if not self['global'].has_key('downloadDir') or self['global']['downloadDir'] == None:
			logStatusMsg(u"Must specify downloadDir in [global] config", 1, False )
			raise SystemExit
		if not self['global'].has_key('runOnce') or self['global']['runOnce'] == None:
			self['global']['runOnce'] = False
		if not self['global'].has_key('scanMins') or self['global']['scanMins'] == None:
			self['global']['scanMins'] = 15
		if self['global']['cookieType'] == 'MSIECookieJar' and self['global']['urllib']:
			logStatusMsg(u'Cannot use MSIECookieJar with urllib. Choose one or the other', 1, False )
			raise SystemExit
		if self['global']['cookieType'] != 'MSIECookieJar' and self['global']['cookieType'] != 'LWPCookieJar' and self['global']['cookieType'] != 'MozillaCookieJar':
			logStatusMsg(u'Invalid cookieType option: %s. Only MSIECookieJar, LWPCookieJar, and MozillaCookieJar are valid options. Exiting...' % self['global']['cookieType'], 1, False)
			raise SystemExit
		if not self['global'].has_key('lockPort') or self['global']['lockPort'] == None:
			self['global']['lockPort'] = 8023
		if self['global'].has_key('log') and self['global']['log']:
			if not self['global'].has_key('logFile') or self['global']['logFile'] == None:
				self['global']['logFile'] = u'downloads.log'
		# check all directories to make sure they exist. Ask for creation?
		if self['global']['downloadDir']:
			if not os.path.isdir( os.path.join(self['global']['workingDir'], self['global']['downloadDir']) ):
				try: os.mkdir( os.path.join(self['global']['workingDir'], self['global']['downloadDir']) )
				except OSError, m: 
					logStatusMsg( unicode(m) + os.linesep + u"Could not find path %s and could not make a directory there. Please make sure this path is correct and try creating the folder with proper permissions for me" % os.path.join(self['global']['workingDir'], self['global']['downloadDir']), 1, False )
					raise SystemExit
		for thread in self['threads']:
			if self['threads'][thread]['directory']:
				if not os.path.isdir( os.path.join(self['global']['workingDir'], self['threads'][thread]['directory']) ):
					try: os.mkdir( os.path.join(self['global']['workingDir'], self['threads'][thread]['directory']) )
					except OSError, m: 
						logStatusMsg( unicode(m) + os.linesep + u"Could not find path %s and could not make a directory there. Please make sure this path is correct and try creating the folder with proper permissions for me" % os.path.join(self['global']['workingDir'], self['threads'][thread]['directory']), 1, False)
						raise SystemExit
			if len(self['threads'][thread]['downloads']) != 0: 
				for downDict in self['threads'][thread]['downloads']:
					if downDict['Dir']:
						if not os.path.isdir( os.path.join(self['global']['workingDir'], downDict['Dir'] ) ):
							try: os.mkdir( os.path.join(self['global']['workingDir'], downDict['Dir'] ) )
							except OSError, m:
								logStatusMsg( unicode(m) + os.linesep + u"Could not find path %s and could not make a directory there. Please make sure this path is correct and try creating the folder with proper permissions for me" % os.path.join(self['global']['workingDir'], downDict['Dir'] ), 1, False)
								raise SystemExit
	def save(self):
		fd = codecs.open(self.filename, 'w', 'utf-8')
		fd.write("%s%s" %('[global]', os.linesep))
		keys = self['global'].keys()
		keys.sort()
		for key in keys:
			# rss option deprecated
			if key == 'rss': continue
			# don't write defaults
			if self['global'][key] == GlobalOptions()[key]: continue
			fd.write("%s = %s%s" % (key, unicode(self['global'][key]), os.linesep))
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
				if threadKey.lower() == 'downloads':
					if len(self['threads'][thread][threadKey]) == 0 : continue
					for downDict in self['threads'][thread][threadKey]:
						fd.write('download%s = %s%s' % (downNum, unicode(downDict['localTrue']), os.linesep))
						# don't bother writing if it's the default value
						if downDict['Dir'] != DownloadItemConfig()['Dir']: 
							fd.write('download%sDir = %s%s' % (downNum, unicode(downDict['Dir']), os.linesep))
						if downDict['False'] != DownloadItemConfig()['False']: 
							fd.write('download%sFalse = %s%s' % (downNum, unicode(downDict['False']), os.linesep))
						if downDict['maxSize'] != DownloadItemConfig()['maxSize']: 
							fd.write('download%sMaxSize = %s%s' % (downNum, unicode(downDict['maxSize']), os.linesep) )
						if downDict['minSize'] != DownloadItemConfig()['minSize']: 
							fd.write('download%sMinSize = %s%s' % (downNum, unicode(downDict['minSize']), os.linesep) )
						if downDict['True'] != DownloadItemConfig()['True']: 
							fd.write('download%sTrue = %s%s' % (downNum, unicode(downDict['True']), os.linesep))
						downNum += 1
				elif 'checkTime' == threadKey:
					if len(self['threads'][thread][threadKey]) == 0: continue
					for checkTup in self['threads'][thread][threadKey]:
						# checkNum is the item number we started on
						fd.write('checkTime%sDay = %s%s' % (checkNum, self.dayList[checkTup[0]], os.linesep))
						fd.write('checkTime%sStart = %s%s' % (checkNum, unicode(checkTup[1]), os.linesep))
						fd.write('checkTime%sStop = %s%s' % (checkNum, unicode(checkTup[2]), os.linesep))
						checkNum += 1
				else:
					if self['threads'][thread][threadKey] == ThreadLink()[threadKey]: continue
					fd.write('%s = %s%s' % (threadKey, unicode(self['threads'][thread][threadKey]), os.linesep))
			fd.write(os.linesep)
		fd.close()

# # # # #
# User/InterProcess Communication
# # # # #
def callUserFunction( functionName, directory, filename, rssItemNode, retrievedLink, downloadDict, threadName ):
	u"""calls the named function in userFunctions with arguments (these are not keyword arguments): directory, filename, rssItemNode, retrievedLink, downloadDict, threadName.
directory: name of the directory the file was saved to
filename: name of the file the downloaded data was saved to
rssItemNode: the feedparser entry for the item we are downloading. This will have been altered such that the original ['link'] element is now at ['oldlink'] and the ['link'] element has been made to be friendly with urllib2RetrievePage and mechRetrievePage
retrievedLink: the resultant url from the retrieval. May be different from ['link'] and ['oldlink'] in a number of ways (percent quoting and character encoding, in particular, plus any changes to the url from server redirection, etc.)
downloadDict: a dictionary representing the download<x> options. keys are: 'localTrue' (corresponding to download<x>) ; 'False' ; 'True' ; 'Dir' ; 'minSize' ; and 'maxSize' corresponding to their analogues in download<x>.
threadName: the name of the config entry. to be accessed like getConfig()['threads'][threadName]
	"""
	global userFunctions
	logStatusMsg( u"attempting postDownloadFunction", 5)
	userFunct = userFunctions.__getattribute__(functionName)
	userFunct(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName )

def userFunctHandling():
	u"""tries to import userFunctions, sets up the namespace
reserved words in userFunctions: everything in globals() except '__builtins__', '__name__', '__doc__', 'userFunctHandling', 'callUserFunction', 'userFunctions'.
	Reserved words: 'Config', 'ConfigParser', 'DownloadItemConfig', 'FailedItem', 'Fatal', 'GlobalOptions', 'Locked', 'Log', 'MAXFD', 'MakeRss', 'PrettyPrint', 'ReFormatString', 'SaveInfo', 'SaveProcessor', 'SharedData', 'ThreadLink', 'UMASK', '_USER_AGENT', 'UserDict', 'Warning', '_VERSION', '__file__', '_configInstance', '_log', '_sharedData', '_action', 'bdecode', 'callDaemon', 'cgi', 'checkFileSize', 'checkRegEx', 'checkRegExDown', 'checkRegExGFalse', 'checkRegExGTrue', 'checkSleep', 'cj', 'cliOptions', 'codecs', 'commentConfig', 'config', 'configFile', 'configFileNotes', 'contact', 'cookieHandler', 'cookielib', 'copy', 'copyright', 'createDaemon', 'downloadFile', 'downloader', 'encodeQuoteUrl', 'feedparser', 'findNewFile', 'getConfig', 'getFileSize', 'getFilenameFromHTTP', 'getSharedData', 'getVersion', 'getopt', 'helpMessage', 'httplib', 'killDaemon', 'logMsg', 'logStatusMsg', 'main', 'mechRetrievePage', 'mechanize', 'mimetypes', 'minidom', 'nonCoreDependencies', 'opener', 'os', 'percentIsQuoted', 'percentNeedsQuoted', 'percentQuote', 'percentQuoteCustom', 'percentQuoteDict', 'percentUnQuote', 'percentunQuoteDict', 'pickle', 're', 'rss', 'rssparse', 'run', '_runOnce', 'saved', 'searchFailed', 'securityIssues', 'signalHandler', 'socket', 'status', 'sys', 'time', 'unQuoteReQuote', 'urllib', 'urllib2', 'urllib2RetrievePage', 'urlparse', 'utfWriter', 'writeNewFile', 'xmlEscape', 'xmlUnEscape'
	check docstrings/source for use notes on these reserved words."""
	global userFunctions
	# to generate if userFunctions part, add ", " to end of global list, then feed to sed: 
	# echo globalList | sed -r 's/([a-zA-Z0-9_]*), /userFunctions.\1 = \1\n/g' | xclip, paste below
	if not userFunctions:
		for threadKey in getConfig()['threads'].keys():
			if getConfig()['threads'][threadKey]['postDownloadFunction']:
				logStatusMsg( os.path.realpath('./'), 5)
				import userFunctions
				break
		else: 
			userFunctions = 1
	bypassGlobalsList = ('__builtins__', '__name__', '__doc__', 'userFunctHandling', 'callUserFunction', 'userFunctions' )
	globalList = []
	for key, value in globals().iteritems():
		if key in bypassGlobalsList: continue
		if userFunctions != 1:	setattr(userFunctions, key, value )
		globalList.append(key)
	return globalList


class ReFormatString:
	u"""takes a string or filename, and formats it (somewhat) smartly so that line overflows are indented for easier reading, and doesn't get longer than terminal width (may not be fully crossplatform compatible. width defaults to 80)"""
	def __init__(self, inputstring=None, filename=None, linesep=os.linesep, lineLength=None, indent=' '*4, comment=None):
		if not inputstring and not filename: raise Exception, u"must provide at least a filename or inputstring"
		elif inputstring and filename: raise Exception, u"cannot provide a filename and inputstring, only one or the other"
		if inputstring: self.inputstring = inputstring
		elif file:
			fd = codecs.open(filename, 'r', 'utf-8')
			self.inputstring= fd.read()
			fd.close()
			del fd
		else: self.inputstring = None
		self.linesep = linesep
		#try:	self.lineLength = int( os.popen( 'tput cols').read() )
		self.lineLength = self._getLineWidth()
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
		u"""feed me a string and an index number, with an optional stop number, and i will return with those."""
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
		if len(lineText) <= TextAllowed: 	return [ lineText ]
		newLines = []
		firstRunBreak = True
		while lineText:
			if len(lineText) <= TextAllowed: 
				newLines.append( lineText )
				break
			for pos in xrange(TextAllowed-1, -1, -1):
				if lineText[pos] in [' ', '\t',]:
					lineBreakNum = pos
					break
			else: lineBreakNum = TextAllowed
			newLines.append( lineText[:lineBreakNum] )
			lineText = lineText[lineBreakNum+1:]
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
	def _getLineWidth(self):
		width = 80
		# 'posix', 'nt', 'dos', 'os2', 'mac', or 'ce'
		if os.name == u'posix' or os.name == u'mac' or os.name == u'os2':
			try: width = int(os.popen('stty size').read().split()[1])
			except ValueError: pass
		elif os.name == u'nt' or os.name == u'dos' or os.name == u'ce':
			try:
				try: from ctypes import windll, create_string_buffer
				except ImportError, m:
					raise Warning
				# from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440694
				h = windll.kernel32.GetStdHandle(-12)
				csbi = create_string_buffer(22)
				res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
				if res:
					import struct
					(bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
					width = right - left + 1
			# would be good to know what possible exceptions there might be here
			except Warning: pass
			except: pass
		elif os.name == u'mac': pass
		return width
		
class Log:
	u"""how we keep track of our logged data"""
	def __init__(self):
		# if not getConfig()['global']['log']: return None
		self.fd = codecs.open( getConfig()['global']['logFile'], 'a', 'utf-8')
	def write(self, message):
		self.fd.write( unicode( message ) )
	def flush(self):
		self.fd.flush()
	def close(self):
		self.fd.close()

def logMsg( msg, level, close=False,  ):
	u"""Do not call directly except to close """
	global _log
	if not _log and close: return None
	elif not _log: _log = Log()
	if msg and getConfig()['global']['log'] and getConfig()['global']['log'] >= level: _log.write(  msg + os.linesep  )
	if close: 
		_log.flush()
		_log.close()
		_log = None

def logStatusMsg( msg, level, config=True ):
	u"""write a message to the log/stdout/stderr, depending on the level. if config=False, goes straight to stderr"""
	TimeCode = u"[%4d%02d%02d.%02d:%02d.%02d]" % time.localtime()[:6]
	newmsg = TimeCode + '   ' + unicode( msg ) 
	if not config:
		sys.stderrUTF.write(  unicode(ReFormatString( inputstring=newmsg)) )
		return None
	logMsg( newmsg, level )
	status( newmsg, level )

class SharedData:
	u"""Mechanism for sharing data. Do not instantiate directly,
	use getSharedData() instead."""
	def __init__( self ):
		self.scanning = False	# True when scan in progress
		self.scanoutput = ""	# output of last scan
		self.exitNow = False	# should exit immediatley if this is set

def getSharedData():
	u"""Return a shared instance of SharedData(), creating one if neccessary. Truncates if necessary."""
	global _sharedData
	if not _sharedData:
		_sharedData = SharedData()
	if len(_sharedData.scanoutput) > 2000:
		# don't want to just keep adding to this. Make a cutoff at somepoint. This seems reasonable. Think about this more.
		maxLength = len(_sharedData.scanoutput) - 1500
		_sharedData.scanoutput = _sharedData.scanoutput[maxLength : ]
	return _sharedData

def status( message, level ):
	u"""Prints status information, writing to stdout if config 'verbose' option is set. Do not call directly. use logStatusMsg"""
	sharedData = getSharedData()
	if level ==1 or level ==2: output = sys.stderrUTF
	else: output = sys.stdoutUTF
	if getConfig()['global']['verbose'] and getConfig()['global']['verbose'] >= level:
		output.write( unicode( ReFormatString(message) ) + os.linesep )
		output.flush()
	sharedData.scanoutput += unicode( message ) + os.linesep

def getVersion():
	u"""returns the version of the program"""
	global _VERSION
	return _VERSION

def killDaemon( pid ):
	u"""kills the daemon. do not call from within a running instance of main(). it could loop forever"""
	while True:
		saved = SaveProcessor()
		try:
			saved.lock()
			saved.unlock()
			break
		except Locked:
			del saved
			sys.stdoutUTF.write( u"Save Processor is in use, waiting for it to unlock" )
			time.sleep(2)
	os.kill(pid,9)

# # # # #
#Daemon
# # # # #
def createDaemon():
	u"""Detach a process from the controlling terminal and run it in the
	background as a daemon.
	"""
	logStatusMsg(u"forking process", 5)
	try:		pid = os.fork()
	except OSError, e:
		logStatusMsg(u"s [%d]" % (e.strerror, e.errno), 1)
		raise Exception
	logStatusMsg(u"seems to have forked", 5)
	if pid == 0:	# The first child.
		logStatusMsg(u"setsid", 5)
		os.setsid()
		logStatusMsg(u"forking second child", 5)
		try:
			pid = os.fork()	# Fork a second child.
		except OSError, e:
			logStatusMsg(u"%s [%d]" % (e.strerror, e.errno), 1)
			raise Exception
		if (pid == 0):	# The second child.
			logStatusMsg(u'setting umask', 5)
			os.umask(UMASK)
		else: # exit() or _exit()?  See below.
			logStatusMsg(u"exit the first child", 5)
			os._exit(0)	# Exit parent (the first child) of the second child.
	else:
		logStatusMsg(u"pid wasn't 0", 5)
		os._exit(0)	
	logStatusMsg(u"setup resource information", 5)
	import resource		# Resource usage information.
	logStatusMsg(u"maxfd settings....", 5)
	maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	if maxfd == resource.RLIM_INFINITY:
		maxfd = MAXFD
	logStatusMsg(u"closing maxfd stuff", 5) 
	logMsg(0, 0, 1) # closing the fd's crashes when the logfile is open, so close it
	for fd in range(0, maxfd):
		try:
			os.close(fd)
		except OSError:	# ERROR, fd wasn't open to begin with (ignored)
			pass
	logStatusMsg(u"redoing stdin, stdout, stderr", 5)
	os.open(REDIRECT_TO, os.O_RDWR)	# standard input (0)
	os.dup2(0, 1)			# standard output (1)
	os.dup2(0, 2)			# standard error (2)
	return 0

def callDaemon():
	u"""setup a daemon"""
	logStatusMsg(u"calling create daemon", 5)
	retCode = createDaemon()
	logStatusMsg(u"daemon should've processed", 5)
	
	# The code, as is, will create a new file in the root directory, when
	# executed with superuser privileges.  The file will contain the following
	# daemon related process parameters: return code, process ID, parent
	# process group ID, session ID, user ID, effective user ID, real group ID,
	# and the effective group ID.  Notice the relationship between the daemon's 
	# process ID, process group ID, and its parent's process ID.
	
	procParams = u"""
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
	logStatusMsg(u"writing daemonInfo", 5)
	try: codecs.open( os.path.join(getConfig()['global']['workingDir'], getConfig()['global']['daemonInfo']), 'w', 'utf-8').write(procParams + u"\n")
	except IOError, m: 
		logStatusMsg( unicode(m) + os.linesep + u"Could not write to, or not set, daemonInfo", 1 )
		raise SystemExit

def signalHandler(signal, frame):
	u"""take the signal, find a stopping point for the program, then exit. only it doesn't work, so don't call it"""
	global saved, SaveProcessor
	try: 
		if not isinstance(saved, SaveProcessor): 
			saved = SaveProcessor()
	except NameError:
		saved = SaveProcessor()
	while saved.lockedState:
		try:
			saved.lock()
			break
		except Locked:
			print "won't kill due to locked"
			time.sleep(1)
			continue	
	saved.save()
	saved.unlock()
	raise SystemExit, u"exiting due to exit signal %s" % signal
	return None

# # # # #
#Running
# # # # #
def checkSleep( totalTime ):
	u"""let's us know when we need to stop sleeping and rescan"""
	logStatusMsg(u'checking sleep', 5)
	sharedData = getSharedData()
	steps = totalTime / 10
	for n in xrange( 0, steps ):
		time.sleep( 10 )
		if sharedData.exitNow:
			raise SystemExit

def run():
	u"""Provides main functionality -- scans threads."""
	global saved, config, rss, downloader, _action
	config = getConfig(filename=configFile, reload=True)
	if _action == 'daemon': getConfig()['global']['verbose'] = 0
	if getConfig()['global']['urllib']: downloader  = urllib2RetrievePage
	else: downloader = mechRetrievePage
	saved = SaveProcessor(getConfig()['global']['saveFile'])
	try:
		saved.lock()
	except Locked:
		logStatusMsg( u"Savefile is currently in use.", 2 )
		raise Warning
	try: saved.load()
	except (IOError, ValueError, IndexError), m: logStatusMsg(unicode(m) + os.linesep + u"didn't load SaveProcessor", 1)
	logStatusMsg(u"checking working dir, maybe changing dir", 5)
	if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): os.chdir(getConfig()['global']['workingDir'])
	timeTuple = time.localtime().tm_wday, time.localtime().tm_hour
	if getConfig()['global']['runOnce']:
		if saved.lastChecked > ( int(time.time()) - (getConfig()['global']['scanMins']*60) ):
			logStatusMsg(u"Threads have already been scanned.", 2)
			raise Warning
	if getConfig()['global']['rssFeed']:
		logStatusMsg(u'trying to generate rss feed', 5)
		if getConfig()['global']['rssFilename']:
			logStatusMsg(u'rss filename set', 5)
			loadRss ={}
			loadRss['title'] = getConfig()['global']['rssTitle']
			loadRss['description'] = getConfig()['global']['rssDescription']
			loadRss['link'] = getConfig()['global']['rssLink']
			rss = MakeRss(filename=getConfig()['global']['rssFilename'])
			if os.path.isfile( getConfig()['global']['rssFilename'] ):
				logStatusMsg(u'loading rss file', 5)
				rss.parse()
			rss.channelMeta = loadRss
		else:		logStatusMsg(u"no rssFilename set, cannot write feed to a file")
	userFunctHandling()
	if saved.failedDown:
		logStatusMsg(u"Scanning previously failed downloads", 4)
		for i in  xrange( len( saved.failedDown) - 1, -1, -1 ):
			logStatusMsg(u"  Attempting to download %s" % saved.failedDown[i]['link'], 4 )
			if downloadFile( *saved.failedDown[i].returnTuple() ):
				logStatusMsg(u"Success!", 4)
				del saved.failedDown[ i ]
				saved.save()
			else:
				logStatusMsg(u"Failure on %s in failedDown" % saved.failedDown[i]['link'], 4)
	logStatusMsg( u"Scanning threads", 4 )
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
				logStatusMsg(u"""RSS feed "%s" has indicated that we should wait greater than the scan time you have set in your configuration. Will try again at next configured scantime""" % key, 4)
				continue
		logStatusMsg( u"finding new downloads in thread %s" % key, 4 )
		if getConfig()['threads'][key]['noSave'] == True:
			logStatusMsg( u"(not saving to disk)", 4)
		try: config['threads'][key] = rssparse(getConfig()['threads'][key], threadName=key)	
		except IOError, ioe: raise Fatal, u"%s: %s" % (ioe.strerror, ioe.filename)
	if rss:
		rss.close(length=getConfig()['global']['rssLength'])
		rss.write(filename=getConfig()['global']['rssFilename'])
	saved.lastChecked = int(time.time()) -30
	saved.save()
	saved.unlock()
	logMsg( 0 , 0 , close=1)

def main( ):
	global _runOnce
	config = getConfig(filename=configFile)
	sharedData = getSharedData()
	sharedData.scanoutput = ""
	if not _runOnce:
		_runOnce = getConfig()['global']['runOnce']
	while True:
		try:
			sharedData.scanoutput += os.linesep * 2
			sharedData.scanning = True
			logStatusMsg( u"[Waking up] %s" % time.asctime() , 4)
			startTime = time.time()
			run()
			logStatusMsg( u"Processing took %d seconds" % (time.time() - startTime) , 4)
		except Warning, message:
			logStatusMsg( u"Warning: %s" % unicode(message), 1 )
		except Fatal, message:
			logStatusMsg( u"Error: %s" % unicode(message), 1 )
			sharedData.scanning = False
			raise SystemExit
		sharedData.scanning = False
		if _runOnce:
			logStatusMsg( u"[Complete] %s" % time.asctime() , 4)
			break
		logStatusMsg( u"[Sleeping] %s" % time.asctime() , 4)
		elapsed = time.time() - saved.lastChecked
		#checkSleep has a 10 second resolution, let's sleep for 9, just to be on the safe side
		time.sleep(9)
		if  getConfig()['global']['scanMins'] * 60 < time.time() - saved.lastChecked: checkSleep ( getConfig()['global']['scanMins'] * 60 - elapsed )
		else: checkSleep( getConfig()['global']['scanMins'] * 60 )
	


helpMessage=u"""RSSDler is a Python based program to automatically grab the link elements of an rss feed, aka an RSS broadcatcher. It happens to work just fine for grabbing RSS feeds of torrents, so called torrent broadcatching. It may also used with podcasts and such. Though designed with an eye toward rtorrent, it should work with any torrenting program that can read torrent files written to a directory. It does not explicitly interface with rtorrent in anyway and therefore has no dependency on it. You can find the webpage here: http://libtorrent.rakshasa.no/wiki/UtilsRSSDler

Effort has been put into keeping the program from crashing from random errors like bad links and such. However, some of the exceptions caught are too broad and keep users from knowing what is wrong with their configuration, though this problem should be significantly mitigated by the new verbosity options. Try to be careful when setting up your configuration file. If you are having problems, try to start with a very basic setup and slowly increase its complexity. You need to have a basic understanding of regular expressions to setup the regex and download<x> options, which is probably necessary to broadcatch in an efficient manner. If you do not know what and/or how to use regular expressions, google is your friend. There are literally dozens of tutorials and documentation on the subject with a range of difficulty levels from beginner to expert. If you are having problems that you believe are RSSDler's fault, feel free to email me at the below address. Please be sure to include as much information as you can.

%s

%s
	
%s

Configuration File:
%s

Global Options:
%s

	
Thread options:
%s


A Netscape cookies file must have the proper header that looks like this:
# HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.
# To delete cookies, use the Cookie Manager.

cookiedata ....

%s

Contact:  %s
""" % (cliOptions, nonCoreDependencies, securityIssues, configFileNotes, GlobalOptions.__doc__, ThreadLink.__doc__, copyright, contact)
#if we lock saved before calling kill, it will be locked and we will never get to an unlock state which is our indicator that it is ok to kill.
if __name__ == '__main__':
	try: 
		(argp, rest) =  getopt.gnu_getopt(sys.argv[1:], "drokc:h", longopts=["daemon", "run", "runonce", "kill", "config=", "set-default-config=", "help", "list-failed", "list-saved", "purged-saved", "purge-failed", "comment-config"])
	except	getopt.GetoptError:
			sys.stderrUTF.write(helpMessage)
			sys.exit(1)
	
	for param, argum in argp:
		if param == "--daemon" or param == "-d":	_action = "daemon"		
		elif param == "--run" or param == "-r": _action = "run"
		elif param == "--runonce" or param == "-o":
			_action = "run"
			_runOnce = True
		elif param == "--kill" or param == "-k":	_action = "kill"
		elif param == "--config" or param == "-c": configFile = argum
		elif param == "--purge-failed": _action="purge-failed"
		elif param == "--help" or param == "-h":  _action = 'help'
		elif param == "--set-default-config": _action ='set-default-config'
		elif param == "--list-failed":	_action = 'list-failed'
		elif param == "--list-saved": _action = 'list-saved'
		elif param == "--purge-saved": _action = 'purge-saved'
		elif param == "--comment-config": _action = 'comment-config'
			
	if _action == 'comment-config':
		# do not use ReFormatString b/c we want to preserve lines for e.g. > sample.cfg
		print commentConfig
		raise SystemExit
	elif _action == "daemon":
		#call daemon
		if (hasattr(os, "devnull")):
			REDIRECT_TO = os.devnull
		else:
			REDIRECT_TO = "/dev/null"
		config = getConfig(filename=configFile, reload=True)
		getConfig()['global']['verbose'] = 0
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
			logStatusMsg(u"changing directory to %s" % getConfig()['global']['workingDir'], 5)
			os.chdir(getConfig()['global']['workingDir'])
		logStatusMsg(u"entering Daemon mode", 5)
		callDaemon()
		logStatusMsg( u"--- RSSDler %s" % getVersion() , 4)
##		import signal
##		signal.signal(signal.SIGINT, signalHandler)
##		signal.signal(signal.SIGQUIT, signalHandler)
		main()
	elif _action == 'help':
		sys.stdoutUTF.write(unicode(ReFormatString(inputstring=helpMessage)) + os.linesep)
		raise SystemExit
	elif _action == "kill":
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
	elif _action == "list-failed":
		config = getConfig(filename=configFile, reload=True)
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
			os.chdir(getConfig()['global']['workingDir'])
		while 1:
			saved = SaveProcessor( getConfig()['global']['saveFile'] )
			try: 
				saved.lock()
				saved.load()
				break
			except (Locked, IOError, ValueError, IndexError):
				del saved
				time.sleep(3)
				continue
		for failure in  saved.failedDown:
			print failure['link'] 
		saved.unlock()
		sys.exit()
	elif _action == "list-saved":
		config = getConfig(filename=configFile, reload=True)
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
			os.chdir(getConfig()['global']['workingDir'])
		while 1:
			saved = SaveProcessor( getConfig()['global']['saveFile'] )
			try: 
				saved.lock()
				saved.load()
				break
			except (Locked, IOError, ValueError, IndexError):
				del saved
				time.sleep(3)
				continue
		for down in  saved.downloads:
			print down 
		saved.unlock()
		sys.exit()
	elif _action == "purge-failed":
		config = getConfig(filename=configFile, reload=True)
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
			os.chdir(getConfig()['global']['workingDir'])
		while 1:
			saved = SaveProcessor( getConfig()['global']['saveFile'] )
			try: 
				saved.lock()
				saved.load()
				break
			except (Locked, IOError, ValueError, IndexError):
				del saved
				time.sleep(3)
				continue
		while saved.failedDown:
			saved.downloads.append( saved.failedDown.pop()['link'] )
		saved.save()
		saved.unlock()
		sys.exit()
	elif _action == "purge-saved":
		config = getConfig(filename=configFile, reload=True)
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
			os.chdir(getConfig()['global']['workingDir'])
		while 1:
			saved = SaveProcessor( getConfig()['global']['saveFile'] )
			try: 
				saved.lock()
				saved.load()
				break
			except (Locked, IOError, ValueError, IndexError):
				del saved
				time.sleep(3)
				continue
		saved.downloads = []
		saved.save()
		sys.exit()
	elif _action == "run":
		config = getConfig(filename=configFile, reload=True)
		logStatusMsg( u"--- RSSDler %s" % getVersion() , 4)
		if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
			logStatusMsg(u"changing directory to %s" % getConfig()['global']['workingDir'], 5)
			os.chdir(getConfig()['global']['workingDir'])
##		import signal
##		signal.signal(signal.SIGINT, signalHandler)
##		signal.signal(signal.SIGQUIT, signalHandler)
		main()
	elif _action == 'set-default-config':
		a = os.path.realpath( sys.argv[0] )
		if not os.access(a, os.F_OK):
			logStatusMsg( u"Cannot find RSSDler to edit. exiting...", 1)
			raise SystemExit
		if not os.access(a, os.R_OK): 
			logStatusMsg( u"Do not have read permission to RSSDler. exiting...", 1)
			raise SystemExit
		if not os.access(a, os.W_OK):
			logStatusMsg( u"Do not have write permissions to RSSDler. exiting...", 1)
			raise SystemExit
		if not os.access(argum, os.F_OK):
			logStatusMsg( u"config file does not exist! exiting...", 1)
			raise SystemExit
		if not os.access(argum, os.R_OK):
			logStatusMsg( u"no read permission on the config file. exiting...", 1)
			raise SystemExit
		oldFile = codecs.open(a, 'r', 'utf-8').read()
		switch = re.compile(r'^(configFile = )u""".*"""$', re.M)
		newFile = switch.sub(r'\1u"""' + unicode(argum) + '"""', oldFile)
		if newFile == oldFile:
			sys.stderrUTF.write(u'Swich failed, or already set.')
			raise SystemExit
		codecs.open(a, 'w', 'utf-8').write(newFile)
		print "success!"
		raise SystemExit
	
