# [RSSDler](http://code.google.com/p/rssdler/) #
A utility to automatically download enclosures and other objects linked to from various types of RSS feeds. Works well on podcasts, videocasts, and torrents.

### Features include: ###
  * filtering using regular expressions and/or file size
  * global, feed, and filter based download locations
  * can run in the background (at least on GNU/Linux) like a daemon
  * various logging and verbosity levels
  * support for sites protected with cookies (LWP/MSIE/Mozilla/Safari/Firefox3)
  * global and feed scan times
  * respects 'ttl' tag in feeds that have them
  * call custom functions after a download or after a scan of the feed (episode advancement!)
  * generates an RSS feed of what it has downloaded.

Because it is written in Python, it is highly cross-platform compatible. It tries to be memory efficient, with reports of it functioning on consumer routers. Minimal external dependencies help keep that a reality. It became popular when people started using it in conjunction with [rTorrent](http://libtorrent.rakshasa.no/) for torrent broadcatching.

### News ###
  * 2009.10.01  Version 0.4.2 released  See ChangeLog for details.
  * 2008.04.29: Version 0.4.0 released. See ChangeLog and [release message](http://groups.google.com/group/rssdler/t/f2321368ed5cf476) for details.
  * 2008.01.13: Version 0.3.4 released. See ChangeLog for details
  * 2008.01.11: Version 0.3.3 released. See ChangeLog for details
  * 2008.01.01: Version 0.3.2 released. See ChangeLog for details

### Dependencies ###
  * [Python 2.4 or later](http://python.org) (required)
  * [feedparser](http://feedparser.org/) (required)
  * [mechanize](http://wwwsearch.sourceforge.net/mechanize/) (suggested)]

### Support ###
Still have questions after reading the wiki. Message the [group](http://groups.google.com/group/rssdler) and see if you cannot get help  there.



### Development ###

You can also find the [development version](http://rssdler.googlecode.com/svn/trunk/rssdler.py) for testing or using new features or trying out new bugfixes. This may or may not run and may or may not be stable. There are times when it contains bugfixes for the latest version, and times when it is undergoing feature development and may be subject to crashes. The changelog will note the changes in the development version, but those changes may be buggy and/or incomplete. Feel free to test this version and email me the bug reports you have.

### And by popular request: ###
  * a CommentedConfig file
  * As well as sample [postDownloadFunctions](http://rssdler.googlecode.com/svn/trunk/userFunctions.py), the most recent of which will be in your installation tarball
  * An init script can be found in the installation tar ball

If you are here from the rtorrent website, note that you'll want to set downloadDir (see HelpMessage) to the same directory as rtorrent's watch directory. Of course, you can download different rss feeds to different directories with the directory option for each thread.

PLEASE READ THE ChangeLog BETWEEN UPGRADES. Settings may change that require some (minor) user intervention. These will be detailed between releases (as well as more esoteric things).