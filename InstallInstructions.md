Installing RSSDler is pretty easy, though its ease depends on what platform you are on. First, covering the pre-requisites:

  1. Python (required):
    * If you are using Linux, you likely have python available in your distributions repository. This should be as easy as "apt-get install python" or "yum install python" or similar.
    * Otherwise, visit the [python download page](http://www.python.org/download/), and download the installer appropriate for your system. Open it and follow the on-screen instructions.
    * Optional: Many people find [EasyInstall](http://peak.telecommunity.com/DevCenter/EasyInstall) the easiest way to install 3rd party modules. I have not tested EasyInstall, but it should work well. [Installation Instructions](http://peak.telecommunity.com/DevCenter/EasyInstall#installing-easy-install).
    * Further instructions can be found at python.org as well as [diveintopython](http://diveintopython.org/installing_python/index.html).
  1. Feedparser (required):
    * Again, on Linux, this is probably in your distributions repository: "apt-get install python-feedparser" or similar will probably Just Work (tm).
    * "easyinstall feedparser" on the command line
    * Otherwise, go to the [feedparser download page](http://code.google.com/p/feedparser/downloads/list),
      * unpack the file to C:\feedparser, or similar,
      * go to the command line (windows: start, run, cmd 

&lt;enter&gt;

)
      * cd to the directory you unpacked feedparser to (e.g. "cd C:\feedparser")
      * run python on the setup.py file with the install option: "C:\Python25\python.exe setup.py install" or similar
  1. Mechanize (recommended, but not required):
    * Again, on linux, this is probably as easy as "apt-get install python-mechanize" or similar.
    * "easyinstall mechanize" on the command line
    * Otherwise, follow the similar procedure for feedparser for [mechanize](http://wwwsearch.sourceforge.net/mechanize/#source)

Now that that is done, (and it only needs to be done once), we install RSSDler:
  * make a directory in your home folder to keep all your rssdler related files (not necessarily your downloads) in, preferably .rssdler (the defaults assume that is what it will be).
  * [Download](http://code.google.com/p/rssdler/downloads/list) the rssdler.tar.gz and unpack it: tar xvzf rssdler-X.Y.Z.tar.gz.
  * cd rssdlerXYZ
  * sudo python setup.py install
  * You have now installed all the requirements for RSSDler as well as RSSDler itself
  * You can run it with just "rssdler -r" anywhere, and it will find your config file at ~/.rssdler/config.txt, if you installed it there. Otherwise, specify the configuration file with -c.
  * Take a look at the HelpMessage and CommentedConfig to help in the creation of a suitable configuration file