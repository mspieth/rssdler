# Building lib/rTorrent as Debian Packages #

This page describes how to take a tarball of the libTorrent and rTorrent source, and make debian packages that should install well on the platform. This will likely not work exactly right when trying to compile from svn, only the major release tarballs.

You may be required to install the debian build tools, and the build process may complain about missing packages. Simply sudo apt-get install those as you get complaints.

  1. Create a workspace: mkdir buildrtorrent && cd buildrtorrent
  1. Get the tarballs (http://libtorrent.rakshasa.no/): wget urltolibtorrent && wget urltortorrent
  1. Unpack them: tar xzf lib/rtorrent\_version.tar.gz
  1. Get the most recent patches you can from the debian maintainer: http://debian.ghostbar.ath.cx/ (these are the lib/rtorrent\_version.diff.gz files)
  1. Apply the patch: cd libtorrent\_version && gunzip -c ../libtorrent\_version.diff.gz | patch -p1
  1. Change the version number (see note below): dch -i
  1. Make the build rules executable: chmod +x debian/rules
  1. Build the packages: dpkg-buildpackage -rfakeroot
  1. Install the packages: cd ../ && sudo dpkg -i libtorrent10\_version.deb libtorrent-dev\_version.deb
  1. Start over at step 5, but for rtorrent instead of libtorrent
  1. Cleanup the workspace (move the .debs if you want to keep them for later): cd ../ && rm -r buildrtorrent

Note: Instead of, for example 0.11.9-1 like the maintainer likes to do, I use -0, in case a more recent package comes into my source, I can use the official packages instead of mine.