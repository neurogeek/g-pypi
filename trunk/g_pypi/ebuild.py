#!/usr/bin/env python
# pylint: disable-msg=C0103,C0301,E0611,W0511

# Reasons for pylint disable-msg's
# 
# E0611 - No name 'resource_string' in module 'pkg_resources'
#         No name 'BashLexer' in module 'pygments.lexers'
#         No name 'TerminalFormatter' in module 'pygments.formatters'
#         (False positives ^^^)
# C0103 - Variable names too short (p, pn, pv etc.)
#         (These can be ignored individually with some in-line pylint-foo.)
# C0301 - Line too long in some docstrings
"""

ebuild.py
=========

Creates an ebuild


"""

import re
import sys
import os
import logging
from time import localtime

from Cheetah.Template import Template
from pkg_resources import resource_string, WorkingSet, Environment, Requirement
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import TerminalFormatter, HtmlFormatter
from pygments.formatters import BBCodeFormatter

from g_pypi.portage_utils import (make_overlay_dir, find_s_dir, unpack_ebuild,
        get_portdir, get_workdir, find_egg_info_dir, valid_cpn,
        get_installed_ver, get_repo_names)
from g_pypi.config import MyConfig
from g_pypi import enamer
from g_pypi.__init__ import __version__ as VERSION


__docformat__ = 'restructuredtext'
__revision__ = '$Revision: 214 $'[11:-1].strip()

#Cheetah template
EBUILD_TEMPLATE = 'ebuild.tmpl'


def get_version():
    """
    Get g-pypi's version and revision

    @returns: string
    """
    return "%s (rev. %s)" % (VERSION, __revision__)


