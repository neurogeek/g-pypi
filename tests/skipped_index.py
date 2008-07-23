#!/usr/bin/env python


"""

*** WARNING ***
*** WARNING ***
*** WARNING ***

This will attempt to create an ebuild for every single release on PyPI
which obviously will take a long time and require a decent amount of bandwidth

*** WARNING ***
*** WARNING ***
*** WARNING ***

"""

import pickle
import os

from yolk.pypi import CheeseShop


cheeseshop = CheeseShop()
PKG_INDEX = "pkg_index"

if os.path.exists(PKG_INDEX):
    full_index = pickle.load(open(PKG_INDEX, 'r'))
else:
    full_index = cheeseshop.search({"name":"foo"}, "or")
    pickle.dump(full_index, open(PKG_INDEX, "w"))

found = False
for pkg in full_index:
    found = True
    if found:
        if 'dev' in pkg['version']:
            #print pkg['name'], pkg['version']
            os.system('echo Testing %s' % pkg['name'].encode('utf-8'))
            os.system('g-pypi -Vo %s' % pkg['name'])
    #os.system('echo %s' % ('-' * 79))
