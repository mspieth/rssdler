def ifTorrent(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName):
	u"""a postDownloadFunction for RSSDler. Confirms that downloaded data is valid bencoded (torrent) data
	If not, removes the file from disk, saved.downloads, and rss feed, adds it to saved.failedDown
	"""
	global saved
	try: fd = open(os.path.join(directory, filename), 'rb')
	except IOError, m:
		logStatusMsg( unicode(m) + u" could not even open our just written file. leaving function..", 2)
		return None
	try: fdT = bdecode( fd.read() )
	except ValueError: fdT = False
	if fdT: 
		# maybe you want to store downloaded data in a tmp directory so you can vet it here and then pass it on to wherever
		# os.rename( os.path.join(directory, filename), os.path.join('/my/other/directory', filename) )
		# if we successfully bdecoded the data, means that it is a torrent and we can exit, otherwise
		return True
	# the url for this download should be the last one added to saved. could try checking against rssItemNode['link'] to be sure
	else:
		logStatusMsg(u"The file %s wasn't actually torrent data. Attempting to remove from queue. Will add to failedDown" % filename , 1)
		try: os.unlink( os.path.join(directory, filename) )
		except OSError: logStatusMsg(u"could not remove file from disk: %s" % filename, 1 )	
		saved.failedDown.append( FailedItem( saved.downloads.pop(), threadName, rssItemNode, downloadDict) )
		# if using rss, remove the rss entry for the items
		global rss
		if rss: rss.delItem()
		return False

def currentOnly(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName):
	u"""A postDownloadFunction: checks to make sure that the item was added recently. Useful for feeds that get messed up on occasion."""
	if time.time() - time.mktime( rssItemNode['updated_parsed'] ) > 86400:
		try: os.unlink( os.path.join(directory, filename) )
		except OSError: logStatusMsg(u"could not remove file from disk: %s" % filename, 1 )	
		global rss
		if rss: rss.delItem()
	
def noRss(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName):
	u"""A postDownloadFunction: removes the downloaded item from RSS, in case you want to generate an rss feed of some downloaded items, but not all"""
	global rss
	if rss: rss.delItem()

def rmObj(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName):
	u"""A temporary fix to issue #2 (link below). Removes .obj extension from files with mime-type Octect-Stream
	http://code.google.com/p/rssdler/issues/detail?id=2
	"""
	if filename.endswith('.obj'):
		newfilename = filename[:-4]
		try: os.rename( os.path.join(directory, filename), os.path.join(directory, newfilename) )
		except Exception, m: logStatusMsg(u"could not remove .obj from filename %s" % filename, 2)

def _saveFeed(page, ppage, retrievedLink, threadName, filename, length):
	u"""A helper postScanFunction. Do not call directly, use saveFeed. Uses MakeRss to generate an archive of rss items.
	Useful for later perusal by a human read rss reader without having to hit up the server multiple times.
	WILL generate an invalid feed that may break some readers. See issue #3 (link below).
	http://code.google.com/p/rssdler/issues/detail?id=3
	"""
	global minidom, random
	try:
		if not minidom: from xml.dom import minidom
	except ImportError, m:
		logStatusMsg(unicode(m), 1 )
		raise ImportError
	try:
		if not random: import random
	except ImportError, m:
		logStatusMsg( unicode(m), 1 )
		raise ImportError
	rssl = MakeRss(filename=filename, itemsQuaDictBool=True)
	if os.path.isfile( filename ):		rssl.parse()
	rssl.channelMeta = ppage['feed']
	links = [ x['link'] for x in rssl.itemsQuaDict ] # if no link key, this will fail without proper handling
	for entry in reversed( ppage['entries'] ):
		if entry['link'] not in links: rssl.makeItemNode( entry ) # this logic could be better
	rssl.close(length=length)
	rssl.write()
	

def saveFeed(*args):
	u"""A postScanFunction that will save an archive of the feed to the indiciated filename, and store as many items indicated in desiredLength.
	Feed will not be perfect, but will work in most cases relatively well. That is, a forgiving reader will parse.
	"""
	args = list(args)
	desiredLength = 100
	args.extend( ('afilenameforfeed.xml', desiredLength) )
	_saveFeed( *args )
