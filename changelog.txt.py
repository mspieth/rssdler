#!/usr/bin/python
# -*- coding: utf-8 -*-
# init script for rtorrent: su -c "screen -S "${srnname}" -X screen sg ${group} -c rtorrent ${options[i]} 2>&1 1>/dev/null" ${user} | tee -a "$logfile" >&2
# release steps:
# edit note on init script as being in development
# re-edit globals used in userFunctHandling()
# if change comment config, change \b corrupted to \b
# change membership test and natural numbers to appropriate values
#  min{nX | nX >= Y ; nX >= Z ; n ∈ ℕ }
# change version number on import to XYZ
# change date on verXYZ to current date
# make link (with [[BR]] on end) to newest version in intro
releaseBashLAPTOP="""
cd /project/directory/in/terminal/with/access/to/XClipboard
X=0
Y=3
Z=2
XYZ="$X""$Y""$Z"
cp rssdlerDev.py Old/rssdler"$XYZ".py && cd Old && ln -s rssdler"$XYZ".py rssdler-"$X"."$Y"."$Z".py && chmod 550 rssdler"$XYZ".py
cd ..
./changelog.txt.py -w | xclip
./Old/rssdler"$XYZ".py --comment-config | xclip #if changes
rm Old/rssdler-"$X"."$Y"."$Z".py # after upload of file
"""
printaction = None
##from Old.rssdler032 import *
from rssdlerDev import *

Bugs=u"""Known Bugs:
	- python's networking modules do not deal with unicode strings. Effort has been made to encode to utf-8 before passing on to any of the networking functions. If you see anything about a Unicode error, PLEASE email me the traceback message and any more information you can provide about it.
	- generic mimetype causes .obj to be appended to filename. Maybe trust filename from header, and only check mimetype if filename is from url?
"""
Requests = """Requests: NONE!?!""" 
Todo = """TODO:
	- MakeRss class full convert arbitrary feedparser Dictionary to XML (low priority, look for other implementations, if anyone sees this has been done somewhere, let me know)
	- make a decision of whether to use percentQuote or percentQuoteCustom. If you get any unicode errors, especially with urls, this is a good place to look to see if handling can be improved."""
	
ver032 = u"""0.3.2 alpha (development version)
	<DATE>
	- made init script for debian based distros
	- global umask option (reads as decimal NOT OCTAL, read documentation for details and before using (i'm serious))
	- got proper signal handling. Exit the program cleanly (like -k.). aka: let ctrl-c (somewhat) cleanly exit the program.
	- added global option maxLogLength. the internal message log can grow rather large, make a setting to allow truncating at a certain number of lines to keep memory usage after long run times under control.
	- added postScan function for threads
	- ReFormatString got called with no config, when config should indicate there is no stdout/stderr (daemon mode) and tries to print. this causes a crash. Now notices daemon mode and fails to print anything.
	- scanMins for threads (see documentation on implementation notes)
	- MakeRss methods changed slightly, storage of items as dictionaries until .close(). (This means you should redownload the userFunctions.py if you were using mine, as there had to be some minor changes.) (MakeRss)
	- removed dependency on saxutils for xml(Un)Escape
	- returned properly from failed rss feed retrieval
	- improved memory management when file is not a torrent (probably best with mechanize, helps deal with video podcasts or large audio podcasts better).
	- removed full dependency on mechanize. Config parser will try to import mechanize if urllib = False, set urllib = True if it fails.
	- removed full dependency on bencode.bdecode. made bdecode function. will still try to import the others, but if they are not there, will fall back to this one
	- xml.dom.ext.PrettyPrint was causing problems on some characters. RSSDler no longer uses it. (MakeRss)
	- make failedDown respect rss minScanTime
	- support 'enclosure' attribute (first tries to get first enclosed media element of such feeds, then tries normal link element) (rssparse)
	- catch EOFError on SaveProcessor.load error, notify user that new saveFile will be made on error.
	- no longer raise Warning on failed size grab, just return None (getFileSize)
	- changed daemonInfo format to be just the pid of rssdler ; changed --kill running to accomdate. Allows for use of start-stop-daemon in init script
	- removed logStatusMsg entries before we change directory to working directory/set umask.
	- try to prevent sending same message repeatedly (status, getSharedData, logStatusMsg, only for errors)
	- added tilde to percentQuoteDict (especially helpful for feedburner feeds)"""
