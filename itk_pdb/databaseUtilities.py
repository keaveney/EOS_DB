#!/usr/bin/env python
# databaseUtilities -- a collection of useful functions for interfacing with the ITk Production Database
# Created: 2018/07/24, Updated: 2019/01/28
# Written by Matthew Basso

import itk_pdb.dbAccess as dbAccess, os, sys, collections

# Fix the str (python3) versus basestring (Python2) issue
# See: https://stackoverflow.com/questions/11301138/how-to-check-if-variable-is-string-with-python-2-and-3-compatibility
try:
    basestring
except NameError:
    basestring = str

# Check if the ITK_DB_AUTH environment variable exists
def checkITkDBAuth():
    if os.getenv('ITK_DB_AUTH'):
        dbAccess.token = os.getenv('ITK_DB_AUTH')
    pass

# Define our error class
class Error(Exception):
    def __init__(self, message = None):
        self.message = message

# See: https://stackoverflow.com/questions/287871/print-in-terminal-with-colors
# For additional colours, see: https://stackoverflow.com/questions/15580303/python-output-complex-line-with-floats-colored-by-value
class Colours():
    GREEN       = '\033[92m'
    WHITE       = '\033[97m'
    YELLOW      = '\033[93m'
    RED         = '\033[91m'
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'
    UNDERLINE   = '\033[4m'

# Define our general print function
def printMessage(header, colour, message):
    print('[{0}{1}{2}{3}]$ {4}'.format(colour, Colours.BOLD, header, Colours.ENDC, message))

# Define some more specific pretty printing functions
def INFO(message):
    printMessage('INFO', Colours.WHITE, message)

def PROMPT(message):
    printMessage('PROMPT', Colours.WHITE, message)

def WARNING(message):
    printMessage('WARNING', Colours.YELLOW, message)

def ERROR(message):
    printMessage('ERROR', Colours.RED, message)

def STATUS(message, success):
    if success:
        printMessage('STATUS', Colours.GREEN, message)
    else:
        printMessage('STATUS', Colours.RED, message)

# Define a useful function to ensure all strings in the database output have the proper encoding
# Copied from: https://stackoverflow.com/questions/1254454/fastest-way-to-convert-a-dicts-keys-values-from-unicode-to-str
# For background on the issue of unicode, see: https://stackoverflow.com/questions/11279331/what-does-the-u-symbol-mean-in-front-of-string-values
def convertToUTF8(data):

    # Check if data is a basestring and, if so, encode it with utf-8
    if isinstance(data, basestring):
        return data.encode('utf-8')

    # If data is a mapping (e.g., dict), apply the conversion recursively to each item in the mapping and cast to dict
    elif isinstance(data, collections.Mapping):
        return dict(map(convertToUTF8, data.iteritems()))

    # If data is an iterable (e.g., list), apply the conversion recursively to each item in the iterable and cast it back to the same type
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convertToUTF8, data))

    else:
        return data

# This function works similarly to the above function (I think...) except it will take a binary object and convert it to utf-8
def convertToUTF8FromBinary(data):

    try:
        return data.decode('utf-8')

    except AttributeError:

        if isinstance(data, collections.Mapping):
            return dict(map(convertToUTF8, iter(data.items())))

        elif isinstance(data, collections.Iterable):
            return type(data)(map(convertToUTF8, data))

        else:
            return data

