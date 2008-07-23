

from g_pypi.ebuild import *


def test_get_portage_license():
    """Convert classifier license to known portage license"""
    assert get_portage_license("License :: OSI Approved :: Zope Public License") == "ZPL"
    
    assert get_portage_license("License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)") ==  "LGPL-2.1"

    assert get_portage_license("License :: Public Domain") == "public-domain"
    assert get_portage_license("") == ""


def test_is_valid_license():
    """Check if license string matches a valid one in ${PORTDIR}/licenses"""
    assert is_valid_license("GPL") == False
    assert is_valid_license("GPL-2") == True