ver031 = u"""0.3.1
	2007.10.28
	- verbosity/log level 3 is much less wordy, only adds what is downloaded. To get what used to be level 3 verbosity, use level 4. This is also about equivalent to what verbose = True was pre-0.3.0.
	- symlinks to files messes with the import of modules that are supposed to be in the current working directory. We now prepend '' to sys.path if it is not there to fix this. (global)
	- sample postDownloadFunction, checking to make sure we have valid torrent data, and if not removes from saved list, adds to failed, and if rss is set, clears it from the rss feed. No, this does not go into the main program because it the main program is not meant only for torrents.
	- sets verbose = 0 when entering daemon mode (prevents crash since stdout/stderr are gone). This means Config.save invoked in a postDownloadFunction when run with -d will rewrite this option as 0 (run).
	- fixes bug in SaveProcessor.save/load with missing version
	- check for key content-length before attempting to access (checkFileSize)
	- attempts to get console width on multiple platforms (ReFormatString)
	- more unicode fixes
	- more fixes of quoting urls 
	- rssLength = 0 now means to never truncate the download list, instead of storing nothing like before. (MakeRss)
	- fixed error: "TypeError: returnTuple() takes no arguments (1 given)" that would crop up in run. (saveProccessor/FailedItem)""" 

	
ver030 = u"""0.3.0 alpha quality
	2007.10.19
	- changed how verbose and log work. Now integer, aka no longer Boolean, options! Change config to comply. Now, support for excessive verbosity for easy(er?) problem identification
	- a narrated and commented sample config is now available with most options explained. available with the --comment-config cli option
	- all output now timestamped (down to the second). 
	- gave userFunctions access to many rssdler functions, classes, variables, and instantiations. use wisely. Also, changed the arguments sent to the function called. See documentation for details. EXCEPTION HANDLING IS THE RESPONSIBILITY OF THE FUNCTION BEING CALLED
	- list failed, saved, purge-saved, purge-failed. (removes -f, --failed to remove ambiguity) (cli options)
	- unquoted urls should now properly be detected and quoted, even if containing unquoted % characters
	- all log/status/errorMsg calls now logStatusMsg w/ level indicator
	- helpMessage maintenance
	- more unicodification of strings
	- select cookie format (MSIECookieJar (mechanize only), LWPCookieJar, MozillaCookieJar )
	- fix xml.dom.ext import error on installations that don't have xml.dom.ext available, set PrettyPrint to _write (MakeRss)
	- make a 'write data' function for downloaded data. Should not clobber pre-existing files. Unlinks failed writes. Only used for downloaded data, not logs, etc.
	- unescapes xml entity references in the <link> (feedparser bug, should be updated. )
	- sleep between http fetches (configurable, default is not to sleep)
	- cli opton to reset default config file (advised only for single user systems/installs)
	- put version number in saveFile (for changes to failedTups)
	- changes to how failed/download<x> items are stored internally (should be easier to edit)
	- config.save() will not write out options that are set to their default values (less clutter)"""
	
	
	
ver024 = u"""0.2.4
	2007.10.01
	- moved kill action outside optparse loop so that config file location can be more reliably recognized
	- improved exception handling, notifcation, and logging of errors. Hopefully this will allow users to more easily identify problems they are having and to fix their setup or report bugs as necessary.
	- removed dependency on mechanize, though that dependency is still default. To get rid of it, set urllib = True in global options to make use of urllib2. (new Function: urllib2RetrievePage)
	- added error option to global. 0=Suppress all error messages. 1=Print error to stderr. 2=Log error to logfile. 3=2+1 aka log and stderr. . . Default is 1(status)
	- reduced mechRetrievePage to only fetch urls to reduce complexity of function.
	- removed support for 'rss' and 'checkTime' options. Check out the analogous updated options (rssFeed and related, checkTimeDay and related)
	- removed eval statements
	- regExTrueOptions/regExFalseOptions now apply to download<x> and download<x>False if set.
	- added -f/--failed to clear failed downloads from the queue so that you can clear them out if they are repeatedly trying to download and not working and you just don't care anymore.
	- attempt at improving filename/filetype guessing (getFilenameFromHTTP)
	- try to determine terminal width, adjust text output for more readable messages"""

ver023 = u"""0.2.3
	2007.09.25
	- fixed search for non-specified cookiefile aka None is not a string (mechRetrievePage)"""
	
ver022 = u"""0.2.2
	2007.09.19
	- new log function for easier logging of errors (will begin to add error information to downloads.log)
	- open text files as utf-8 for reading/writing/appending
	- convert url to ISO-8859-1 to prevent unicode errors in httplib from cropping up (mechRetrievePage)
	- work on proper quoting/encoding of invalid urls (mechRetrievePage)
	- removed call to Config().save. aka stops clobbering the config file. No changes to config are made during run time, except for setting defaults, so this should be safe. save still exists as a method of Config(), if you want to make use of it in a postDownloadFunction. Allows for dynamic working directory, unless it is explicitly set in the config file. (run)
	- removed missed check for the former 10 minute scan time minimum (run)
	- fixed (I think) the utfWriter/sys.stdout conflict in status()/global variables
	- removed the requirement for cookies. If a file is specified (new default is None), then it will fail if it can't find a properly Netscape formatted cookie file. If None is specified, it will exclude the cookie jar from the url opener (mechRetrievePage)
	- set the shabang to /usr/bin/env python
	- reworked filename guessing from url. Now parses the url, takes the path, splits off the last element after /, and unquotes that. Still tries to grab from HTTP headers first. (getFilenameFromHTTP). If you know of a standarized method for getting the filename from the url, please send it to me."""

