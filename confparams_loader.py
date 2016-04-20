#!/usr/bin/python

import ConfigParser
import os

class ReadConfFile:
    config = None
    def __init__(self, fileName):
        """ read options from an absolute file path """

        self.config=ConfigParser.SafeConfigParser()
        # TRY ?
        self.config.readfp(open(fileName))


    def read_option(self,name,group='default'):

        value=self.config.get(group,name)
        return value
