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
        failedProcedure(u"The file %s wasn't actually torrent data. Attempting to remove from queue. Will add to failedDown" % filename , directory, filename, threadName, rssItemNode, downloadDict )
        return False

def currentOnly(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName):
    u"""A postDownloadFunction: checks to make sure that the item was added recently. Useful for feeds that get messed up on occasion."""
    try: maxage = getConfig().getint(threadName, 'maxage')
    except (ValueError, ConfigParser.NoOptionError): maxage = 86400
    if time.time() - time.mktime( rssItemNode['updated_parsed'] ) > maxage:
        try: os.unlink( os.path.join(directory, filename) )
        except OSError: logStatusMsg(u"could not remove file from disk: %s" % filename, 1 ) 
        global rss
        if rss: rss.delItem()
    
def noRss(directory, filename, rssItemNode, retrievedLink, downloadDict, threadName):
    u"""A postDownloadFunction: removes the downloaded item from RSS, in case you want to generate an rss feed of some downloaded items, but not all"""
    global rss
    if rss: rss.delItem()

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

def downloadFromSomeSite( directory, filename, rssItemNode, retrievedLink, downloadDict, threadName ):
  """download a file from an html page. 
  set two options in your thread configuration 
  baselink: the baseurl of the site (should include a trailing /
    example: http://cnn.com/
  urlsearch: a string that will be present in the url for any given download. 
    e.g. /download/, /torrent/, gettorrent.php, etc.
    by default, this is not a regular expression, but a code snippet is provided
    in the source if you want to treat it as one.
    depends on libxml2dom
    assumes you want to grab a torrent file. 
    Comment out last two lines if you want a non-torrent file
    """
  try:
    baselink = getConfig().get(threadName, 'baselink')
    urlsearch = getConfig().get(threadName, 'urlsearch')
  except ConfigParser.NoOptionError:
    logging.critical("""To use downloadFromSomeSite function, \
you must provide options baselink and urlsearch in your config""")
    return None
  global libxml2dom
  try: libxml2dom
  except NameError: import libxml2dom
  try: a = codecs.open( os.path.join( directory, filename ), 'rb' )
  except IOError, m:
    failedProcedure( u"""%s: could not even open our just written file.leaving \
function..""" % m, directory, filename, threadName, rssItemNode, downloadDict) 
    return None
  p = libxml2dom.parseString( a.read(), html=True)
  try: link = "%s%s" % (baselink ,  [x.getAttribute('href') for x in
    p.getElementsByTagName('a') if x.hasAttribute('href') and
    x.getAttribute('href').count(urlsearch) ][0] )
    # if you want a regex. Then, instead of
    # x.getAttribute('href').count(urlsearch) do:
    # re.search(urlsearch, x.getAttribute('href'))
  except IndexError, m:
    failedProcedure( u"""%s: could not find href for downloaded %s item for \
redownload""" % (m, threadName), directory, filename, threadName, 
      rssItemNode, downloadDict)
    return None
  try: d = downloader(link)
  except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException), m:
    failedProcedure( '%s: could not download torrent from site' % m,
      directory, filename, threadName, rssItemNode, downloadDict)
    return None
  newfilename = getFilenameFromHTTP( d.info(), d.geturl() )
  newfilename = writeNewFile( newfilename, directory, d )
  # assume we want a torrent file
  if ifTorrent( directory, newfilename, rssItemNode, retrievedLink, downloadDict, threadName):
    os.unlink( os.path.join(directory, filename) )

def failedProcedure( message, directory, filename, threadName, rssItemNode, downloadDict ):
    u"""A function to take care of failed downloads, cleans up saved, failed, rss, the directory/filename, and prints to the log. should be called from other functions here, not directly from RSSDler."""
    logging.critical(unicodeC(message))
    saved.failedDown.append( FailedItem( saved.downloads.pop(), threadName, rssItemNode, downloadDict) )
    try: os.unlink(os.path.join(directory, filename))
    except OSError: logStatusMsg(u"could not remove file from disk: %s" % filename, 1 ) 
    if rss: rss.delItem()
