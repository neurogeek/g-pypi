# !!! Important update !!! #

04/12/2011 - g-pypi2 was sponsored as a Google Summer of Code project in 2010. The student who worked on this was Domen Kožar. We're now working on making g-pypi2 g-pypi 1.0. Thanks to Domen for keeping g-pypi alive and well. The documentation for Domen's work is here http://g-pypi.readthedocs.org/ and contains quite a few new features and changes than listed below.

# g-pypi #

**g-pypi creates ebuilds for Gentoo Linux using information in PyPI (Python Package Index).**


## Features ##

  * Write ebuilds to your overlay or to stdout
  * Determines DEPEND/RDEPEND if they are declared with setuptools install\_requires and creates ebuilds for dependencies
  * Automagically calculates MY\_P, MY\_PN, MY\_PV in many cases.
  * Adds PYTHON\_MODNAME variable if the module != PN
  * Determines ${S} for you by unpacking ebuild
  * Can determine SRC\_URI without downloading the package
  * Scans setup.py for tests and adds src\_test() including checks for nose tests and adds dependency on nose and USE flag
  * Scans setup.py for setuptools and warns if it finds 'extras\_requires' and other info
  * Convert Source Forge URL to mirror://sourceforge format
  * Maps over 20 known licenses in Python classifiers to proper portage-known licenses ($PORTDIR/licenses)
  * Can output ebuild to stdout in ansi color, bbcode, or html
  * Uses Cheetah for the ebuild template for easy customability

g-pypi is similar to [g-cpan](http://www.gentoo.org/proj/en/perl/g-cpan.xml) but has a few differences:

  * ebuilds are created but not emerged
  * Sometimes g-pypi won't work because package authors aren't required to put download links in The Cheese Shop
  * g-pypi has Easter eggs from the Monty Python Cheese Shop sketch
  * g-pypi does not download a cpan-like index so there is no initial configuration in that regard.
  * CPAN seems to have a uniform naming and versioning scheme, making it possible to automatically convert to portage's package naming scheme. Unfortunately anyone can index a Python package on PyPI using crazy names and versions, so you may have to manually set PV with the --PV option etc.


## Basic Usage ##

Write ebuild and ebuilds for dependencies to your overlay:

```
  $ g-pypi package_name
```

Output ebuild to stdout:

```
  $  g-pypi -p package_name
```

By default your first overlay listed in /etc/make.conf PORTDIR\_OVERLAY is used. If you want to use a different one, edit ~/.g-pypi/g-pypirc

By default your first KEYWORD listed in /etc/make.conf KEYWORDS is used. If you want to use a different one, edit ~/.g-pypi/g-pypirc

You can over-ride some variables if g-pypi can't figure out the PN, PV, MY\_P**etc.**

-n or --PN=package-name
-v or --PV=version
--MY\_P=my\_p
--MY\_PN=my\_pn
--MY\_PV=my\_pv

If you don't specify a portage category with '-c' the ebuild will be placed in dev-python

Use '-V' for verbose output for debugging.

## Installation ##

g-pypi is available in pythonhead's public overlay:

If you haven't emerged and configured app-portage/layman:

```
   $ emerge layman
   $ echo "source /usr/portage/local/layman/make.conf" >> /etc/make.conf
```

then:

```
   $ layman --add pythonhead
   $ emerge g-pypi
```

## Development ##

If you want to hack on g-pypi, check out the trunk then deploy in setuptools development mode:

```
$ svn co svn checkout http://g-pypi.googlecode.com/svn/trunk/ g-pypi-read-only
$ sudo python setup.py develop --no-deps
```

(Developers see instructions on the 'Source' tab to authenticate)

Now /usr/bin/g-pypi uses your subversion checkout directory and you're ready to roll.


## License ##

Copyright Rob Cakebread released under the terms of the GNU Public License Version 2