class Ebuild:

    """Contains ebuild"""
    
    def __init__(self, up_pn, up_pv, download_url):
        """Setup ebuild variables"""
        self.pypi_pkg_name = up_pn
        self.config = MyConfig.config
        self.options = MyConfig.options
        self.logger = logging.getLogger("g-pypi")
        self.metadata = None
        self.unpacked_dir = None
        self.ebuild_text = ""
        self.ebuild_path = ""
        self.warnings = []
        self.setup = []
        self.requires = []
        self.has_tests = None

        #Variables that will be passed to the Cheetah template
        self.vars = {
                'need_python': '',
                'python_modname': '',
                'description': '',
                'homepage': '',
                'rdepend': [],
                'depend': [],
                'use': [],
                'slot': '0',
                's': '',
                'keywords': self.config['keyword'],
                'inherit': ['distutils'],
                'esvn_repo_uri': '',
                }
        keyword = os.getenv('ACCEPT_KEYWORDS')
        if keyword:
            self.vars['keywords'] = keyword
        if self.options.subversion:
            #Live svn version ebuild
            self.options.pv = "9999"
            self.vars['esvn_repo_uri'] = download_url
            self.add_inherit("subversion")

	if up_pn.find('.') > -1:
	    self.vars['python_modname'] = self.options.my_pn = up_pn
	    up_pn = self.filter_pkgname(up_pn)
	    self.options.pn = up_pn

        ebuild_vars = enamer.get_vars(download_url, up_pn, up_pv, self.options.pn,
                self.options.pv, self.options.my_pn, self.options.my_pv, self.options.my_p)

        for key in ebuild_vars.keys():
            if not self.vars.has_key(key):
                self.vars[key] = ebuild_vars[key]

	self.vars['p'] = '%s-%s' % (self.vars['pn'], self.vars['pv'])

    def set_metadata(self, metadata):
        """Set metadata"""
        if metadata:
            self.metadata = metadata
        else:
            self.logger.error("Package has no metadata.")
            sys.exit(2)

    def get_ebuild_vars(self, download_url):
        """Determine variables from SRC_URI"""
        if self.options.pn or self.options.pv:
            ebuild_vars = enamer.get_vars(download_url, self.vars['pn'], 
                    self.vars['pv'], self.options.pn, self.options.pv)
        else:
            ebuild_vars = enamer.get_vars(download_url, self.vars['pn'], 
                    self.vars['pv'])
        if self.options.my_p:
            ebuild_vars['my_p'] = self.options.my_p

        if self.options.my_pv:
            ebuild_vars['my_pv'] = self.options.my_pv

        if self.options.my_pn:
            ebuild_vars['my_pn'] = self.options.my_pn

        if ebuild_vars.has_key('my_p'):
            self.vars['my_p'] = ebuild_vars['my_p']
            self.vars['my_p_raw'] = ebuild_vars['my_p_raw']
        else:
            self.vars['my_p'] = ''
            self.vars['my_p_raw'] = ebuild_vars['my_p_raw']
        if ebuild_vars.has_key('my_pn'):
            self.vars['my_pn'] = ebuild_vars['my_pn']
        else:
            self.vars['my_pn'] = ''

        if ebuild_vars.has_key('my_pv'):
            self.vars['my_pv'] = ebuild_vars['my_pv']
        else:
            self.vars['my_pv'] = ''
        self.vars['src_uri'] = ebuild_vars['src_uri']


    def add_metadata(self):
        """
        Extract DESCRIPTION, HOMEPAGE, LICENSE ebuild variables from metadata
        """
        #Various spellings for 'homepage'
        homepages = ['Home-page', 'home_page', 'home-page']
        for hpage in homepages:
            if self.metadata.has_key(hpage):
                self.vars['homepage'] = self.metadata[hpage]

        #There doesn't seem to be any specification for case
        if self.metadata.has_key('Summary'):
            self.vars['description'] = self.metadata['Summary']
        elif self.metadata.has_key('summary'):
            self.vars['description'] = self.metadata['summary']
        #Replace double quotes to keep bash syntax correct
        if self.vars['description'] is None:
            self.vars['description'] = ""
        else:
            self.vars['description'] = self.vars['description'].replace('"', "'")
    
        my_license = ""
        if self.metadata.has_key('classifiers'):
            for data in self.metadata['classifiers']:
                if data.startswith("License :: "):
                    my_license = get_portage_license(data)
        if not my_license:
            if self.metadata.has_key('License'):
                my_license = self.metadata['License']
            elif self.metadata.has_key('license'):
                my_license = self.metadata['license']
            my_license = "%s" % my_license
        if not is_valid_license(my_license):
            if "LGPL" in my_license:
                my_license = "LGPL-2.1"
            elif "GPL" in my_license:
                my_license = "GPL-2"
            else:
                self.add_warning("Invalid LICENSE.")

        self.vars['license'] = "%s" % my_license

    def add_warning(self, warning):
        """Add warning to be shown after ebuild is created"""
        if warning not in self.warnings:
            self.warnings.append(warning.lstrip())

    def post_unpack(self):
        """Check setup.py for:
           * PYTHON_MODNAME != $PN
           * setuptools install_requires or extra_requires
           # regex: install_requires[ \t]*=[ \t]*\[.*\], 

        """
        name_regex = re.compile('''.*name\s*=\s*[',"]([\w+,\-,\_]*)[',"].*''')
        module_regex = \
               re.compile('''.*packages\s*=\s*\[[',"]([\w+,\-,\_]*)[',"].*''')
        if os.path.exists(self.unpacked_dir):
            setup_file = os.path.join(self.unpacked_dir, "setup.py")
            if not os.path.exists(setup_file):
                self.add_warning("No setup.py found!")
                self.setup = ""
                return
            self.setup = open(setup_file, "r").readlines()

        setuptools_requires = module_name = package_name = None
        for line in self.setup:
            name_match = name_regex.match(line)
            if name_match:
                package_name = name_match.group(1)
            elif "packages=" in line or "packages =" in line:
                #XXX If we have more than one and only one is a top-level
                #use it e.g. "module, not module.foo, module.bar"
                mods = line.split(",")[0]
                #if len(mods) > 1:
                #    self.add_warning(line)
                module_match = module_regex.match(mods)
                if module_match:
                    module_name = module_match.group(1)
            elif ("setuptools" in line) and ("import" in line):
                setuptools_requires = True
                #It requires setuptools to install pkg
                self.add_depend("dev-python/setuptools")

        if setuptools_requires:
            self.get_dependencies(setup_file)
        else:
            self.logger.warn("This package does not use setuptools so you will have to determine any dependencies if needed.")
        
        if module_name and package_name:
            #    if module_name != package_name:
            self.vars['python_modname'] = module_name

    def get_unpacked_dist(self, setup_file):
        """
        Return pkg_resources Distribution object from unpacked package
        """
        os.chdir(self.unpacked_dir)
        os.system("/usr/bin/python %s egg_info" % setup_file)
        ws = WorkingSet([find_egg_info_dir(self.unpacked_dir)])
        env = Environment()
        return env.best_match(Requirement.parse(self.pypi_pkg_name), ws)

    def get_dependencies(self, setup_file):
        """
        Generate DEPEND/RDEPEND strings

        * Run setup.py egg_info so we can get the setuptools requirements
          (dependencies)

        * Add the unpacked directory to the WorkingEnvironment

        * Get a Distribution object for package we are isntalling

        * Get Requirement object containing dependencies

          a) Determine if any of the requirements are installed

          b) If requirements aren't installed, see if we have a matching ebuild
          with adequate version available

        * Build DEPEND string based on either a) or b)
        
        """

        #`dist` is a pkg_resources Distribution object
        dist = self.get_unpacked_dist(setup_file)
        if not dist:
            #Should only happen if ebuild had 'install_requires' in it but
            #for some reason couldn't extract egg_info
            self.logger.warn("Couldn't acquire Distribution obj for %s" % \
                    self.unpacked_dir)
            return

        for req in dist.requires():
            added_dep = False
            pkg_name = req.project_name.lower()
            if not len(req.specs):
                self.add_setuptools_depend(req)
                self.add_rdepend("dev-python/%s" % self.filter_pkgname(pkg_name))
                added_dep = True
                #No version of requirement was specified so we only add
                #dev-python/pkg_name
            else:
                comparator, ver = req.specs[0]
                self.add_setuptools_depend(req)
                if len(req.specs) > 1:
                    comparator1, ver = req.specs[0]
                    comparator2, ver = req.specs[1]
                    if comparator1.startswith(">") and \
                            comparator2.startswith("<"):
                        comparator = "="
                        self.add_warning("Couldn't resolve requirements. You will need to make sure the RDEPEND for %s is correct." % req)
                    else:
                        #Some packages have more than one comparator, i.e. cherrypy
                        #for turbogears has >=2.2,<3.0 which would translate to
                        #portage's =dev-python/cherrypy-2.2*
                        self.logger.warn(" **** Requirement %s has multi-specs ****" % req)
                        self.add_rdepend("dev-python/%s" % self.filter_pkgname(pkg_name))
                        break
                #Requirement.specs is a list of (comparator,version) tuples
                if comparator == "==":
                    comparator = "="
                if valid_cpn("%sdev-python/%s-%s" % (comparator, pkg_name, ver)):
                    self.add_rdepend("%sdev-python/%s-%s" % (comparator, self.filter_pkgname(pkg_name), ver))
                else:
                    self.logger.info(\
                            "Invalid PV in dependency: (Requirement %s) %sdev-python/%s-%s" \
                            % (req, comparator, pkg_name, ver)
                            )
                    installed_pv = get_installed_ver("dev-python/%s" % self.filter_pkgname(pkg_name))
                    if installed_pv:
                        self.add_rdepend(">=dev-python/%s-%s" % \
                                (self.filter_pkgname(pkg_name), installed_pv))
                    else:
                        #If we have it installed, use >= installed version
                        #If package has invalid version and we don't have
                        #an ebuild in portage, just add PN to DEPEND, no 
                        #version. This means the dep ebuild will have to
                        #be created by adding --MY_? options using the CLI
                        self.add_rdepend("dev-python/%s" % self.filter_pkgname(pkg_name))
                added_dep = True
            if not added_dep:
                self.add_warning("Couldn't determine dependency: %s" % req)

    def add_setuptools_depend(self, req):
        """
        Add dependency for setuptools requirement
        After current ebuild is created, we check if portage has an
        ebuild for the requirement, if not create it.
        @param req: requirement needed by ebuild
        @type req: pkg_resources `Requirement` object
        """
        self.logger.debug("Found dependency: %s " % req)
        if req not in self.requires:
            self.requires.append(req)

    def get_docs(self):
        """
        Add src_install for installing docs and examples if found
        and appropriate USE flags e.g. IUSE='doc examples' 
        
        """
        doc_dirs = ['doc', 'docs']
        example_dirs = ['example', 'examples', 'demo', 'demos']
        have_docs = False
        have_examples = False
        src_install = ''
        for ddir in doc_dirs:
            if os.path.exists(os.path.join(self.unpacked_dir, ddir)):
                have_docs = ddir
                self.add_use("doc")
                break

        for edir in example_dirs:
            if os.path.exists(os.path.join(self.unpacked_dir, edir)):
                have_examples = edir
                self.add_use("examples")
                break

        if have_docs or have_examples:
            src_install += '\tdistutils_src_install\n'
            if have_docs:
                src_install += '\tif use doc; then\n'
                src_install += '\t\tdodoc "${S}"/%s/*\n' % have_docs
                src_install += '\tfi\n'
            if have_examples:
                src_install += '\tif use examples; then\n'
                src_install += '\t\tinsinto /usr/share/doc/"${PF}"/examples\n'
                src_install += '\t\tdoins -r "${S}"/%s/*\n' % have_examples
                src_install += '\tfi'
        return src_install


    def get_src_test(self):
        """Create src_test if tests detected"""
        nose_test = '''\tPYTHONPATH=. "${python}" setup.py nosetests || die "tests failed"'''
        regular_test = '''\tPYTHONPATH=. "${python}" setup.py test || die "tests failed"'''

        for line in self.setup:
            if "nose.collector" in line:
                self.add_depend("test? ( dev-python/nose )")
                self.add_use("test")
                self.has_tests = True
                return nose_test
        #XXX Search for sub-directories
        if os.path.exists(os.path.join(self.unpacked_dir,
            "tests")) or os.path.exists(os.path.join(self.unpacked_dir,
                "test")):
            self.has_tests = True
            return regular_test

    def add_use(self, use_flag):
        """Add DEPEND"""
        self.vars['use'].append(use_flag)

    def add_inherit(self, eclass):
        """Add inherit eclass"""
        if eclass not in self.vars['inherit']:
            self.vars['inherit'].append(eclass)

    def add_depend(self, depend):
        """Add DEPEND ebuild variable"""
        if depend not in self.vars['depend']:
            self.vars['depend'].append(depend)

    def add_rdepend(self, rdepend):
        """Add RDEPEND ebuild variable"""
        if rdepend not in self.vars['rdepend']:
            self.vars['rdepend'].append(rdepend)

    def get_ebuild(self):
        """Generate ebuild from template"""
        self.set_variables()
        functions = {
            'src_unpack': "",
            'src_compile': "",
            'src_install': "",
            'src_test': ""
        }
        if not self.options.pretend and self.unpacked_dir: # and \
            #    not self.options.subversion:
            self.post_unpack() 
            functions['src_test'] = self.get_src_test() 
        # *_f variables are formatted text ready for ebuild
        self.vars['depend_f'] = format_depend(self.vars['depend'])
        self.vars['rdepend_f'] = format_depend(self.vars['rdepend'])
        self.vars['use_f'] = " ".join(self.vars['use'])
        self.vars['inherit_f'] = " ".join(self.vars['inherit'])
        template = resource_string(__name__, EBUILD_TEMPLATE)
        self.ebuild_text = \
                Template(template, searchList=[self.vars, functions]).respond()

    def set_variables(self):
        """
        Ensure all variables needed for ebuild template are set and formatted
        
        """
        if self.vars['src_uri'].endswith('.zip') or \
                self.vars['src_uri'].endswith('.ZIP'):
            self.add_depend("app-arch/unzip")
        if self.vars['python_modname'] == self.vars['pn']:
            self.vars['python_modname'] = ""
        self.vars['year'] = localtime()[0]
        #Add homepage, license and description from metadata
        self.add_metadata()
        self.vars['warnings'] = self.warnings
        self.vars['gpypi_version'] = get_version()

    def print_ebuild(self):
        """Print ebuild to stdout"""
        #No command-line set, config file says no formatting
        self.logger.info("%s/%s-%s" % \
                (self.options.category, self.vars['pn'],
        self.vars['pv']))
        if self.options.format == "none" or \
            (self.config['format'] == "none" and not self.options.format):
            self.logger.info(self.ebuild_text)
            return

        background = self.config['background']
        if self.options.format == "html":
            formatter = HtmlFormatter(full=True)
        elif self.config['format'] == "bbcode" or \
                self.options.format == "bbcode":
            formatter = BBCodeFormatter()
        elif self.options.format == "ansi" or self.config['format'] == "ansi":
            formatter = TerminalFormatter(bg=background)
        else:
            #Invalid formatter specified
            self.logger.info(self.ebuild_text)
            print "ERROR - No formatter"
            print self.config['format'], self.options.format
            return
        self.logger.info(highlight(self.ebuild_text,
                BashLexer(),
                formatter,
                ))
        self.show_warnings()

    def create_ebuild(self):
        """Write ebuild and update it after unpacking and examining ${S}"""
        #Need to write the ebuild first so we can unpack it and check for $S
        if self.write_ebuild(overwrite=self.options.overwrite):
            unpack_ebuild(self.ebuild_path)
            self.update_with_s()
            #Write ebuild again after unpacking and adding ${S}
            self.get_ebuild()
            #Run any tests if found
            #if self.has_tests:
            #    run_tests(self.ebuild_path)
            #We must overwrite initial skeleton ebuild
            self.write_ebuild(overwrite=True)
            self.print_ebuild()
            self.logger.info("Your ebuild is here: " + self.ebuild_path)
        #If ebuild already exists, we don't unpack and get dependencies 
        #because they must exist.
        #We should add an option to force creating dependencies or should
        #overwrite be used?
        return self.requires

    def write_ebuild(self, overwrite=False):
        """Write ebuild file"""
        #Use command-line overlay if specified, else the one in .g-pyprc
        if self.options.overlay:
            overlay_name = self.options.overlay
            overlays = get_repo_names()
            if overlays.has_key(overlay_name):
                overlay_path = overlays[overlay_name]
            else:
                self.logger.error("Couldn't find overylay/repository by that"+
                        " name. I know about these:")
                for repo in sorted(overlays.keys()):
                    self.logger.error("  " + repo.ljust(18) + overlays[repo])
                sys.exit(1)
        else:
            overlay_path = self.config['overlay']
        ebuild_dir = make_overlay_dir(self.options.category, self.vars['pn'], \
                overlay_path)
        if not ebuild_dir:
            self.logger.error("Couldn't create overylay ebuild directory.")
            sys.exit(2)
        self.ebuild_path = os.path.join(ebuild_dir, "%s.ebuild" % \
                self.vars['p'])
        if os.path.exists(self.ebuild_path) and not overwrite:
            #self.logger.error("Ebuild exists. Use -o to overwrite.")
            self.logger.warn("Ebuild exists, skipping: %s" % self.ebuild_path)
            return
        try:
            out = open(self.ebuild_path, "w")
        except IOError, err:
            self.logger.error(err)
            sys.exit(2)
        out.write(self.ebuild_text)
        out.close()
        return True

    def show_warnings(self):
        """Print warnings for incorrect ebuild syntax"""
        for warning in self.warnings:
            self.logger.warn("** Warning: %s" % warning)

    def update_with_s(self):
        """Add ${S} to ebuild if needed"""
        #if self.options.subversion:
        #    return
        self.logger.debug("Trying to determine ${S}, unpacking...")
        unpacked_dir = find_s_dir(self.vars['p'], self.options.category)
        if unpacked_dir == "":
            self.vars["s"] = "${WORKDIR}"
            return

        self.unpacked_dir = os.path.join(get_workdir(self.vars['p'], 
            self.options.category), unpacked_dir)
        if unpacked_dir and unpacked_dir != self.vars['p']:
            if unpacked_dir == self.vars['my_p_raw']:
                unpacked_dir = '${MY_P}'
            elif unpacked_dir == self.vars['my_pn']:
                unpacked_dir = '${MY_PN}'
            elif unpacked_dir == self.vars['pn']:
                unpacked_dir = '${PN}'

            self.vars["s"] = "${WORKDIR}/%s" % unpacked_dir

    def filter_pkgname(self, pkgname):
    	return pkgname.replace('.', '-')

