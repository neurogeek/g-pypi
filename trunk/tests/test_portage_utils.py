
import os

from g_pypi.portage_utils import find_files, find_egg_info_dir


def test_find_files():
    print [egg for egg in find_files("passwd", "/etc")]

def test_find_egg_info_dir():
    udir = "/var/tmp/portage/dev-python/mako-0.1.7/work/Mako-0.1.7"
    assert find_egg_info_dir(udir) == os.path.join(udir, "lib")
