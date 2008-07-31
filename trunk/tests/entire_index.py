#!/usr/bin/env python


"""

*** WARNING *** *** WARNING *** *** WARNING *** *** WARNING ***

This will attempt to create an ebuild for every single release on PyPI
which obviously will take a long time and consume a decent amount of bandwidth

The delay it takes to create an ebuild is long enough to keep PyPI from
getting hammered too hard. Be nice though.

*** WARNING *** *** WARNING *** *** WARNING *** *** WARNING *** 

Usage:

This script is good to run after making significant changes to g-pypi
after runing nosetests.

Add an overlay to /etc/make.conf PORTDIR_OVERLAY for '/tmp/overlay'
This script will create the overlay itself and the profiles dir with repo_name.

TODO:

Command-line option to create only n number of ebuilds. This could be
a range, 0-20 or 50-100 or random 10 etc.

Allow passing of options to g-pypi such as --debug, --quiet etc.

"""

import pickle
import os
import sys
from random import shuffle

from yolk.pypi import CheeseShop

PKG_INDEX = "pkg_index"

#A temporary overlay, gets created if it doesn't exist, and profiles/repo_name
TMP_OVERLAY = "/tmp/overlay"

REPO_NAME = 'g-pypi-tmp'

cheeseshop = CheeseShop()

if not os.path.exists(TMP_OVERLAY):
    os.mkdir(TMP_OVERLAY)

if not os.path.exists(TMP_OVERLAY + '/profiles'):
    os.mkdir(TMP_OVERLAY + '/profiles')
    fdesc = open(TMP_OVERLAY + '/profiles/repo_name', 'w')
    fdesc.write(REPO_NAME)
    fdesc.close()

if os.path.exists(PKG_INDEX):
    print "Reading PyPI cache... rm %s to re-download full index" % PKG_INDEX
    full_index = pickle.load(open(PKG_INDEX, 'r'))
else:
    print "Downloading entire PyPI index to cache..."
    full_index = cheeseshop.search({"name":""}, "or")
    pickle.dump(full_index, open(PKG_INDEX, "w"))

print "Randomizing cache..."
shuffle(full_index)

for pkg in full_index:
    try:
        os.system('echo Testing %s' % pkg['name'].encode('utf-8'))
        os.system('g-pypi -l %s -o %s' % (REPO_NAME, pkg['name']))
    except KeyboardInterrupt:
        sys.exit()

