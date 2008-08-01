#!/usr/bin/env python
# pylint: disable-msg=C0301,W0613,W0612,C0103,E0611,W0511


"""

cli.py
======

Command-line code for g-pypi


"""

import sys
import optparse
import inspect

from pkg_resources import Requirement
try:
    #portage >=2.2
    from portage import exception as portage_exception
except ImportError:
    #portage <2.2
    from portage import portage_exception

from yolk.pypi import CheeseShop
from yolk.yolklib import get_highest_version
from yolk.setuptools_support import get_download_uri
from g_pypi.config import MyConfig
from g_pypi.ebuild import Ebuild
from g_pypi.portage_utils import ebuild_exists
from g_pypi.__init__ import __version__ as VERSION


__docformat__ = 'restructuredtext'
__revision__ = '$Revision: 215 $'[11:-1].strip()




class StdOut:

    """
    Filter stdout or stderr from specific modules
    So far this is just used for pkg_resources which is quite noisy
    """

    def __init__(self, stream, modulenames):
        self.stdout = stream
        #Modules to squelch
        self.modulenames = modulenames

    def __getattr__(self, attribute):
        if not self.__dict__.has_key(attribute) or attribute == '__doc__':
            return getattr(self.stdout, attribute)
        return self.__dict__[attribute]

    def write(self, inline):
        """
        Write a line to stdout if it isn't in a blacklist
        
        Try to get the name of the calling module to see if we want
        to filter it. If there is no calling module, use current
        frame in case there's a traceback before there is any calling module
        """
        frame = inspect.currentframe().f_back
        if frame:
            mod = frame.f_globals.get('__name__') 
        else:
            mod = sys._getframe(0).f_globals.get('__name__') 
        if not mod in self.modulenames:
            self.stdout.write(inline)

    def writelines(self, inline):
        """Write multiple lines"""
        for line in inline:
            self.write(line)


class GPyPI(object):

    """
    Main class for command-line interface
    """

    def __init__(self, package_name, version, options, logger):
        """
        @param package_name: case-insensitive package name
        @type package_name: string

        @param version: package version
        @type version: string

        @param options: command-line options
        @type options: OptParser config object

        @param logger: message logger
        @type logger: logger object
        """

        self.package_name = package_name
        self.version = version
        self. options = options
        self.logger = logger
        self.tree = [(package_name, version)]
        self.pypi = CheeseShop()
        self.create_ebuilds()

    def raise_error(self, msg):
        """
        Cleanup, print error message and raise GPyPiErro

        @param msg: Error message
        @type msg: string

        """
        #XXX: Call function to do 'ebuild pkg-ver.ebuild clean' etc.
        #to clean up unpacked ebuilds

        self.logger.error("Error: " + msg)
        sys.exit(1)

    def create_ebuilds(self):
        """
        Create ebuild for given package_name and any ebuilds for dependencies
        if needed. If no version is given we use the highest available.
        """
        #Create first ebuild then turn off overwrite in case a dependency
        #ebuild already exists
        #self.logger.debug("Creating dep tree...")
        while len(self.tree):
            (project_name, version) = self.tree.pop(0)
            #self.logger.debug(self.tree)
            #self.logger.debug("%s %s" % (project_name, version))
            self.package_name = project_name
            self.version = version
            requires = self.do_ebuild()
            #print "REQUIRES", requires
            if requires:
                for req in requires:
                    if self.options.no_deps or ebuild_exists("dev-python/%s" % req.project_name.lower()):
                        if not self.options.no_deps:
                            self.logger.info("Skipping dependency (exists): %s" % req.project_name)
                    else:
                        self.add_dep(req.project_name)
            self.options.overwrite = False

    def add_dep(self, project_name):
        '''Add dependency'''
        pkgs = []
        if len(self.tree):
            for deps in self.tree:
                pkgs.append(deps[0])

        if project_name not in pkgs:
            self.tree.append((project_name, None))
            #self.logger.info("Dependency needed: %s" % project_name)

    def url_from_pypi(self):
        """
        Query PyPI for package's download URL
        
        @returns: source URL string
        """

        try:
            return self.pypi.get_download_urls(self.package_name, self.version, pkg_type="source")[0]
        except IndexError:
            return None

    def find_uri(self, method="setuptools"):
        """
        Returns download URI for package
        If no package version was given it returns highest available
        Setuptools should find anything xml-rpc can and more.

        @param method: download method can be 'xml-rpc', 'setuptools', or 'all'
        @type method: string

        @returns download_url string 
        """
        download_url = None

        if method == "all" or method == "xml-rpc":
            download_url = self.url_from_pypi()

        if (method == "all" or method == "setuptools") and not download_url:
            #Sometimes setuptools can find a package URI if PyPI doesn't have it
            download_url = self.uri_from_setuptools()
        return download_url

    def get_uri(self, svn=False):
        """
        Attempt to find a package's download URI

        @returns: download_url string

        """
        download_url = self.find_uri()

        if not download_url:
            self.raise_error("Can't find SRC_URI for '%s'." %  self.package_name)

        self.logger.debug("Package URI: %s " % download_url)
        return download_url

    def uri_from_setuptools(self):
        """
        Use setuptools to find a package's URI
        
        """
        try:
            req = Requirement.parse(self.package_name)
        except ValueError:
            self.raise_error("The package seems to have a ridiculous name or version, can't proceed.")

        if self.options.subversion:
            src_uri = get_download_uri(self.package_name, "dev", "source")
        else:
            src_uri = get_download_uri(self.package_name, self.version, "source")
        if not src_uri:
            self.raise_error("The package has no source URI available.")
        return src_uri

    def verify_pkgver(self):
        """
        Query PyPI to make sure we have correct case for package name
        """


    def do_ebuild(self):
        """
        Get SRC_URI using PyPI and attempt to create ebuild

        @returns: tuple with exit code and pkg_resources requirement

        """
        #Get proper case for project name:
        (package_name, versions) = self.pypi.query_versions_pypi(self.package_name)
        if package_name != self.package_name:
            self.package_name = package_name


        if self.version and (self.version not in versions):
            self.logger.error("Can't find package for version:'%s'." %  self.version)
            return
        else:
            self.version = get_highest_version(versions)

        download_url = self.get_uri()
        try:
            ebuild = Ebuild(self.package_name, self.version, download_url)

        except portage_exception.InvalidVersionString:
            self.logger.error("Can't determine PV, use -v to set it: %s-%s" % \
                    (self.package_name, self.version))
            return
        except portage_exception.InvalidPackageName:
            self.logger.error("Can't determine PN, use -n to set it: %s-%s" % \
                    (self.package_name, self.version))
            return

        ebuild.set_metadata(self.query_metadata())

        ebuild.get_ebuild()
        if self.options.pretend:
            print
            ebuild.print_ebuild()
            return
        return ebuild.create_ebuild()

    def query_metadata(self):
        """
        Get package metadata from PyPI

        @returns: metadata text

        """

        if self.version:
            return self.pypi.release_data(self.package_name, self.version)
        else:
            (pn, vers) = self.pypi.query_versions_pypi(self.package_name)
            return self.pypi.release_data(self.package_name, get_highest_version(vers))

