How to install rTorrent on a Debian-based distro with my packages:

  * If you have previously installed from source/svn, it would be a good idea to: "make uninstall."
  * If you have previously installed from .deb packages (e.g. dpkg, apt-get, aptitude, or other package manager), you do not need to worry about previous installations.
  * Download the .debs (urls assume you want 0.8.0/0.12.0, see "Downloads" page for a list):
    * wget http://rssdler.googlecode.com/files/rtorrent_0.8.0-0_i386.deb
    * wget http://rssdler.googlecode.com/files/libtorrent10_0.12.0-0_i386.deb
  * Use dpkg to install:
    * sudo dpkg -i libtorrent10\_0.12.0-0\_i386.deb rtorrent\_0.8.0-0\_i386.deb
    * you may get an error about missing dependencies. they should be listed out for you. To fix, perform:
      * sudo apt-get install list of dependencies
      * repeat the sudo dpkg... command above
  * (Optional) Cleanup:
    * rm rtorrent\_0.8.0-0\_i386.deb libtorrent10\_0.12.0-0\_i386.deb
  * Enjoy