#!/usr/bin/env python
import os
from distutils.core import setup
from distutils.command.build_scripts import build_scripts
from distutils.command.install_data import install_data

import rssdler

if os.name == "nt":
    install_init_rename = install_data
    class build_scripts_rename(build_scripts):
        """Renames scripts so they end with '.py' on Windows."""
        def run(self):
            build_scripts.run(self)
            for f in os.listdir(self.build_dir):
                fpath = os.path.join(self.build_dir, f)
                if not fpath.endswith('.py'):
                    if os.path.exists(fpath + '.py'):  os.unlink(fpath + '.py')
                    os.rename(fpath, fpath + '.py')
else:
    build_scripts_rename = build_scripts
    class install_init_rename(install_data):
        """Renames init files so they dont end with '.init' on Linux."""
        def run(self):
            print "Install Data Run"
            install_data.run(self)
            print "Install Dict %r" % self.__dict__
            for f in self.outfiles:
                if f.endswith('.init'):
                    fnew = f[:-5]
                    print "*** Rename File: %s to %s" % (f, fnew)
                    os.rename(f, fnew)

setup(
    name = 'rssdler',
    version = rssdler.getVersion(),
    description = rssdler.__doc__ ,
    long_description = """RSSDler - A Broadcatching Script
    Handles all RSS feeds supported by feedparser 0.9x, 1.0, and 2.0; CDF; and
    Atom 0.3 and 1.0
    Required: Python 2.4 or later
    Required: feedparser libtorrent
    Recommended: mechanize""",
    author = 'lostnihilist',
    author_email = 'lostnihilist@gmail.com',
    url = 'http://code.google.com/p/rssdler/',
    download_url = 'http://code.google.com/p/rssdler/downloads/list',
    license = 'GPLv2',
    platforms = ['Posix', 'Windows', 'OSX'],
    scripts = ('rssdler',),
    py_modules = ['rssdler',],
    data_files=[('/etc/init.d', ['rssdler.init',])],
    cmdclass = {'build_scripts': build_scripts_rename,
                'install_data': install_init_rename,},
)