# Introduction #

Please read this guide if you would like to hack on g-pypi.

# Getting Started #

## Checking out trunk ##

Developers **without** commit access:

```
svn checkout http://g-pypi.googlecode.com/svn/trunk/ g-pypi-read-only
```


Developers **with** commit access:

```
svn checkout https://g-pypi.googlecode.com/svn/trunk/ g-pypi --username <username>
```

Use setuptools development mode:

```
cd g-pypi
sudo python setup.py develop
```

This will install g-pypi in /usr/bin and use your checkout directory's path.

# Coding Style #

  * Follow PEP 8 when possible
  * Run pylint before committing

# Unit Tests #

Run 'nosetests' from the SVN checkout directory. Make sure all tests pass before committing.

If you modify enamer.py in any way, make sure you write new unit tests if needed.

# Creating a Release #

Get out of setuptools development mode:

```
sudo python setup.py develop --uninstall
```

Create source tarball and upload to the Python Package Index:

```
python setup.py register sdist upload
```

Bump the ebuild and commit to the 'pythonhead' overlay.

Test the ebuild then go back to setuptools development mode:

```
sudo python setup.py develop
```