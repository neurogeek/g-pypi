#!/usr/bin/env python


"""

enamer
======

Unit tests via nose

This module does all the trickery to determine MY_*, SRC_URI etc. variables

"""

import sys

#import functions we're testing implicitly so we can get an idea of coverage
from g_pypi.enamer import is_valid_uri, get_filename, get_vars, \
        parse_sourceforge_uri


def test_parse_sourceforge_uri():
    """
    Convert sourceforge URI to portage mirror URI

    """

    assert parse_sourceforge_uri("http://internap.dl.sourceforge.net/sourceforge/pythonreports/PythonReports-0.3.0.tar.gz") == \
            ("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz", 
                    "http://sourceforge.net/projects/pythonreports/")
    assert parse_sourceforge_uri("http://downloads.sourceforge.net/pythonreports/PythonReports-0.3.0.tar.gz") == \
            ("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                    "http://sourceforge.net/projects/pythonreports/")

    #Test abbreviated sf.net domain
    assert parse_sourceforge_uri("http://downloads.sf.net/pythonreports/PythonReports-0.3.0.tar.gz") == \
            ("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                    "http://sourceforge.net/projects/pythonreports/")

    #Non-sourceforge URI
    assert parse_sourceforge_uri("http://yahoo.com/pythonReports-0.3.0.tar.gz")\
            == ('', '')

def test_is_valid_uri():
    """Check if URI's addressing scheme is valid
     
     g-pypi will use http, ftp and mirror
    
    """

    assert is_valid_uri('http://foo.com/foo-1.0.tbz2') == True
    assert is_valid_uri('ftp://foo.com/foo-1.0.tbz2') == True
    assert is_valid_uri('mirror://sourceforge/foo-1.0.tbz2') == True
    assert is_valid_uri('http://foo.com/foo-1.0.tbz2#md5=2E3AF09') == True
    assert is_valid_uri('The Marked Men') == False
    assert is_valid_uri('svn://foo.com/trunk/foo') == True
    assert is_valid_uri('http://www.themarkedmen.com/') == True

def test_get_filename():
    """Return filename minus extension from src_uri"""
    assert get_filename("http://www.foo.com/pkgfoo-1.0.tbz2") == "pkgfoo-1.0"
    assert get_filename("http://www.foo.com/PKGFOO-1.0.tbz2") == "PKGFOO-1.0"
    assert get_filename("http://www.foo.com/pkgfoo_1.0.tbz2") == "pkgfoo_1.0"
    assert get_filename("http://www.foo.com/PKGFOO_1.0.tbz2") == "PKGFOO_1.0"
    assert get_filename("http://www.foo.com/pkg-foo-1.0_beta1.tbz2") == \
            "pkg-foo-1.0_beta1"
    assert get_filename("http://www.foo.com/pkg_foo-1.0lawdy.tbz2") == \
            "pkg_foo-1.0lawdy"
    assert get_filename("http://internap.dl.sourceforge.net/sourceforge/abeni/abeni-0.0.22.tar.gz") == "abeni-0.0.22"
    assert get_filename("http://internap.dl.sourceforge.net/sourceforge/dummy/StupidName_0.2.tar.gz") == "StupidName_0.2"



test_get_vars_docs = \
    """
    
    Test ``get_vars`` with all types of URI's we can come up with.

    Note:
    -----

    up_pn and up_pv are upstream's package name and package version respectively
    and not actually used in an ebuild. These are the names returned
    from yolklib/PyPI.

    
    """

def test_get_vars1():
    """
    Absolute best-case scenario determines $P from up_pn, up_pv
    We have a sanely named package and URI is perfect.

    """

    up_pn = "pkgfoo"
    up_pv = "1.0"
    uri = "http://www.foo.com/pkgfoo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': '',
         'my_pv': '',
         'my_p': '',
         'my_p_raw': '',
         'src_uri': 'http://www.foo.com/${P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars2():
    """
    (up_pn == pn) but URI has wrong case

    """
    up_pn = "pkgfoo"
    up_pv = "1.0"
    uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': 'PkgFoo',
         'my_pv': '',
         'my_p': '${MY_PN}-${PV}',
         'my_p_raw': 'PkgFoo-1.0',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars3():
    """ 
    (up_pn != pn) URI has correct case
    
    """
    up_pn = "PKGFoo"
    up_pv = "1.0"
    uri = "http://www.foo.com/pkgfoo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': '',
         'my_pv': '',
         'my_p': '',
         'my_p_raw': '',
         'src_uri': 'http://www.foo.com/${P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars4():
    """
    
    up_pn is not lower case but matches uri pn
    
    """

    pn = "pkgfoo"
    up_pn = "PKGFoo"
    up_pv = "1.0"
    uri = "http://www.foo.com/PKGfoo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv, pn)
    correct =\
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': 'PKGfoo',
         'my_pv': '',
         'my_p': '${MY_PN}-${PV}',
         'my_p_raw': 'PKGfoo-1.0',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv, pn)
    _get_vars(input_test, correct, results)


def test_get_vars5():
    """
    up_pn is not lower case and doesn't match uri case
    """
    pn = "pkgfoo"
    up_pn = "PKGFoo"
    up_pv = "1.0"
    uri = "http://www.foo.com/pkgFOO-1.0.tbz2"
    input_test = (uri, up_pn, up_pv, pn)
    correct =\
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': 'pkgFOO',
         'my_pv': '',
         'my_p': '${MY_PN}-${PV}',
         'my_p_raw': 'pkgFOO-1.0',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv, pn)
    _get_vars(input_test, correct, results)