# Define our StandardCommand object
# This class is based on Bruce Gallop's StandardCommand class in read_db.py with a few modifications
class StandardCommand(object):

    # Define our init function
    # required_args := keyword arguments requied by the uuCMD
    # allowed_args := keyword arguments allowed by the uuCMD (not exhaustive)
    def __init__(self, *args):
        self._action = args[0]
        self._method = args[1]
        self._required_args = args[3]
        self._allowed_args = self._required_args + [arg for arg in args[2] if arg not in self._required_args]

    # Check that the arguments pass to run are (a) allowed and (b) meet the required arguments
    # Arguments like '<something>__<something else>' create a dictionary <something> containing a dictionary <something else>
    def __checkArgs(self, **kwargs):
        for arg in self._required_args:
            if arg not in kwargs.keys():
                print('databaseUtilities.py: Keyword argument \'{0}\' is required for command \'{1}\' -- EXITING'.format(arg, self._action))
                sys.exit(1)
        for k in kwargs.keys():
            if k not in self._allowed_args:
                print('databaseUtilities.py: Keyword argument \'{0}\' is not allowed for command \'{1}\' -- EXITING'.format(k, self._action))
                sys.exit(1)
            elif '__' in k:
                k_outer = k.split('__')[0]
                k_inner = k.split('__')[1]
                if k_outer not in kwargs.keys():
                    kwargs[k_outer] = {}
                kwargs[k_outer][k_inner] = kwargs[k]
                del kwargs[k]
        return kwargs

    # Define our run function, which sends method as a uuCMD to the database
    def run(self, **kwargs):

        # Disable argument checking for uploadTestRunResults (kind of hacky? -- though dictionary can be highly varied!)
        if self._action != 'uploadTestRunResults':
            kwargs = self.__checkArgs(**kwargs)

        data = dbAccess.doSomething(self._action, method = self._method, data = kwargs)

        # The output from requests with python3 is already in utf-8, so we don't want to convert it further
        # I don't understand .encode() versus .decode() that well, but running it again converts the entire object to binary, so we don't want that
        if sys.version_info >= (3, 0):
            pass
        else:
            data = convertToUTF8(data)

        # If we ask for more multiple components, we can extract this list using the 'pageItemList' key
        # This key is not present for return values with only one component or test, hence the exception
        try:
            return data['pageItemList']
        except KeyError:
            try:
                return data['itemList']
            except KeyError:
                return data

