#!/usr/bin/env python

# pylint: disable-msg=R0201
# method could be function but we need shared class data

"""

config.py
=========

Creates and reads config file using ConfigObj

        config['keyword'] = get_keyword()
        config['overlay'] = get_portdir_overlay()
        config['format'] = "ansi"

"""

import os
import logging

from configobj import ConfigObj

from g_pypi.portage_utils import get_keyword, get_portdir_overlay

__docformat__ = 'restructuredtext'

CONFIG_DIR = os.path.expanduser("~/.g-pypi")


class MyConfig:

    """
    Holds options from config file
    """

    config = None
    options = None
    logger = None

    def __init__(self):
        self.set_config(self.get_config())
    
    def get_config(self):
        """Read config file, create if it doesn't exist"""
        if not os.path.exists(self.get_rc_filename()):
            self.create_config()
        return ConfigObj(self.get_rc_filename()) 

    def create_config(self):
        """Create config file with defaults"""
        if not os.path.exists(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        self.create_config_obj()

    def create_config_obj(self):
        """Set defaults for ConigObj"""
        config = ConfigObj()
        config.filename = self.get_rc_filename()
        config['keyword'] = get_keyword()
        config['overlay'] = get_portdir_overlay()
        config['format'] = "ansi"
        config['background'] = "dark"
        config.write()
        self.set_config(config)
        #logger isn't set yet
        print "Your default keyword will be: %s " % \
                config['keyword']
        print "Your default overlay will be: %s " % \
                config['overlay']
        print "To change these edit: %s \n\n" % config.filename

    def set_config(self, config):
        """Set config"""
        MyConfig.config = config

    def set_options(self, options):
        """Set options"""
        MyConfig.options = options

    def get_rc_filename(self):
        """Return rc_file filename"""
        return os.path.join(CONFIG_DIR, "g-pypirc")

    def set_logger(self):
        """Set logger"""
        MyConfig.logger = logging.getLogger("g-pypi")
        if MyConfig.options.verbose:
            MyConfig.logger.setLevel(logging.INFO)
        elif MyConfig.options.quiet:
            MyConfig.logger.setLevel(logging.ERROR)
        elif MyConfig.options.debug:
            MyConfig.logger.setLevel(logging.DEBUG)
        else:
            MyConfig.logger.setLevel(logging.INFO)
        MyConfig.logger.addHandler(logging.StreamHandler())

    def get_logger(self):
        """Return logging object"""
        return MyConfig.logger