def test_get_vars6():
    """
    pn has uppercase
    """
    pn = "pkgfoo"
    up_pn = "PkgFoo"
    up_pv = "1.0"
    pv = "1.0"
    my_pn = up_pn
    my_pv = ""
    uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv, pn, pv, my_pn)
    correct =\
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': 'PkgFoo',
         'my_pv': '',
         'my_p': '${MY_PN}-${PV}',
         'my_p_raw': 'PkgFoo-1.0',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv, pn, pv, my_pn, my_pv)
    _get_vars(input_test, correct, results)

def test_get_vars7():
    """
    up_pn has uppercase, no PN given
    """
    up_pn = "PkgFoo"
    up_pv = "1.0"
    pn = ""
    pv = "1.0"
    my_pv = ""
    my_pn = "PkgFoo"
    uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv, pn, pv, my_pn, my_pv)
    correct =\
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': 'PkgFoo',
         'my_pv': '',
         'my_p': '${MY_PN}-${PV}',
         'my_p_raw': 'PkgFoo-1.0',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv, pn, pv, my_pn, my_pv)
    _get_vars(input_test, correct, results)

def test_get_vars8():
    """
    Bad suffix on PV that can be removed
    """

    up_pn = "pkgfoo"
    up_pv = "1.0dev"
    uri = "http://www.foo.com/pkgfoo-1.0dev.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0',
         'p': 'pkgfoo-1.0',
         'my_pn': '',
         'my_pv': '${PV}dev',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0dev',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars9():
    """
    An existing -r123 suffix on upstream version
    is changed to _pre123
    """
    up_pn = "pkgfoo"
    up_pv = "1.0-r123"
    uri = "http://www.foo.com/pkgfoo-1.0-r123.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_pre123',
         'p': 'pkgfoo-1.0_pre123',
         'my_pn': '',
         'my_pv': '${PV/_pre/-r}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0-r123',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars10():
    """
    -r1234 suffix on PV that can be removed
    """
    up_pn = "pkgfoo"
    up_pv = "1.0.dev-r1234"
    uri = "http://www.foo.com/pkgfoo-1.0.dev-r1234.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_pre1234',
         'p': 'pkgfoo-1.0_pre1234',
         'my_pn': '',
         'my_pv': '${PV/_pre/.dev-r}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0.dev-r1234',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars11():
    """
    -r1234 suffix on PV that can be removed
    """
    up_pn = "pkgfoo"
    up_pv = "1.0dev-r1234"
    uri = "http://www.foo.com/pkgfoo-1.0dev-r1234.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_pre1234',
         'p': 'pkgfoo-1.0_pre1234',
         'my_pn': '',
         'my_pv': '${PV/_pre/dev-r}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0dev-r1234',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars12():
    """
    a4 suffix -> _alpha4
    """
    up_pn = "pkgfoo"
    up_pv = "1.0a4"
    uri = "http://www.foo.com/pkgfoo-1.0a4.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_alpha4',
         'p': 'pkgfoo-1.0_alpha4',
         'my_pn': '',
         'my_pv': '${PV/_alpha/a}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0a4',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars13():
    """
    b1 suffix -> _beta1
    """
    up_pn = "pkgfoo"
    up_pv = "1.0b1"
    uri = "http://www.foo.com/pkgfoo-1.0b1.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_beta1',
         'p': 'pkgfoo-1.0_beta1',
         'my_pn': '',
         'my_pv': '${PV/_beta/b}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0b1',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def test_get_vars14():
    """
    -b1 suffix -> _beta1
    """
    up_pn = "pkgfoo"
    up_pv = "1.0-b1"
    uri = "http://www.foo.com/pkgfoo-1.0-b1.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_beta1',
         'p': 'pkgfoo-1.0_beta1',
         'my_pn': '',
         'my_pv': '${PV/_beta/-b}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0-b1',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars15():
    """
    -a4 suffix -> _alpha4
    """
    up_pn = "pkgfoo"
    up_pv = "1.0-a4"
    uri = "http://www.foo.com/pkgfoo-1.0-a4.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_alpha4',
         'p': 'pkgfoo-1.0_alpha4',
         'my_pn': '',
         'my_pv': '${PV/_alpha/-a}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0-a4',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars16():
    """
    -rc3 suffix -> _rc3
    """
    up_pn = "pkgfoo"
    up_pv = "1.0-rc3"
    uri = "http://www.foo.com/pkgfoo-1.0-rc3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': '',
         'my_pv': '${PV/_rc/-rc}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0-rc3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars17():
    """
    rc3 suffix -> _rc3
    """
    up_pn = "pkgfoo"
    up_pv = "1.0rc3"
    uri = "http://www.foo.com/pkgfoo-1.0rc3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': '',
         'my_pv': '${PV/_rc/rc}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0rc3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars18():
    """
    .rc3 suffix -> _rc3
    """
    up_pn = "pkgfoo"
    up_pv = "1.0.rc3"
    uri = "http://www.foo.com/pkgfoo-1.0.rc3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': '',
         'my_pv': '${PV/_rc/.rc}',
         'my_p': '${PN}-${MY_PV}',
         'my_p_raw': 'pkgfoo-1.0.rc3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars19():
    """
    uppercase package name
    .rc3 suffix -> _rc3
    """
    up_pn = "PkgFoo"
    up_pv = "1.0.rc3"
    uri = "http://www.foo.com/PkgFoo-1.0.rc3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': 'PkgFoo',
         'my_pv': '${PV/_rc/.rc}',
         'my_p': '${MY_PN}-${MY_PV}',
         'my_p_raw': 'PkgFoo-1.0.rc3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars20():
    """
    -c3 suffix -> _rc3
    """
    up_pn = "PkgFoo"
    up_pv = "1.0-c3"
    uri = "http://www.foo.com/PkgFoo-1.0-c3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': 'PkgFoo',
         'my_pv': '${PV/_rc/-c}',
         'my_p': '${MY_PN}-${MY_PV}',
         'my_p_raw': 'PkgFoo-1.0-c3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars21():
    """
    uppercase package name
    .c3 suffix -> _rc3
    """
    up_pn = "PkgFoo"
    up_pv = "1.0.c3"
    uri = "http://www.foo.com/PkgFoo-1.0.c3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': 'PkgFoo',
         'my_pv': '${PV/_rc/.c}',
         'my_p': '${MY_PN}-${MY_PV}',
         'my_p_raw': 'PkgFoo-1.0.c3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars22():
    """
    uppercase package name
    c3 suffix -> _rc3
    """
    up_pn = "PkgFoo"
    up_pv = "1.0c3"
    uri = "http://www.foo.com/PkgFoo-1.0c3.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkgfoo',
         'pv': '1.0_rc3',
         'p': 'pkgfoo-1.0_rc3',
         'my_pn': 'PkgFoo',
         'my_pv': '${PV/_rc/c}',
         'my_p': '${MY_PN}-${MY_PV}',
         'my_p_raw': 'PkgFoo-1.0c3',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)