# Define a bunch of useful StandardCommands
SC = StandardCommand
commands =  {   
                'getComponent':                 SC('getComponent', 'GET', [], ['component']), # component := serial number or component code
                'listComponents':               SC('listComponents', 'GET', ['subproject', 'componentType', 'type', 'currentStage', 'pageInfo__pageIndex',
                                                    'pageInfo__pageSize'], ['project']),
                'listComponentsByProperty':     SC('listComponentsByProperty', 'POST', ['subproject', 'componentType', 'type', 'propertyFilter', 'pageInfo__pageIndex',
                                                    'pageInfo__pageSize'], ['project']), # propertyFilter = [{code: <REQUIRED>, operator: <REQUIRED>, value: }] -- hard to check!
                'listMyComponents':             SC('listMyComponents', 'GET', ['project', 'limit', 'pageInfo__pageIndex', 'pageInfo__pageSize'], []),
                'registerComponent':            SC('registerComponent', 'POST', ['type', 'properties', 'comments'], ['project', 'subproject', 'institution', 'componentType']),
                                                    # properties -- hard to check!
                'createDummyChildren':          SC('createDummyChildren', 'POST', [], ['component']),
                'deleteComponent':              SC('deleteComponent', 'POST', [], ['component']),
                'assembleComponent':            SC('assembleComponent', 'POST', ['properties'], ['parent', 'child']),
                'assembleComponentBySlot':      SC('assembleComponentBySlot', 'POST', ['properties'], ['parent', 'slot', 'child']),
                'disassembleComponent':         SC('disassembleComponent', 'POST', [], ['parent', 'child']),
                'setComponentStage':            SC('setComponentStage', 'POST', [], ['component', 'stage']),
                'setComponentGrade':            SC('setComponentGrade', 'POST', ['comment'], ['component', 'grade']),
                'setComponentCompleted':        SC('setComponentCompleted', 'POST', [], ['component', 'completed']),
                'setComponentTrashed':          SC('setComponentTrashed', 'POST', [], ['component', 'trashed']),
                'setComponentProperty':         SC('setComponentProperty', 'POST', ['value'], ['component', 'code']),
                'setParentChildRelationPropertyBySlot': SC('setParentChildRelationPropertyBySlot', 'POST', ['value'], ['component', 'slot', 'property']),
                'createComponentComment':       SC('createComponentComment', 'POST', [], ['component', 'comments']),
                'updateComponentComment':       SC('updateComponentComment', 'POST', [], ['component', 'code', 'comment']),
                'deleteComponentComment':       SC('deleteComponentComment', 'POST', [], ['component', 'code']),
                'createComponentAttachment':    SC('createComponentAttachment', 'POST', ['title', 'description', 'url'], ['component', 'data', 'type']),
                'updateComponentAttachment':    SC('updateComponentAttachment', 'POST', ['title', 'description'], ['component', 'code']),
                'deleteComponentAttachment':    SC('deleteComponentAttachment', 'POST', [], ['component', 'code']),
                'getTestRun':                   SC('getTestRun', 'GET', [], ['testRun']), # testRun := ID of test run
                'listTestRunsByComponent':      SC('listTestRunsByComponent', 'GET', ['stage', 'testType', 'runNumber', 'pageInfo__pageIndex', 'pageInfo__pageSize'],
                                                    ['component']),
                'listTestRunsByParameter':      SC('listTestRunsByParameter', 'POST', ['stage', 'pageInfo__pageIndex', 'pageInfo__pageSize'],
                                                    ['project', 'componentType', 'testType', 'parameterFilter']), # parameterFilter = [{code: <REQUIRED>, parent: , operator: <REQUIRED>, value: }]
                'listTestRunsByTestType':       SC('listTestRunsByTestType', 'GET', ['stage', 'pageInfo__pageIndex', 'pageInfo__pageSize'],
                                                    ['project', 'componentType', 'testType']),
                'listMyTestRuns':               SC('listMyTestRuns', 'GET', ['limit', 'pageInfo__pageIndex', 'pageInfo__pageSize'], []),
                'uploadTestRunResults':         SC('uploadTestRunResults', 'POST', [], []), # Let's not assume anything about the input keys -- disable argument checking
                'getShipment':                  SC('getShipment', 'GET', [], ['shipment']),
                'listShipmentsByInstitution':   SC('listShipmentsByInstitution', 'POST', ['status', 'pageInfo__pageIndex', 'pageInfo__pageSize'], ['code']),
                'listShipmentsByComponent':     SC('listShipmentsByComponent', 'GET', ['status', 'pageInfo__pageIndex', 'pageInfo__pageSize'], ['component']),
                'createShipment':               SC('createShipment', 'POST', ['name', 'trackingNumber', 'shippingService', 'shipmentItems', 'comments'], ['sender', 'recipient', 'type', 'status']),
                'updateShipment':               SC('updateShipment', 'POST', ['name', 'trackingNumber', 'shippingService', 'shipmentItems'], ['shipment', 'sender', 'recipient', 'type', 'status']),
                'deleteShipment':               SC('deleteShipment', 'POST', [], ['shipment']),
                'createShipmentComment':        SC('createShipmentComment', 'POST', [], ['shipment', 'comments']),
                'updateShipmentComment':        SC('updateShipmentComment', 'POST', [], ['shipment', 'code', 'comment']),
                'deleteShipmentComment':        SC('deleteShipmentComment', 'POST', [], ['shipment', 'code']),
                'createShipmentAttachment':     SC('createShipmentAttachment', 'POST', ['title', 'description'], ['shipment', 'data']),
                'updateShipmentAttachment':     SC('updateShipmentAttachment', 'POST', ['title', 'description'], ['shipment', 'code']),
                'deleteShipmentAttachment':     SC('deleteShipmentAttachment', 'POST', [], ['shipment', 'code']),
                'getComponentType':             SC('getComponentType', 'GET', ['fullTree'], ['id']),
                'getComponentTypeByCode':       SC('getComponentTypeByCode', 'GET', [], ['project', 'code']),
                'listComponentTypes':           SC('listComponentTypes', 'GET', ['pageInfo__pageIndex', 'pageInfo__pageSize'], ['project']),
                'listTestTypes':                SC('listTestTypes', 'GET', ['pageInfo__pageIndex', 'pageInfo__pageSize'], ['project', 'componentType']),
                'listInstitutions':             SC('listInstitutions', 'GET', ['pageInfo__pageIndex', 'pageInfo__pageSize'], []),
                'listProjects':                 SC('listProjects', 'GET', ['pageInfo__pageIndex', 'pageInfo__pageSize'], [])
            }