def get_portage_license(my_license):
    """
    Map defined classifier license to Portage license

    http://cheeseshop.python.org/pypi?%3Aaction=list_classifiers
    We should probably check this list with every major list, eh?
    """
    my_license = my_license.split(":: ")[-1:][0]
    known_licenses = {
        "Aladdin Free Public License (AFPL)": "Aladdin",
        "Academic Free License (AFL)": "AFL-3.0",
        "Apache Software License": "Apache-2.0",
        "Apple Public Source License": "Apple",
        "Artistic License": "Artistic-2",
        "BSD License": "BSD-2",
        "Common Public License": "CPL-1.0",
        "GNU Free Documentation License (FDL)": "FDL-3",
        "GNU General Public License (GPL)": "GPL-2",
        "GNU Library or Lesser General Public License (LGPL)": "LGPL-2.1",
        "IBM Public License": "IBM",
        "Intel Open Source License": "Intel",
        "MIT License": "MIT",
        "Mozilla Public License 1.0 (MPL)": "MPL",
        "Mozilla Public License 1.1 (MPL 1.1)": "MPL-1.1",
        "Nethack General Public License": "nethack",
        "Open Group Test Suite License": "OGTSL",
        "Python License (CNRI Python License)": "PYTHON",
        "Python Software Foundation License": "PSF-2.4",
        "Qt Public License (QPL)": "QPL",
        "Sleepycat License": "DB",
        "Sun Public License": "SPL",
        "University of Illinois/NCSA Open Source License": "ncsa-1.3",
        "W3C License": "WC3",
        "zlib/libpng License": "ZLIB",
        "Zope Public License": "ZPL",
        "Public Domain": "public-domain"
        }
    if known_licenses.has_key(my_license):
        return known_licenses[my_license]
    else:
        return ""

def is_valid_license(my_license):
    """Check if license string matches a valid one in ${PORTDIR}/licenses"""
    return os.path.exists(os.path.join(get_portdir(), "licenses", my_license))


def format_depend(dep_list):
    """
    Return a formatted string containing DEPEND/RDEPEND

    @param dep_list: list of portage-ready dependency strings
    @return: formatted DEPEND or RDEPEND string ready for ebuild

    Format::

    DEPEND="dev-python/foo-1.0
        >=dev-python/bar-0.2
        dev-python/zaba"

    * First dep has no tab, has linefeed
    * Middle deps have tab and linefeed
    * Last dep has tab, no linefeed

    """

    if not len(dep_list):
        return ""

    output = dep_list[0] + "\n"
    if len(dep_list) == 1:
        output = output.rstrip()
    elif len(dep_list) == 2:
        output += "\t" + dep_list[-1]
    else:
        #Three or more deps
        middle = ""
        for dep in dep_list[1:-1]:
            middle += "\t%s\n" % dep
        output += middle + "\t" + dep_list[-1]
    return output

