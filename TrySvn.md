This page describes how to test out the version in SVN.

At this point, it is easiest (though not necessary) to store your configuration stuff in a folder ~/.rssdler, with your config file being config.txt in that folder. If you do not do this, make sure to set workingDir and specify config file as a command line option when running.

  * svn co http://rssdler.googlecode.com/svn/trunk/ rssdlersvn
  * cd rssdlersvn
  * sudo python setup.py install
    * on windows, sudo is not available. to install system wide, you need system administrator privileges.
  * cd ..
  * rm -r rssdlersvn
    * before deleting, there are files in there that could prove useful to you.
      * rssdler.sh can be used for system startup on nix systems, though not OSX due to the launchd system. See [StartupOSX](StartupOSX.md).
      * userFunctions.py can be saved in your workingDir (~/.rssdler by default). it contains a number of postDownload and postScanFunctions that people have found useful.