#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Functional CLI testing using the PyPI RSS feed to try to create an ebuild
for each package.

"""

__docformat__ = 'restructuredtext'

import urllib
import os
import sys

#TODO:
"""
Add switch for --pretend make default write ebuilds
Make option to write ebuild to tempdir and then cleanup after test is done




"""
if sys.version_info[0] == 2 and sys.version_info[1] == 5:
    #Python >=2.5 has elementtree 
    from xml.etree.cElementTree import iterparse
else:
    try:
        #Python <2.5 has elementtree as 3rd party module
        from cElementTree import iterparse
    except ImportError:
        print "You need to install cElementTree"
        sys.exit(2)

PYPI_URL = 'http://www.python.org/pypi?:action=rss'

#Packages we don't want to test. Mainly ones that require svn auth
SKIP = ['byCycleCore']

def get_pkg_ver(pv, add_quotes=True):
    """Return package name and version"""
    n = len(pv.split())
    if n == 2:
        #Normal package_name 1.0
        pkg_name, ver = pv.split()
    else:
        parts = pv.split()
        ver = parts[-1:]
        if add_quotes:
            pkg_name = "'%s'" % " ".join(parts[:-1])
        else:
            pkg_name = "%s" % " ".join(parts[:-1])
    return pkg_name, ver

def cli_test(pypi_xml):
    """Test the command-line tool"""
    for event, elem in iterparse(pypi_xml):
        if elem.tag == "title":
            if not elem.text.startswith('Cheese Shop recent updates'):
                    pkg_name, ver = get_pkg_ver(elem.text)
                    if pkg_name not in SKIP:
                        #If I don't use os.system for the echo's, all the msgs
                        #appear at the end of a log when redirecting output
                        os.system('echo Testing %s' % elem.text)
                        os.system('g-pypi -V %s' % pkg_name)
                        os.system('echo %s' % ('-' * 79))
            elem.clear()

if __name__ == "__main__":
    cli_test(urllib.urlopen(PYPI_URL))