def parse_pkg_ver(package_spec):
    """
    Return tuple with package_name and version from CLI args

    @param package_spec: pkg_resources package spec
    @type package_spec: string

    @returns: tupe with pkg_name and version

    """

    arg_str = ("").join(package_spec)
    if "==" not in arg_str:
        #No version specified
        package_name = arg_str
        version = None
    else:
        (package_name, version) = arg_str.split("==")
        package_name = package_name.strip()
        version = version.strip()
    return (package_name, version)

def show_version():
    """
    Print g-pypi's version
    """
    print "g-pypi version %s (rev. %s)" % (VERSION, __revision__)

def main():
    """Parse command-line options and do it."""

    usage = "usage: %prog [options] <package_name[==version]>"
    opt_parser = optparse.OptionParser(usage=usage)

    opt_parser.add_option("-p", "--pretend", action='store_true', dest=
                         "pretend", default=False, help=
                         "Print ebuild to stdout, don't write ebuild file, \
                         don't download SRC_URI.")

    opt_parser.add_option("-o", "--overwrite", action='store_true', dest=
                         "overwrite", default=False, help=
                         "Overwrite existing ebuild.")

    opt_parser.add_option("--no-deps", action='store_true', dest=
                         "no_deps", default=False, help=
                         "Don't create ebuilds for any needed dependencies.")

    opt_parser.add_option("-c", "--portage-category", action='store', dest=
                         "category", default="dev-python", help=
                         "Specify category to use when creating ebuild. Default is dev-python")

    opt_parser.add_option("-n", "--PN", action='store', dest=
                         "pn", default=False, help=
                         "Specify PN to use when naming ebuild.")

    opt_parser.add_option("-v", "--PV", action='store', dest=
                         "pv", default=False, help=
                         "Specify PV to use when naming ebuild.")

    opt_parser.add_option("--MY_PV", action='store', dest=
                         "my_pv", default=False, help=
                         "Specify MY_PV")

    opt_parser.add_option("--MY_PN", action='store', dest=
                         "my_pn", default=False, help=
                         "Specify MY_PN")

    opt_parser.add_option("--MY_P", action='store', dest=
                         "my_p", default=False, help=
                         "Specify MY_P")

    opt_parser.add_option("-l", "--overlay", action='store', dest=
                         'overlay', metavar='OVERLAY_NAME', default=None, help=
                         'Specify overy to use by name ($OVERLAY/profiles/repo_name)')

    opt_parser.add_option("--format", action='store', dest=
                         "format", default=None, help=
                         "Format when printing to stdout: ansi, html, bbcode, or none")
    opt_parser.add_option("-s", "--subversion", action='store_true', dest=
                         "subversion", default=False, help=
                         "Create live subversion ebuild if repo is available.")

    opt_parser.add_option("-V", "--verbose", action='store_true', dest=
                         "verbose", default=False, help=
                         "Show more output.")
    opt_parser.add_option("-q", "--quiet", action='store_true', dest=
                         "quiet", default=False, help=
                         "Show less output.")

    opt_parser.add_option("-d", "--debug", action='store_true', dest=
                         "debug", default=False, help=
                         "Show debug information.")


    opt_parser.add_option("--version", action='store_true', dest=
                         "version", default=False, help=
                         "Show g-pypi version and exit.")

    (options, package_spec) = opt_parser.parse_args()
    if options.version:
        show_version()
        return

    #Turn off all output from the pkg_resources module by default
    sys.stdout = StdOut(sys.stdout, ['distutils.log'])
    sys.stderr = StdOut(sys.stderr, ['distutils.log'])

    config = MyConfig()
    config.set_options(options)
    config.set_logger()
    logger = config.get_logger()
    
    if not package_spec:
        opt_parser.print_help()
        logger.error("\nError: You need to specify a package name at least.")
        return 1
    (package_name, version) = parse_pkg_ver(package_spec)
    gpypi = GPyPI(package_name, version, options, logger)

if __name__ == "__main__":
    sys.exit(main())

