#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
ComponentType.py: contains a class for representing component types in the ITkPD
Created: 2018/10/18
Updated: 2019/01/28
'''

__author__  = 'Matthew Basso'
__email__   = 'matthew.joseph.basso@cern.ch'

from itk_pdb.databaseUtilities import commands as dbCommands, INFO
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

class ComponentType(object):

    def __init__(self, project, code, verbose = True, get_immediately = False):

        '''
        A class for representing component types in the ITkPD.
            
        Args:
            project (str): the code for the project, choose ['S'|'P'|'CM'|'CE'].
            code (str): the code for the component type.
            verbose (bool): enable printing for all functions in the class (default: True).
            get_immediately (bool): immediately fetch the json for the test type (default: False).
        '''

        # Read in our args
        self.project = project
        self.code = code
        self.verbose = verbose

        # Initialize json to None
        self.json = None

        # Fetch our json immediately if get_immediately
        if get_immediately:
            self.get()

    def get(self):

        '''
        Fetch the json for the component type from the ITkPD.
        '''

        self.json = dbCommands['getComponentTypeByCode'].run(project = self.project, code = self.code)

    def printJSON(self, verbose = None):

        '''
        Pretty print the json for the component type.
        '''

        # Pretty print the json
        if self.verbose:
            INFO('Printing JSON for (project, component type) code (\'{0}\', \'{1}\'):\n'.format(self.project, self.code))
            pp.pprint(self.json)
            print('')
        else:
            pp.pprint(self.json)
