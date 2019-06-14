#!/usr/bin/env python
# -*- coding: utf-8

'''
Component.py: contains a class for representing components in the ITkPD.
Created: 2018/10/15
Updated: 2019/01/28
'''

__author__  = 'Matthew Basso'
__email__   = 'matthew.joseph.basso@cern.ch'

from itk_pdb.databaseUtilities import commands as dbCommands, Colours, INFO, WARNING, ERROR
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

class Component(object):

    def __init__(self, get_immediately = False, expert = False, **kwargs):

        '''
        A class for representing components in the ITkPD.
            
        Args:
            kwargs (dict): the code for the component (kwargs: 'component') OR the code for the project, the code for the component type, and the code for the type (kwargs: 'project', 'componentType', 'type').
            get_immediately (bool): immediately fetch the json for the test type (default: False).
            expert (bool): disable self.get() inside member functions, arg checking, and printing INFO/WARNING functions (default: False).
        '''

        # Read in our args
        self.expert = expert

        # Get our keys
        keys = kwargs.keys()

        # If we only have the 'component' key, then we are dealing with a single component
        if keys == ['component']:

            # Read in our component code and initialize our component type information
            self.component = kwargs['component'].lower()
            self.project = None
            self.componentType = None
            self.type = None

            # Do arg checking on self.component to see if it looks like a component code
            if len(self.component) != 32 and self.component.isalnum():
                if not self.expert:
                    ERROR('Invalid component code: {0}'.format(self.component))
                    ERROR('Keyword arg \'component\' must be 32 alphanumeric digits -- exitting.')
                raise Error()

        # Else if kwargs contains 'project', 'componentType', and 'type', we are dealing with a non-existent (?) component to be registered
        elif set(kwargs) == set(['project', 'componentType', 'type']):

            # Initialize self.component and fill in our component type info
            self.component = None
            self.project = kwargs['project'].upper()
            self.componentType = kwargs['componentType'].upper()
            self.type = kwargs['type'].upper()

            # Do arg checking on self.project to see if matches the allowed types
            if self.project not in ['S', 'P', 'CE', 'CM']:
                if not self.expert:
                    ERROR('Invalid project code: {0}'.format(self.project))
                    ERROR('Keyword arg \'project\' must be one of \'S\', \'P\', \'CE\', or \'CM\' -- exitting.')
                raise Error()

        # Else we don't have any of the required args to construct a Component object -- exit the code
        else:
            if not self.expert:
                ERROR('Unknown keyword args (excluding \'get_immediately\' and \'expert\'): {0}'.format(kwargs))
                ERROR('Component class constructor must only include kwargs \'component\' OR (\'project\' AND \'componentType\' AND \'type\') -- exitting.')
            raise Error()

        # Get the component's json immediately (as well as its type dictionary), assuming component != None
        if get_immediately and self.component != None:
            self.get()
            self.project = self.json['project']['code']
            self.componentType = self.json['componentType']['code']
            self.type = self.json['type']['code']

        # Else, initialize json to None
        else:
            self.json = None

    def setExpert(self, expert):

        '''
        Set the member function expert to True or False.

        Args:
            expert (bool): sets self.expert to expert.
        '''

        # Check if the arg is True or False
        if expert == True:
            self.expert = True
            return True

        # If False, update the json right away so we don't get undefined behaviour
        elif expert == False:
            self.expert = False
            self.get()
            return True

        # Else, do nothing
        else:
            return False

    def reset(self, get_immediately = False, expert = False, **kwargs):

        '''
        Reset member variables self.shipment to 'shipment' and self.json to None.

        Args:
            shipment (str): the shipment id to update the class with.
            get_immediately (bool): immediately fetch the json for the shipment (default: False).
            expert (bool): disable self.get() inside member functions, arg checking, and printing INFO/WARNING functions (default: False).
        '''

        # Reset self.shipment and self.json
        self.shipment = shipment
        self.json = None

        # Set expert mode
        if expert == True:
            self.expert = True
        elif expert == False:
            self.expert = False
        else:
            pass

        # Fetch our json immediately if get_immediately
        if get_immediately:
            self.get()
        return True

    def __getComponentType(self):

        '''
        Fetch the json for the component type specified in the kwargs of the constructor of the object or specified by the loaded component
        '''

        if self.project == None:
            self.project = self.json['project']['code']
        if self.componentType == None:
            self.componentType = self.json['componentType']['code']
        if self.type == None:
            self.type = self.json['type']['code']
        self.componentType_json = dbCommands['getComponentTypeByCode'].run(project = self.project, code = self.componentType)
        return True

    def __isType(self, value, type):

        '''
        Determine if value is of type 'type'.

        Args:
            value (int|float|str|bool): the value whose type is to be determined.
            type (str): the name of the type to test value against. Choose from ['integer'|'float'|'string'|'boolean'].

        Returns:
            bool: True if value is of type 'type', False otherwise.
        '''

        if type == 'integer':
            if isinstance(value, int):
                return True
            else:
                return False
        elif type == 'float':
            if isinstance(value, float):
                return True
            else:
                return False
        elif type == 'string':
            if isinstance(value, str):
                return True
            else:
                return False
        elif type == 'boolean':
            if isinstance(value, bool):
                return True
            else:
                return False
        else:
            return False

    def get(self):

        '''
        Fetch the json for the component from the ITkPD.
        '''

        self.json = dbCommands['getComponent'].run(component = self.component)
        return True

    """
    ### BEGIN -- DISABLE

    def register(self, institution, type, properties, comments = None):

        '''
        Register a component in the ITkPD.

        Args:
            institution (str): the institution code for the location of component.
            type (str): the type code for the component type to be registered.
            properties (dict): a dictionary of the properties for the component.
            comments (list[str]): (default: None).
        '''

        if not self.expert;

            # If we already have json loaded for the class, prevent a component from being registered and loaded into the class
            if self.json != None:
                WARNING('Class\'s json has already been populated - re-registering component is disallowed.')
                INFO('No component registered.')
                return

            # Check to see that comments is a list of strings
            if not isinstance(comments, list) and [comment for comment in comments if not isinstance(comment, str)] != []:
                WARNING('Comment(s) must be given as a list of strings.')
                INFO('No comment(s) created.')
                return

            # If we haven't retrieved the json for the component type, do so now
            if self.componentType_json == None
                self.__getComponentType()

            for property in pro

            # Check if the properties are set properly
            properties = [property['code'] for property in self.componentType_json['properties']]
            if code not in properties:
                WARNING('Property \'{0}\' is not associated with component type \'{1}\'.'.format(property, self.type['code']))
                INFO('Property not set.')
                return

            i = properties.index(code)

            # Check if the value is set to None and if the property is required (i.e., cannot be set to None)
            if value == None and properties[i]['required']:
                WARNING('Property \'{0}\' is required and cannot be set to None.'.format(property))
                INFO('Property not set.')
                return

            # Check that the value of the property has the right type (if not None)
            elif not self.__isType(value, properties[i]['dataType']):
                WARNING('Property \'{0}\' is not associated with component type \'{1}\'.'.format(property, self.type['code']))
                INFO('Property not set.')
                return












        # Register the component, update self.component, and fetch the updated json
        # We assume the component type is associated with a single subproject - this may need to be fixed
        dtoOut = dbCommands['registerComponent'].run(project = self.json['project']['code'], subproject = self.json['subprojects'][0]['code'],
                                                        institution = institution, componentType = self.type, type = type, properties = properties,
                                                        comments = comments)
        self.component = dtoOut['component']['code']
        if not self.expert:
            self.get()
            INFO('Component type \'{0}\' registered with component code {1}'.format(self.type, self.component))

    ### END -- DISABLE
    """

    def createDummyChildren(self):

        '''
        Create dummy children for the component.
        '''

        # Create the dummy children and fetch the updated json
        dtoOut = dbCommands['createDummyChildren'].run(component = self.component)

        if not self.expert:
            self.get()

            # If the component does not accomodate children (i.e., we should have added none), say so
            if dtoOut['dummyChildren'] == []:
                INFO('Component code {0} does not accommodate child components and so none were created.'.format(self.component))

            # Else report that they were added properly
            else:
                INFO('Dummy children created for component code {0}.'.format(self.component))
        return True

    def delete(self):

        '''
        Delete the component from the ITkPD.
        '''

        # Delete the component and fetch the updated json
        dbCommands['deleteComponent'].run(component = self.component)
        if self.expert:
            self.get()
            INFO('Component code {0} deleted.'.format(self.component))
        return True


    """
    ### BEGIN -- DISABLE
    ### The following functions are disabled until the details of assembly are ironed out -- maybe it makes sense to have an 'Assembly' object?

    def assemble(self, parent_or_child, code, properties):

        '''
        Assemble a parent-child component pair.

        Args:
            parent_or_child (str): choose 'parent' if you're adding a parent to the component, 'child' if you're adding a child to the component
            code (str): the component code for the parent or child component to be added
            properties (dict): 
        '''

        # Make sure that parent_or_child is either 'parent' or 'child'
        if not self.expert and (parent_or_child == 'parent' or parent_or_child == 'child'):
            WARNING('Please select \'parent\' or \'child\' for argument, \'parent_or_child\', \'{0}\' is unrecognized.'.format(parent_or_child))
            INFO('No components assembled')
            return

        # If 'parent', add the code as a parent to the class's component
        if parent_or_child == 'parent':
            dbCommands['assembleComponent'].run(parent = code, child = self.component, properties = None)

        # Else if 'child', add the code as a child to the class's component
        else:
            dbCommands['assembleComponent'].run(parent = self.component, child = code, properties = None)
        if not self.expert:
            INFO('Component code {0} added as a {1} for component code {2}'.format(code, parent_or_child, self.component))

    def assembleBySlot(self, parent_or_child, slot, child, properties):

        '''

        '''

        dbCommands['assembleComponentBySlot'].run(parent = parent, slot = slot, child = child, properties = None):

    def disassemble(self, parent_or_child, code):

        '''
        Disassemble a parent-child component pair.

        Args:
            parent_or_child (str): choose 'parent' if you're removing a parent from the component, 'child' if you're removing a child from the component
            code (str): the component code for the parent or child component to be removed
            properties (dict): 
        '''

        # Make sure that parent_or_child is either 'parent' or 'child'
        if not self.expert and (parent_or_child == 'parent' or parent_or_child == 'child'):
            WARNING('Please select \'parent\' or \'child\' for argument, \'parent_or_child\', \'{0}\' is unrecognized.'.format(parent_or_child))
            INFO('No components disassembled')
            return

        # If 'parent', remove the code as a parent of the class's component
        if parent_or_child == 'parent':
            dbCommands['disassembleComponent'].run(parent = code, child = self.component)

        # Else if 'child', remove the code as a child of the class's component
        else:
            dbCommands['disassembleComponent'].run(parent = self.component, child = code)
        if not self.expert:
            INFO('Component code {0} removed as a {1} from component code {2}'.format(code, parent_or_child, self.component))

    def setParentChildRelationPropertyBySlot(self):

        '''

        '''

        dbCommands['setParentChildRelationPropertyBySlot'].run(component = self.component, slot = slot, property = property, value = value)

    ### END -- DISABLE
    """

    def setStage(self, stage):

        '''
        Set the stage for the component.

        Args:
            stage (str): the code for the stage of the component.
        '''

        if not self.expert:

            # If we haven't retrieved the json for the component type, do so now
            if self.componentType_json == None:
                self.__getComponentType()

            # Check if stage is in the component type's associated stages
            if stage not in [stage['code'] for stage in self.componentType_json['stages']]:
                WARNING('Stage \'{0}\' is not associated with component type \'{1}\'.'.format(stage, self.type['code']))
                INFO('Stage not set.')
                return False

        # Update the stage and fetch the updated json
        dbCommands['setComponentStage'].run(component = self.component, stage = self.stage)
        if not self.expert:
            self.get()
            INFO('Component code {0} updated to stage \'{1}\'.'.format(self.component, stage))
        return True

    def setGrade(self, grade, comment = None):

        '''
        Set the grade for the component.

        Args:
            grade (int): the grade for the component.
            comment (str): a comment to be included alongside the grade (default: None).
        '''

        # Check that grade is an integer and comment is a string
        if not self.expert:
            if not isinstance(grade, int):
                WARNING('Grade must be an integer.')
                INFO('Grade not set.')
                return False
            elif comment != None and not isinstance(comment, str):
                WARNING('Comment must be a string.')
                INFO('Grade not set.')
                return False

        # If no comment is provided, don't include it in the uuCMD call
        if comment == None:
            dbCommands['setComponentGrade'].run(component = self.component, grade = grade)
            
        # If a comment is provided, include it in the uuCMD call
        else:
            dbCommands['setComponentGrade'].run(component = self.component, grade = grade, comment = comment)
            
        # Fetch the updated json
        if not self.expert:
            self.get()
            INFO('Grade set to {0} for component code {1}.'.format(str(grade), self.component))
        return True

    def setCompleted(self, completed):

        '''
        Set the Completed status for the component.

        Args:
            completed (bool): set the component as Completed if True.
        '''

        # Check that completed is a boolean
        if not self.expert and not isinstance(completed, bool):
            WARNING('Completed must be a boolean.')
            INFO('Completed not set.')
            return

        # Set completed and fetch the updated json
        dbCommands['setComponentCompleted'].run(component = self.component, completed = completed)
        if not self.expert:
            self.get()
            INFO('Completed set to {0} for component code {1}.'.format(completed, self.component))

    def setTrashed(self, trashed):

        '''
        Set the Trashed status for the component.

        Args:
            trashed (bool): set the component as Trashed if True.
        '''

        # Check that trashed is a boolean
        if not self.expert and not isinstance(trashed, bool):
            WARNING('Trashed must be a boolean.')
            INFO('Trashed not set.')
            return False

        # Set trashed and fetch the updated json
        dbCommands['setComponentTrashed'].run(component = self.component, trashed = trashed)
        if not self.expert:
            self.get()
            INFO('Trashed set to {0} for component code {1}.'.format(trashed, self.component))
        return True

    def setProperty(self, code, value):

        '''
        Set a property for the component.

        Args:
            code (str): the code for the property to be set.
            value (int|float|str|bool): the value for the property.
        '''

        if not self.expert:

            # If we haven't retrieved the json for the component type, do so now
            if self.componentType_json == None:
                self.__getComponentType()

            # Check if the property code is in the component type's associated properties
            properties = [property['code'] for property in self.componentType_json['properties']]
            if code not in properties:
                WARNING('Property \'{0}\' is not associated with component type \'{1}\'.'.format(property, self.type['code']))
                INFO('Property not set.')
                return False

            i = properties.index(code)

            # Check if the value is set to None and if the property is required (i.e., cannot be set to None)
            if value == None and properties[i]['required']:
                WARNING('Property \'{0}\' is required and cannot be set to None.'.format(property))
                INFO('Property not set.')
                return False

            # Check that the value of the property has the right type (if not None)
            elif not self.__isType(value, properties[i]['dataType']):
                WARNING('Property \'{0}\' is not associated with component type \'{1}\'.'.format(property, self.type['code']))
                INFO('Property not set.')
                return False

        # Update the stage and fetch the updated json
        dbCommands['setComponentProperty'].run(component = self.component, code = code, value = value)
        if not self.expert:
            self.get()
            INFO('Component code {0} updated to stage \'{1}\'.'.format(self.component, stage))
        return True

    def createComment(self, comments):

        '''
        Create a list of comments associated with the component.

        Args:
            comments (list[str]): a list of comments to be created.
        '''

        if not self.expert:

            if not isinstance(comments, list) and [comment for comment in comments if not isinstance(comment, str)] != []:
                WARNING('Comment(s) must be given as a list of strings.')
                INFO('No comment(s) created.')
                return False

        # Add the comments and fetch the updated json
        dbCommands['createComponentComment'].run(component = self.component, comments = comments)
        if not self.expert:
            self.get()

            # Report the codes for the new comments (at the end of the comments list from the json)
            comments_new = self.json['comments'][(len(self.json['comments']) - len(comments)):]
            INFO('Comment code(s) {0} created for component code {1}.'.format(', '.join([comment['code'] for comment in comments_new]), self.component))
        return True

    def updateComment(self, code, comment):

        '''
        Update a comment associated with the component.

        Args:
            code (str): the code for the comment to be updated.
            comment (str): the content the comment will be updated with.
        '''

        # Check that the comment code is associated with a comment for the component
        if not self.expert and code not in [comment['code'] for comment in self.json['comments']]:
            WARNING('Code {0} is not associated with any comments of component code {1}.'.format(code, self.component))
            INFO('No comments deleted.')
            return False

        # Update the comment and fetch the updated json
        dbCommands['updateComponentComment'].run(component = self.component, code = code, comment = comment)
        if not self.expert:
            self.get()
            INFO('Comment code {0} updated for component code {1}.'.format(code, self.component))
        return True

    def deleteComment(self, code):

        '''
        Delete a comment associated with the component.

        Args:
            code (str): the code for the comment to be deleted.
        '''

        # Check that the comment code is associated with a comment for the component
        if not self.expert and code not in [comment['code'] for comment in self.json['comments']]:
            WARNING('Code {0} is not associated with any comments of component code {1}.'.format(code, self.component))
            INFO('No comments deleted.')
            return False

        # Delete the comment and fetch the updated json
        dbCommands['deleteComponentComment'].run(component = self.component, code = code)
        if not self.expert:
            self.get()
            INFO('Comment code {0} deleted from component code {1}.'.format(code, self.component))
        return True

    def createAttachment(self, data, title = None, description = None):

        '''
        Create an attachment with binary data and add it to the component.

        Args:
            data (bin str): binary data to be uploaded.
            title (str): the title for the attachment (default: None).
            description (str): the description for the attachment (default: None)
        '''

        # Get our function call kwargs
        kwargs = {'component': self.component, 'title': title, 'description': description, 'data': data}
        
        # Generate our dtoIn by removing the items in kwargs which are None
        dtoIn = {k:v for k,v in kwargs.items() if v is not None}

        # Create our attachment and fetch the updated json
        dbCommands['createComponentAttachment'].run(**dtoIn)
        if not self.expert:
            self.get()
            INFO('Attachment code {0} created for component code {1}.'.format(self.json['attachments'][-1]['code'], self.component))
        return True

    def updateAttachment(self, code, title = None, description = None):

        '''
        Update an attachment associated with the component.

        Args:
            title (str): the updated title for the attachment (default: None).
            description (str): the updated description for the attachment (default: None).
        '''

        # Check that the attachment code is associated with a attachment for the component
        if not self.expert and code not in [attachment['code'] for attachment in self.json['attachments']]:
            WARNING('Code {0} is not associated with any attachments of component code {1}.'.format(code, self.component))
            INFO('No attachments updated.')
            return False

        # Get our function call kwargs
        kwargs = {'component': self.component, 'code': code, 'title': title, 'description': description}

        # Generate our dtoIn by removing the items in kwargs which are None
        dtoIn = {k:v for k,v in kwargs.items() if v is not None}

        # Update our attachment and fetch the updated json
        dbCommands['updateComponentAttachment'].run(**dtoIn)
        if not self.expert:
            self.get()
            INFO('Attachment code {0} updated for component code {1}.'.format(code, self.component))
        return True

    def deleteAttachment(self, code):

        '''
        Delete an attachment associated with the component.

        Args:
            code (str): the code for attachment to be deleted.
        '''

        # Check that the attachment code is associated with a attachment for the component
        if not self.expert and code not in [attachment['code'] for attachment in self.json['attachments']]:
            WARNING('Code {0} is not associated with any attachments of component code {1}.'.format(code, self.component))
            INFO('No attachments deleted.')
            return False

        # Delete the attachment and fetch the updated json
        dbCommands['deleteComponentAttachment'].run(component = self.component, code = code)
        if not self.expert:
            self.get()
            INFO('Attachment code {0} deleted from component code {1}.'.format(code, self.component))
        return True

    def printJSON(self):

        '''
        Pretty print the json for the component type.
        '''

        # Pretty print the json
        if not self.expert:
            INFO('Printing JSON for component code {0}:\n'.format(self.component))
            pp.pprint(self.json)
            print('')
        else:
            pp.pprint(self.json)
        return True

# class ComponentList(object):

#     def __init__(self, verbose = True):
#         self.verbose = verbose
#         self.json = None
#         self.components = []

#     def __getitem__(self, i):
#         try:
#             return self.components[i]
#         except (IndexError, TypeError):
#             return None