ver021 = u"""0.2.1
	2007.09.12
	- fixed a minor bug that caused failed downloads to crash on retry"""

ver020 = u"""0.2 
	2007.09.11
	- UPGRADE NOTE: make sure your failedDownloads list is empty in your saved state. if unsure, delete saved state. However, this may cause torrents to be redownloaded
	- Added support for individual regex's for individual downloads. (see download<x>(false||true) ). Also added support for individual download directories
	- Changed makeRss class. New items should end up on top of the xml file, whereas before they were appended to the end. This will make the feed drop some items in the wrong order, but will be self correcting and should not change again. some behavior of the class functions/methods have changed. 
	- ConfigParser.save() changed to make the config be saved in sane (approximately alphabetical) order, with [global] on top. This bypasses the normal save method, and could be broken someplace.
	- No more minimum minutes on scanMins. Up to user to have sane setting. will respect <ttl></ttl>. If site wants a min scan time, they should set it programmatically.
	- checks for directory existence. Will try to create it if it does not exist. if this fails, will raise an exception and exit
	- sharedData now truncated to a size of 1500 after it reaches over 2000 characters. Just to keep its size reasonable.
	- fixed defaults for persistenceClasses (e.g. maxSize)"""


ver010 = u"""0.1
	- First Release"""
intro = u"""= [http://libtorrent.rakshasa.no/wiki/UtilsRSSDler RSSDler] =
== A Utility in [http://python.org/ Python] for [http://en.wikipedia.org/wiki/Broadcatching Broadcatching] RSS feeds with rTorrent ==
Actually, the program can also be used for podcasts (though it looks toward the <link> as opposed to the <enclosure> attribute) as well, these are, from what I've seen, typically identical, at least insofar as feedparser presents them. 

Written by lostnihilist: lostnihilist _at_ gmail _dot_ com

You can find the archive of [http://libtorrent.rakshasa.no/wiki/UtilsRSSDler#tkt-changes-hdr older versions] at the bottom of this page.[[BR]]
Newest, stable version: [http://libtorrent.rakshasa.no/attachment/wiki/UtilsRSSDler/rssdler-0.3.1.py?format=raw rssdler-0.3.1.py]  [[BR]]

Also below is the [http://libtorrent.rakshasa.no/attachment/wiki/UtilsRSSDler/rssdlerDev.py?format=raw development version]. This may or may not run and may or may not be stable. There are times when it contains bugfixes for the latest version, and times when it is undergoing feature development and may be subject to crashes. The changelog will note the changes in the development version, but those changes may be buggy and/or incomplete. Feel free to test this version and email me the bug reports you have.

And by popular request: 
 * a [http://libtorrent.rakshasa.no/wiki/UtilsRSSDlerConfig commented config file] [[BR]]
 * As well as sample [http://libtorrent.rakshasa.no/wiki/UtilsRSSDlerPDF postDownloadFunctions] .  [[BR]]
 * Also, now an [http://libtorrent.rakshasa.no/attachment/wiki/UtilsRSSDler/rssdler.sh?format=raw init script]. Find instruction at the top of the script. Only works for versions >= 0.3.2, which is now in development.

You'll want to set downloadDir (see below) to the same directory as rtorrent's watch directory. Of course, you can download different rss feeds to different directories with the directory option for each thread. 

PLEASE READ THE [http://libtorrent.rakshasa.no/wiki/UtilsRSSDler#changelog CHANGELOG] BETWEEN UPGRADES. Settings may change that require some (minor) user intervention. These will be detailed between releases (as well as more esoteric things). """
	
def main():
	global printaction
	stringlist = [Bugs, Requests, Todo, ver032, ver031, ver030, ver024, ver023, ver022, ver021, ver020, ver010]
	a = ''
	for i in stringlist: a += i + ( os.linesep * 3)
	if printaction == 'wiki':
		sys.stdoutUTF.write( intro + u'\n\n\n')
		sys.stdoutUTF.write( unicode( ReFormatString( u'=== Help Message === #helpmessage\n{{{\n' + helpMessage + u'\n}}}\n\n\n' ) ) )
		sys.stdoutUTF.write( unicode( ReFormatString(u'=== Change Log === #changelog\n{{{\n' + a + u'\n}}}\n') ) )
	elif printaction == 'changeonly':
		sys.stdoutUTF.write( unicode( ReFormatString( a ) ) + u'\n' )
	else: print sys.argv, len(sys.argv), sys.argv[1]

if __name__ == '__main__':
	if len( sys.argv ) == 1: printaction = 'changeonly'
	if len( sys.argv ) >1 and sys.argv[1] == '-w': printaction = 'wiki'
	main()
	sys.exit()
