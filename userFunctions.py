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
    if fdT:     return True
    else:
        failedProcedure(u"The file %s wasn't actually torrent data. Attempting to remove from queue. Will add to failedDown" % filename , 1, directory, filename, threadName, rssItemNode, downloadDict )
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

def saveFeed(page, ppage, retrievedLink, threadName):
    u"""A helper postScanFunction. Do not call directly, use saveFeed. Uses MakeRss to generate an archive of rss items.
    Useful for later perusal by a human read rss reader without having to hit up the server multiple times.
    WILL generate an invalid feed that may break some readers. See issue #3 (link below).
    http://code.google.com/p/rssdler/issues/detail?id=3
    """
    # makes use of custom options you can define for each section/thread
    # those options are rssfile and rsslength
    # these are NOT global options, only apply to the thread
    # if this function is called without these specified in the config
    # will default to threadName.xml and length = 100
    try: filename= getConfig().get(threadName, 'rssfile') 
    except ConfigParser.NoOptionError: filename = "%s.xml" % threadName
    try: length = getConfig().getint(threadName, 'rsslength')
    except ConfigParser.NoOptionError: length = 100
    rssl = MakeRss(filename=filename, parse=True, itemsQuaDictBool=True)
    rssl.channelMeta = ppage['feed']
    links = [ x['link'] for x in rssl.itemsQuaDict ] # if no link key, this will fail without proper handling
    [ rssl.addItem(x) for x in reversed(ppage['entries']) if x['link'] not in links ]
    rssl.close(length=length)
    rssl.write()

def failedProcedure( message, level, directory, filename, threadName, rssItemNode, downloadDict ):
    u"""A function to take care of failed downloads, cleans up saved, failed, rss, the directory/filename, and prints to the log. should be called from other functions here, not directly from RSSDler."""
    logStatusMsg( message, level)
    saved.failedDown.append( FailedItem( saved.downloads.pop(), threadName, rssItemNode, downloadDict) )
    try: os.unlink(os.path.join(directory, filename))
    except OSError: logStatusMsg(u"could not remove file from disk: %s" % filename, 1 ) 
    if rss: rss.delItem()
