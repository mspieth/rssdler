Note: Apologies for the highlighting. Get on Google to allow us [to disable syntax highlighting](http://code.google.com/p/support/issues/detail?id=44).
Text here may reflect changes made in svn that have not yet been officially released.
### Help Message ###
```
RSSDler is a Python based program to automatically grab the 
    link elements of an rss feed, aka an RSS broadcatcher. 

http://code.google.com/p/rssdler/

It happens to work just fine for grabbing RSS feeds of torrents, so called 
    torrent broadcatching. It may also used with podcasts and such. 
    Though designed with an eye toward rtorrent, it should work with any
    torrenting program that can read torrent files written to a directory. It 
    does not explicitly interface with rtorrent in anyway and therefore has no 
    dependency on it. 


Effort has been put into keeping the program from crashing from random errors
    like bad links and such. Try to be careful when setting up your 
    configuration file. If you are having problems, try to start with a very
    basic setup and slowly increase its complexity. You need to have a basic 
    understanding of regular expressions to setup the regex and download<x> 
    options, which is probably necessary to broadcatch in an efficient manner.
    If you do not know what and/or how to use regular expressions, google is 
    your friend. If you are having problems that you believe are RSSDler's 
    fault, post an issue:
    http://code.google.com/p/rssdler/issues/list 
    or post a message on: 
    http://groups.google.com/group/rssdler. 
    Please be sure to include as much information as you can.

Command Line Options:
    --config/-c can be used with all the options except --comment-config, --help
    --comment-config: Prints a commented config file to stdout
    --help/-h: print the short help message (command line options)
    --full-help/-f: print the complete help message (quite long)
    --run/-r: run according to the configuration file
    --runonce/-o: run only once then exit
    --daemon/-d: run in the background (Unix-like only)
    --kill/-k: kill the currently running instance (may not work on Windows)
    --config/-c: specify a config file (default /home/james/.rssdler/config.txt).
    --list-failed: Will list the urls of all the failed downloads
    --purge-failed: Use to clear the failed download queue. 
        Use when you have a download stuck (perhaps removed from the site or 
        wrong url in RSS feed) and you no longer care about RSSDler attempting 
        to grab it. Will be appended to the saved download list to prevent 
        readdition to the failed queue.
        Should be used alone or with -c/--config. Exits after completion.
    --list-saved: Will list everything that has been registered as downloaded.
    --purge-saved: Clear the list of saved downloads, not stored anywhere.
    --state/-s: Will return the process ID if another instance is running with.
        Otherwise exits with return code 1
        Note for Windows: will return the pid found in daemonInfo,
        regardless of whether it is currently running.
    --set-default-config: [No longer available. Deprecated]


Non-standard Python libraries used:
    feedparser: [REQUIRED] http://www.feedparser.org/
    mechanize: [RECOMMENDED] http://wwwsearch.sourceforge.net/mechanize/
    For debian based distros: 
    "sudo apt-get install python-feedparser python-mechanize"

    
Security Note: 
    I keep getting notes about people running as root. DO NOT DO THAT!
    

Configuration File:
There are two types of sections: global and threads. 
There can be as many thread sections as you wish, but only one global section.
global must be named "global." Threads can be named however you wish, 
except 'global,' and each name should be unique. 
With a couple of noted exceptions, there are three types of options:
    
Boolean Options: 'True' is indicated by "True", "yes", or "1". 
    "False" is indicated by "False", "no", or "0" (without the quotes)
Integer Options: Just an integer. 1, 2, 10, 2348. Not 1.1, 2.0, 999.3 or 'a'.
String Options: any string, should make sense in terms of the option 
    being provided (e.g. a valid file/directory on disk; url to rss feed)

Required indicates RSSDler will not work if the option is not set. 
Recommended indicates that the default is probably not what you want. 
Optional is not necessarily not recommended, just each case determines use 

Run with --comment-config to see what a configuration file would look like.
    e.g. rssdler --comment-config > .config.txt.sample


Global Options:
    
    downloadDir: [Recommended] A string option. Default is workingDir. 
        Set to a directory where downloaded files will go.
    workingDir: [Optional] A string option. Default is ${HOME}/.rssdler.
        Directory rssdler switches to, relative paths are relative to this
    minSize: [Optional] An integer option. Default None. Specify, in MB.
        the minimum size for a download to be. 
        Files less than this size will not be saved to disk.
    maxSize: [Optional] An integer option. Default None. Specify, in MB.
        the maximum size for a download to be. 
        Files greater than this size will not be saved to disk.
    log: [Optional] An integer option. Default 0. Write meassages a log file 
        (specified by logFile). See verbose for what options mean.
    logFile: [Optional] A string option. Default downloads.log. Where to log to.
    verbose: [Optional] An integer option, Default 3. Lower decreases output. 
        5 is absurdly verbose, 1 is major errors only. 
        Set to 0 to disable. Errors go to stderr, others go to stdout.
    cookieFile: [Optional] A string option. Default 'None'. The file on disk, 
        in Netscape Format (requires headers)(unless otherwise specified) 
        that has cookie data for whatever site(s) you have set that require it.
    cookieType: [Optional] A string option. Default 'MozillaCookieJar.' 
        Possible values (case sensitive): 'MozillaCookieJar', 'LWPCookieJar', 
        'MSIECookieJar', 'Firefox3', 'Safari', 'KDE'. Only mechanize supports MSIECookieJar.
        Program will exit with error if you try to use urllib and MSIECookieJar.
        Firefox3 requires that you use Python 2.5+, specifically sqlite3 must be
          available.
        Safari requires xml.dom.minidom and is experimental
    scanMins: [Optional] An integer option. Default 15. Values are in minutes. 
        The number of minutes between scans.
        If a feed uses the <ttl> tag, it will be respected. 
        If you have scanMins set to 10 and the site sets <ttl>900</ttl> 
        (900 seconds; 15 mins); then the feed will be scanned every other time.
        More formally, the effective scan time for each thread is:
        for X = global scanMins, Y = ttl: min{nX | nX >= Y ; n ∈ ℕ}
    sleepTime: [Optional] An integer option. Default 1. Values are in seconds. 
        Amount of time to pause between fetches of urls. 
        Some servers do not like when they are hit too quickly, 
        causing weird errors (e.g. inexplicable logouts).
    runOnce: [Optional] A boolean option, default False. 
        Set to True to force RSSDler to exit after it has scanned
    urllib: [Optional]. Boolean Option. Default False. Do not use mechanize.
        You lose several pieces of functionality. 
        1) Referers will no longer work. On most sites, this will not be a 
            problem, but some sites require referers and will deny requests 
            if the referer is not passed back to the site. 
        2) Some sites have various 'refresh' mechanisms that may redirect you 
            around before actually giving you the file to download. 
            Mechanize has the ability to follow these sites.
    noClobber: [Optional] Boolean. Default True. Overwrite file, or use new name
    rssFeed: [Optional] Boolean Option. Default False. Setting this option 
        allows you to create your own rss feed of the objects you have 
        downloaded. It's a basic feed, likely to not include links to the 
        original files. The related rss items (all are required if this is set 
        to True):
    rssLength: [Optional]  Integer. Default 20. An integer. How many entries 
        should the RSS feed store before it starts dropping old items. 0 means 
        that the feed will never be truncated.
    rssTitle: [Optional] A string. Default "some RSS Title".  Title of rssFeed.
    rssLink: [Optional]   string: Default 'nothing.com'. <link> on generated rss
    rssDescription: [Optional] A string. Default "Some RSS Description".
    rssFilename: [Optional] A string. Default 'rssdownloadfeed.xml'. 
        Where to save generated rss
    saveFile: [Optional] A string option. Default savedstate.dat. History data.
    lockPort: [Optional] An integer option. Default 8023. Port to lock saveFile
    daemonInfo: [Optional] A string. Default daemon.info. PID written here.
    umask: [Optional] An integer option. Default 077 in octal.
        Sets umask for file creation. PRIOR TO 0.4.0 this was read as BASE10.
        It is now read as octal like any sane program would.
        Do not edit this if you do not know what it does. 
    debug: [Optional] A boolean option. Default False. If rssdler is attached to
        a console-like device and this is True, will enter into a post-mortem 
        debug mode.
    rss: DEPRECATED, will no longer be processed.
    error: DEPRECATED, wil no longer be processed.

    
Thread options:
    link: [Required] A string option. Link to the rss feed.
    active:  [Optional] A boolean option. Default True. Whether Feed is scanned.
    maxSize: [Optional] An integer option, in MB. default is None. 
        A thread based maxSize like in global. If set to None, will default to 
        global's maxSize. 
        Other values override global, including 0 to indicate no maxSize.
    minSize: [Optional] An integer opton, in MB. default is None. 
        A thread based minSize, like in global. If set to None, will default to 
        global's minSize. 
        Other values override global, including 0 to indicate no minSize.
    noSave: [Optional] Boolean. Default: False. True: Never download seen files
    directory: [Optional] A string option. Default to None. If set, 
        overrides global's downloadDir, directory to download download objects.
    checkTime<x>Day: [Optional] A string option. Scan only on specified day
        Either the standard 3 letter abbreviation of the day of the week, 
        or the full name. One of Three options that will specify a scan time. 
        the <x> is an integer.
    checkTime<x>Start: [Optional] An integer option. Default: 0. 
        The hour (0-23) at which to start scanning on correlated day. 
        MUST specify checkTime<x>Day.
    checkTime<x>Stop: [Optional] An integer option. Default 23. 
        The hour (0-23) at which to stop scanning on correlated day. 
        MUST specify checkTime<x>Day.
    regExTrue: [Optional] A string option. Default None. Case insensitive
        If specified, will only download if a regex search of the download name
    regExTrueOptions: [Optional] STRING. Default None. Python re.OPTIONS
    regExFalse: [Optional] A string (regex) option. Default None. 
        If specified, will only download if pattern not in name
    regExFalseOptions: [Optional] A string option. Default None. re.OPTIONS
    postDownloadFunction: [Optional] A string option. Default None. 
        The name of a function, stored in userFunctions.py found in the current 
        working directory. Any changes to this requires a restart of RSSDler. 
        Calls the named function in userFunctions after a successful download 
        with arguments: directory, filename, rssItemNode, retrievedLink, 
        downloadDict, threadName. Exception handling is up to the function, 
        no exceptions are caught. Check docstrings (or source) of 
        userFunctHandling and callUserFunction to see reserved words/access to 
        RSSDler functions/classes/methods.
    preScanFunction: [Optional] See postScanFunction, only before scan.
    postScanFunction: [Optional] A string option. Default None. 
        The name of a function, stored in userFunctions.py. Any changes to this 
        requires a restart of RSSDler. Calls the named function after a scan of 
        a feed with arguments, page, ppage, retrievedLink, and threadName. 
        Exception Handling is up to the function, no exceptions are caught. 
        Check docstrings of userFunctHandling and callUserFunctions for more 
        information.
    The following options are ignored if not set (obviously). But once set, 
        they change the behavior of regExTrue (RET) and regExFalse (REF). 
        Without specifying these options, if something matches RET and doesn't 
        match REF, it is downloaded, i.e. RET and REF constitute sufficient 
        conditions to download a file. Once these are specified, RET and REF 
        become necessary (well, when download<x>(True|False) are set to True, 
        or a string for False) but not sufficient conditions for any given 
        download. If you set RET/REF to None, they are of course ignored and 
        fulfill their 'necessity.' You can specify these options as many times 
        as you like, by just changing <x> to another number. 
    download<x>: [Optional] No default. Where <x> is an integer,
        This is a 'positive' hit regex. This is required for download<x>true and
        download<x>false.
    download<x>False: [Optional] Default = True. 
        However, this is not strictly a boolean option. True means you want to 
        keep regExFalse against download<x>. If not, set to False, and there 
        will be no 'negative' regex that will be checked against. You can also 
        set this to a string (i.e. a regex) that will be a negative regex ONLY 
        for the corresponding download<x>. Most strings are legal, however the 
        following False/True/Yes/No/0/1 are reserved words when used alone and 
        are interpreted, in a case insensitive manner as Boolean arguments. 
        Requires a corresponding download<x> argument.
    download<x>True. [Optional] A Boolean option. default True. True checks 
        against regExTrue. False ignores regExTrue. Requires a corresponding 
        download<x> argument.
    download<x>Dir. [Optional] A String option. Default None. If specified, the 
        first of the download<x> tuples to match up with the download name, 
            downloads the file to the directory specified here. Full path is 
            recommended.
    download<x>Function. [Optional] A String option. Default None. just like 
        postDownloadFunction, but will override it if specified.
    download<x>MinSize. [Optional]. An Integer option. Default None. 
        Analogous to minSize.
    download<x>MaxSize. [Optional]. An integer option. Default None. 
        Analogous to maxSize.
    scanMins [Optional]. An integer option. Default 0. Sets the MINIMUM 
        interval at which to scan the thread. If global is set to, say, 5, and 
        thread is set to 3, the thread will still only be scanned every 5 
        minutes. Alternatively, if you have the thread set to 7 and global to 5,
        the actual interval will be 10. More formally, the effective scan time 
        for each thread is:
        for X = global scanMins, Y = thread scanMins, Z = ttl Mins: 
        min{nX | nX >= Y ; nX >= Z ; n ∈ ℕ }
    checkTime: DEPRECATED. Will no longer be processed.
    Programmers Note: 
        download<x>* stored in a DownloadItemConfig() Dict in .downloads. 
        checkTime* stored as tuple of (DoW, startHour, endHour)
    

Most options can be altered during runtime (i.e. by editing then saving the
    config file. Those that require a restart include: 
    - config file location
    - verbosity/logging level ; log file location
    - daemonInfo
    - debug
    - changes to userFunctions

A Netscape cookies file must have the proper header that looks like this:
# HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.


cookiedata ....

RSSDler - RSS Broadcatcher
Copyright (C) 2007, 2008, lostnihilist

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; under version 2 of the license.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

Contact for problems, bugs, and/or feature requests: 
  http://groups.google.com/group/rssdler or 
  http://code.google.com/p/rssdler/issues/list or
Author: lostnihilist <lostnihilist _at_ gmail _dot_ com> or 
"lostnihilist" on #libtorrent@irc.worldforge.org
```