def test_get_vars23():
    """
    package name with a '.' in it, Zope packages have this often

    Problem:
         We can't have a '.' in PN

    Solution:
        We convert the . to a -

    Note: We also may need to use PYTHON_MODNAME='pkg.foo'

    Example:
        zope.foo -> zope-foo
    """
    up_pn = "pkg.foo"
    up_pv = "1.0"
    uri = "http://www.foo.com/pkg.foo-1.0.tbz2"
    input_test = (uri, up_pn, up_pv)
    correct = \
        {'pn': 'pkg-foo',
         'pv': '1.0',
         'p': 'pkg-foo-1.0',
         'my_pn': '${PN/./-}',
         'my_pv': '',
         'my_p': '${MY_PN}-${PV}',
         'my_p_raw': 'pkg.foo-1.0',
         'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
         }
    results = get_vars(uri, up_pn, up_pv)
    _get_vars(input_test, correct, results)


def _get_vars(input_test, correct, results):
    try:
        assert results == correct
    except AssertionError:
        print "=" * 79
        #Docstring from the calling function:
        print sys._getframe(1).f_code.co_name + ".__doc__"
        print sys._getframe(1).f_code.co_name.__doc__
        print "=" * 79
        print
        print input_test
        print "<var> -> <result> -> <correct>"
        print
        for key in results.keys():
            if results[key] != correct[key]:
                print "*", 
            print key, "->", results[key], "->", correct[key]

        raise AssertionError
