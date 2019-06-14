#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
ShipmentClasses.py: classes for representing shipments in the ITkPD.
Created: 2018/10/01
Updated: 2019/01/28
'''

__author__  = 'Matthew Basso'
__email__   = 'matthew.joseph.basso@cern.ch'

from itk_pdb.databaseUtilities import commands as dbCommands, Colours, INFO, WARNING
from itk_pdb.ComponentClasses import Component
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

class Shipment(object):

    def __init__(self, shipment, get_immediately = False, expert = False):

        '''
        A class for representing shipments in the ITkPD.
            
        Args:
            shipment (str): the id for the shipment.
            get_immediately (bool): immediately fetch the json for the shipment (default: False).
            expert (bool): disable self.get() inside member functions, arg checking, and printing INFO/WARNING functions (default: False).

        Notes:
            Setting expert to True may result in exceptions or undefined behaviour.
            --> It is up to the user to perform arg checking and update the json explicitly using self.get().
        '''

        # Read in our args
        self.shipment = shipment
        self.expert = expert

        # Initialize json to None
        self.json = None

        # Fetch our json immediately if get_immediately
        if get_immediately:
            self.get()

    def __getitem__(self, i):

        '''
        Return a Component object for a component included in the shipmentItems list.

        Args:
            i (int): the index of the component in shipmentItems (in the order the components are presented)

        Returns:
            :obj:`Component`: the Component object for the selected index.

        Notes:
            The argument expert is set to True for the returned Component object
            --> This disables self.get() in other function calls, arg checking, and print statements.
        '''

        try:
            return Component(self.json['shipmentItems'][i]['code'], expert = True)
        except (IndexError, TypeError):
            return None

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

    def reset(self, shipment, get_immediately = False, expert = False):

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

    def get(self):

        '''
        Fetch the json for the component type from the ITkPD.
        '''

        self.json = dbCommands['getShipment'].run(shipment = self.shipment)
        return True

    def create(self, sender, recipient, type, status, name = None, trackingNumber = None, shippingService = None, shipmentItems = None, comments = None):

        '''
        Create a shipment in the ITkPD.

        Args:
            sender (str): the code for the institution sending the shipment.
            recipient (str): the code for the institution receiving the shipment.
            type (str): the code for the type of shipment. Choose from ['domestic'|'intraContinental'|'continental'].
            status (str): the code for the status of the shipment. Choose from ['prepared'|'inTransit'|'delivered'|'deliveredWithDamage'|'undelivered'].
            name (str): the name of the shipment (default: None).
            trackingNumber (str): the tracking number associated with the shipment (default: None).
            shippingService (str): the shipping service delivering the shipment (default: None).
            shipmentItems (list[str]): a list of component codes for the components contained in the shipment (default: None).
            comments (list[str]): a list of comments associated with the shipment (default: None).
        '''

        # Perform checking on the provided args
        if not self.expert:
            if self.json != None:
                WARNING('Class\'s json has already been populated - creating a shipment is disallowed')
                INFO('No shipment created.')
                return False
            if type not in ['domestic', 'intraContinental', 'continental']:
                WARNING('Shipping type \'{0}\' is not recognized.'.format(status))
                INFO('No shipment created.')
                return False
            elif status not in ['prepared', 'inTransit', 'delivered', 'deliveredWithDamage', 'undelivered']:
                WARNING('Shipping status \'{0}\' is not recognized.'.format(status))
                INFO('No shipment created.')
                return False
            elif not isinstance(comments, list) and [comment for comment in comments if not isinstance(comment, str)] != []:
                WARNING('Comment(s) must be given as a list of strings.')
                INFO('No shipment created.')
                return False
            elif not isinstance(shipmentItems, list) and [item for item in shipmentItems if not isinstance(item, str)] != []:
                WARNING('Shipment item(s) must be given as a list of component codes (strings).')
                INFO('No shipment created.')
                return False

        # Fetch our args and remove any keys with values set to None
        kwargs = {'name': name, 'sender': sender, 'recipient': recipient, 'trackingNumber': trackingNumber, 'shippingService': shippingService,
                    'type': type, 'status': status, 'shipmentItems': shipmentItems, 'comments': comments}
        dtoIn = {k:v for k,v in kwargs.items() if v is not None}

        # Create the shipment, update self.shipment, and fetch the updated json
        dtoOut = dbCommands['createShipment'].run(**dtoIn)
        self.shipment = dtoOut['shipment']['id']
        if not self.expert:
            self.get()
            INFO('Shipment id {0} created.'.format(self.shipment))
        return True

    def update(self, sender = None, recipient = None, type = None, status = None, name = None, trackingNumber = None, shippingService = None, shipmentItems = None):
        
        '''
        Update the shipment in the ITkPD.

        Args:
            sender (str): the (updated) code for the institution sending the shipment (default: None).
            recipient (str): the (updated) code for the institution receiving the shipment (default: None).
            type (str): the (updated) code for the type of shipment. Choose from ['domestic'|'intraContinental'|'continental'].(default: None).
            status (str): the (updated) code for the status of the shipment. Choose from ['prepared'|'inTransit'|'delivered'|'deliveredWithDamage'|'undelivered'] (default: None).
            name (str): the (updated) name of the shipment (default: None).
            trackingNumber (str): the (updated) tracking number associated with the shipment (default: None).
            shippingService (str): the (updated) shipping service delivering the shipment (default: None).
            shipmentItems (list[str]): the (updated) list of component codes for the components contained in the shipment (default: None).

        Notes:
            The args sender, recipient, type, and status are required, but if they are not changed from their default values (None), they will assume
            the values currently stored in self.json (all of the other args, if not specified, will not not affect the shipment).
        '''

        # If self.json is not None, set a required arg for the uuCMD equal to its present value in self.json if it's equal to None in the function call
        if self.json != None:
            if sender == None:
                sender = self.json['sender']['code']
            if recipient == None:
                recipient = self.json['recipient']['code']
            if type == None:
                type = self.json['type']
            if status == None:
                status = self.json['status']

        # Perform checking on the provided args
        if not self.expert:
            if self.json == None:
                WARNING('Class\'s json is not populated - updating a shipment is disallowed.')
                INFO('No shipment updated.')
                return False
            if type not in ['domestic', 'intraContinental', 'continental']:
                WARNING('Shipping type \'{0}\' is not recognized.'.format(status))
                INFO('Shipment id {0} not updated.'.format(self.shipment))
                return False
            elif status not in ['prepared', 'inTransit', 'delivered', 'deliveredWithDamage', 'undelivered']:
                WARNING('Shipping status \'{0}\' is not recognized.'.format(status))
                INFO('Shipment id {0} not updated.'.format(self.shipment))
                return False
            elif shipmentItems != None and not isinstance(shipmentItems, list) and [item for item in shipmentItems if not isinstance(item, str)] != []:
                WARNING('Shipment item(s) must be given as a list of component codes (strings).')
                INFO('Shipment id {0} not updated.'.format(self.shipment))
                return False

        # Fetch our args and remove any keys with values set to None
        kwargs = {'name': name, 'shipment': self.shipment, 'sender': sender, 'recipient': recipient, 'trackingNumber': trackingNumber,
                    'shippingService': shippingService, 'type': type, 'status': status, 'shipmentItems': shipmentItems}
        dtoIn = {k:v for k,v in kwargs.items() if v is not None}
        
        # Update the shipment and fetch the updated json
        dbCommands['updateShipment'].run(**dtoIn)
        if not self.expert:
            self.get()
            INFO('Shipment id {0} updated.'.format(self.shipment))
        return True

    def delete(self):

        '''
        Delete the shipment from the ITkPD.
        '''

        # Delete the shipment
        dbCommands['deleteShipment'].run(shipment = self.shipment)
        if not self.expert:
            INFO('Shipment id {0} deleted.'.format(self.shipment))
        return True

    def createComment(self, comments):

        '''
        Create a list of comments associated with the shipment.

        Args:
            comments (list[str]): a list of comments to be created.
        '''

        # Perform type checking on the provided args
        if not self.expert and not isinstance(comments, list) and [comment for comment in comments if not isinstance(comment, str)] != []:
            WARNING('Comment(s) must be given as a list of strings.')
            INFO('No comment(s) created.')
            return False

        # Create the comments and fetch the updated json
        dbCommands['createShipmentComment'].run(shipment = self.shipment, comments = comments)
        if not self.expert:
            self.get()
            comments_new = self.json['comments'][(len(self.json['comments']) - len(comments)):]
            INFO('Comment code(s) {0} created for shipment id {1}.'.format(', '.join([comment['code'] for comment in comments_new]), self.shipment))
        return True

    def updateComment(self, code, comment):

        '''
        Update a comment associated with the shipment.

        Args:
            code (str): the code for the comment to be updated.
            comment (str): the content the comment will be updated with.
        '''

        # Check the provided code to see if it's associated with a comment of the shipment
        if not self.expert and code not in [comment['code'] for comment in self.json['comments']]:
            WARNING('Code {0} is not associated with any comments of shipment id {1}.'.format(code, self.shipment))
            INFO('No comments deleted.')
            return False

        # Update the comment and fetch the updated json
        dbCommands['updateShipmentComment'].run(shipment = self.shipment, code = code, comment = comment)
        if not self.expert:
            self.get()
            INFO('Comment code {0} updated for shipment id {1}.'.format(code, self.shipment))
        return True

    def deleteComment(self, code):

        '''
        Delete a comment associated with the shipment.

        Args:
            code (str): the code for the comment to be deleted.
        '''

        # Check the provided code to see if it's associated with a comment of the shipment 
        if not self.expert and code not in [comment['code'] for comment in self.json['comments']]:
            WARNING('Code {0} is not associated with any comments of shipment id {1}.'.format(code, self.shipment))
            INFO('No comments deleted.')
            return False

        # Delete the comment and fetch the updated json
        dbCommands['deleteShipmentComment'].run(shipment = self.shipment, code = code)
        if not self.expert:
            self.get()
            INFO('Comment code {0} deleted from shipment id {1}.'.format(code, self.shipment))
        return True

    def createAttachment(self, data, title = None, description = None):

        '''
        Create an attachment with binary data and add it to the shipment.

        Args:
            data (bin str): binary data to be uploaded.
            title (str): the title for the attachment (default: None).
            description (str): the description for the attachment (default: None)
        '''

        # Fetch our args and remove any keys with values set to None
        kwargs = {'shipment': self.shipment, 'title': title, 'description': description, 'data': data}
        dtoIn = {k:v for k,v in kwargs.items() if v is not None}

        # Create the attachment and fetch the updated json
        dbCommands['createShipmentAttachment'].run(**dtoIn)
        if not self.expert:
            self.get()
            INFO('Attachment code {0} created for shipment id {1}.'.format(self.json['attachments'][-1]['code'], self.shipment))
        return True

    def updateAttachment(self, code, title = None, description = None):

        '''
        Update an attachment associated with the shipment.

        Args:
            title (str): the updated title for the attachment (default: None).
            description (str): the updated description for the attachment (default: None).
        '''

        # Check the provided code to see if it's associated with an attachment of the shipment
        if not self.expert and code not in [attachment['code'] for attachment in self.json['attachments']]:
            WARNING('Code {0} is not associated with any attachments of shipment id {1}.'.format(code, self.shipment))
            INFO('No attachments updated.')
            return False

        # Fetch our args and remove any keys with values set to None
        kwargs = {'shipment': self.shipment, 'code': code, 'title': title, 'description': description}
        dtoIn = {k:v for k,v in kwargs.items() if v is not None}

        # Update the attachment and fetch the updated json
        dbCommands['updateShipmentAttachment'].run(**dtoIn)
        if not self.expert:
            self.get()
            INFO('Attachment code {0} updated for shipment id {1}.'.format(code, self.shipment))
        return True

    def deleteAttachment(self, code):

        '''
        Delete an attachment associated with the shipment.

        Args:
            code (str): the code for attachment to be deleted.
        '''

        # Check the provided code to see if it's associated with an attachment of the shipment
        if not self.expert and code not in [attachment['code'] for attachment in self.json['attachments']]:
            WARNING('Code {0} is not associated with any attachments of shipment id {1}.'.format(code, self.shipment))
            INFO('No attachments deleted.')
            return False

        # Delete the attachment and fetch the updated json
        dbCommands['deleteShipmentAttachment'].run(shipment = self.shipment, code = code)
        if not self.expert:
            self.get()
            INFO('Attachment code {0} deleted from shipment id {1}.'.format(code, self.shipment))
        return True

    def printJSON(self):

        '''
        Pretty print the json for the component type.
        '''

        # Pretty print the json
        if not self.expert:
            INFO('Printing JSON for shipment id {0}:\n'.format(self.shipment))
            pp.pprint(self.json)
            print('')
        else:
            pp.pprint(self.json)
        return True

    def printSummary(self):

        '''
        Print a (very) pretty summary of the info associated with the shipment.
        '''

        if not self.expert:
            INFO('Printing summary for shipment id {0}:\n'.format(self.shipment))

        # Print general details associated with the shipment
        print('    {0}{1}Shipment ID{2}      : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['id']))
        print('    {0}{1}Shipment Name{2}    : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['name']))
        print('    {0}{1}Shipment Number{2}  : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['shipmentNumber']))
        print('    {0}{1}Shipping Service{2} : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['shippingService']))
        print('    {0}{1}Tracking Number{2}  : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['trackingNumber']))
        print('    {0}{1}Type{2}             : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['type']))
        print('    {0}{1}Status{2}           : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, self.json['status']))
        print('    {0}{1}Managing User{2}    : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, '{0} {1} ({2})'.format(self.json['user']['firstName'], self.json['user']['lastName'], self.json['user']['userIdentity'])))
        print('    {0}{1}Sender{2}           : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, '{0} ({1})'.format(self.json['sender']['name'], self.json['sender']['code'])))
        print('    {0}{1}Recipient{2}        : {3}'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC, '{0} ({1})'.format(self.json['recipient']['name'], self.json['recipient']['code'])))
        
        # Print a list of the items contained in the shipment
        print('    {0}{1}Shipment Items{2}   :'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC))
        header_shipment_items = ['Index', 'Serial Number', 'Code', 'Component Type', 'Type']
        format_shipment_items = '        {:<10}{:<20}{:<35}{:<20}{:<20}'
        print(Colours.BOLD + Colours.WHITE + format_shipment_items.format(*header_shipment_items) + Colours.ENDC)
        for i, item in enumerate(self.json['shipmentItems']):
            try:
                row = [i, item['serialNumber'], item['code'], '{0} ({1})'.format(item['componentType']['name'], item['componentType']['code']), 
                        '{0} ({1})'.format(item['componentType']['type']['name'], item['componentType']['type']['code'])]
            except KeyError:
                row = [item['serialNumber'], '{0} ({1})'.format(item['componentType']['name'], item['componentType']['code']), 'N/A']
            print(format_shipment_items.format(*row))

        # Print a list of the comments associated with the shipment
        print('    {0}{1}Comments{2}         :'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC))
        header_comments = ['Code', 'Date', 'Time', 'User', 'Comment']
        format_comments = '        {:<30}{:<20}{:<20}{:<35}{:}'
        print(Colours.BOLD + Colours.WHITE + format_comments.format(*header_comments) + Colours.ENDC)
        for comment in list(reversed(sorted(self.json['comments'], key = lambda comment: comment['dateTime']))):
            row = [comment['code'], comment['dateTime'].split('T')[0], comment['dateTime'].split('T')[1], '{0} {1} ({2})'.format(comment['user']['firstName'], 
                    comment['user']['lastName'], comment['user']['userIdentity']), comment['comment']]
            print(format_comments.format(*row))

        # Print a list of the attachments associated with the shipment
        print('    {0}{1}Attachments{2}      :'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC))
        header_attachments = ['Date', 'Time', 'User', 'Filename', 'Content Type', 'Title', 'Description']
        format_attachments = '        {:<20}{:<20}{:<35}{:<20}{:<20}{:<20}{:}'
        print(Colours.BOLD + Colours.WHITE + format_attachments.format(*header_attachments) + Colours.ENDC)
        for attachment in list(reversed(sorted(self.json['attachments'], key = lambda attachment: attachment['dateTime']))):
            row = [attachment['dateTime'].split('T')[0], attachment['dateTime'].split('T')[1], '{0} {1} ({2})'.format(attachment['user']['firstName'],
                    attachment['user']['lastName'], attachment['user']['userIdentity']), attachment['filename'], attachment['contentType'],
                    attachment['title'], attachment['description']] 
            print(format_attachments.format(*row))

        # Print the history associated with the shipment
        print('    {0}{1}History{2}          :'.format(Colours.BOLD, Colours.WHITE, Colours.ENDC))
        header_history = ['Date', 'Time', 'User', 'Status']
        format_history = '        {:<20}{:<20}{:<35}{:<20}'
        print(Colours.BOLD + Colours.WHITE + format_history.format(*header_history) + Colours.ENDC)
        for item in list(reversed(sorted(self.json['history'], key = lambda item: item['dateTime']))):
            row = [item['dateTime'].split('T')[0], item['dateTime'].split('T')[1], '{0} {1} ({2})'.format(item['user']['firstName'],
                    item['user']['lastName'], item['user']['userIdentity']), item['code']]
            print(format_history.format(*row))
        
        if not self.expert:
            print('')
        return True

class ShipmentList(object):

    def __init__(self, verbose = True):

        '''
        A class for obtaining lists of shipments in the ITkPD.
            
        Args:
            verbose (bool): enable INFO/WARNING print functions (default: True).

        Notes:
            Arg checking is always enabled since it is easy to do.
            --> Only verbosity may be disabled.
            --> If the args do not make sense, the commands will not do anything.
        '''

        # Read in our args
        self.verbose = verbose

        # Initialize the json read in from the DB and our stored list of Shipment objects
        self.json = None
        self.shipments = []

    def __getitem__(self, i):

        '''
        Return a Shipment object for a shipment included in the self.shipments list.

        Args:
            i (int): the index of the shipment in self.shipments (in the order the shipments are presented).

        Returns:
            :obj:`Shipment`: the Shipment object for the selected index.

        Notes:
        The arguments get_immediately and expert are set to True and False, respectively, for the returned Shipment objects.
        --> This enables self.get() in function calls, arg checking, and print statements.
        '''

        try:
            return self.shipments[i]
        except (IndexError, TypeError):
            return None

    def getListByInstitution(self, code, status = None):

        '''
        Loads a list of shipments associated with an institution into self.json.

        Args:
            code (list[str]): a list of institution codes to filter shipments by.
            status (list[str]): a list of status codes to filter shipments by. Choose status codes from ['prepared'|'inTransit'|'delivered'|'deliveredWithDamage'|'undelivered'] (default None).

        Notes:
            If code and/or status are given as strings instead of list of strings, those strings are implicitly converted to lists of strings.
        '''

        if not isinstance(code, list):
            code = [code]
        dtoIn = {'code': code, 'status': status}
        if status == None:
            del dtoIn['status']
        else:
            if not isinstance(status):
                status = [status]
            allowed_statuses = ['prepared', 'inTransit', 'delivered', 'deliveredWithDamage', 'undelivered']
            unknown_statuses = [status_item for status_item in status if status_item not in allowed_statuses]
            if unknown_statuses != []:
                if self.verbose:
                    WARNING('Shipping status(es) \'{0}\' is(are) not recognized.'.format('\', \''.join(unknown_statuses)))
                    INFO('No list generated.')
                return False
        self.json = dbCommands['listShipmentsByInstitution'].run(**dtoIn)
        if self.verbose:
            if status == None:
                INFO('Retrieved list of shipments by institution using code(s) \'{0}\'.'.format('\', \''.join(code)))
            else:
                INFO('Retrieved list of shipments by component using code(s) \'{0}\' and filtering by status(es) \'{1}\'.'.format('\', \''.join(code), '\', \''.join(status)))
        return True

    def getListByComponent(self, component, status = None):

        '''
        Load a list of shipments associated with a component code into self.json.

        Args:
            code (list[str]): the code for the component to filter shipments by.
            status (list[str]): a status codes to filter shipments by. Choose status codes from ['prepared'|'inTransit'|'delivered'|'deliveredWithDamage'|'undelivered'] (default None).
        '''

        dtoIn = {'component': component, 'status': status}
        if status == None:
            del dtoIn['status']
        else:
            allowed_statuses = ['prepared', 'inTransit', 'delivered', 'deliveredWithDamage', 'undelivered']
            unknown_statuses = [status_item for status_item in status if status_item not in allowed_statuses]
            if unknown_statuses != []:
                if self.verbose:
                    WARNING('Shipping status(es) \'{0}\' not recognized.'.format('\', \''.join(unknown_statuses)))
                    INFO('No list generated.')
                return False
        self.json = dbCommands['listShipmentsByComponent'].run(**dtoIn)
        if self.verbose:
            if status == None:
                INFO('Retrieved list of shipments by component using code \'{0}\'.'.format(code))
            else:
                INFO('Retrieved list of shipments by component using code \'{0}\' and filtering by status(es) \'{1}\'.'.format(code, '\', \''.join(status)))
        return True

    def storeShipments(self, *args):

        '''
        Store shipments in self.shipments.

        Args:
            args (int): the index(indices) of the shipment(s) in self.shipments to be stored.

        Notes:
            If args == (), then all of the shipments in self.json are stored.
            Args that are not integers are ignored
        '''

        if self.shipments == []:
            ids_stored = []
        else:
            ids_stored = [shipment.json['id'] for shipment in self.shipments]
        if args == ():
            args = range(len(self.json))
        for i in args:
            try:
                id_current = self.json[i]['id']
                if id_current in ids_stored:
                    if self.verbose:
                        WARNING('Shipment id {0} ({1} --> {2}) is already in stored list of shipments -- skipping.'.format(id_current, self.json[i]['sender']['code'], self.json[i]['recipient']['code']))
                else:
                    self.shipments.append(Shipment(shipment = id_current, get_immediately = True))
                    if self.verbose:
                        INFO('Added shipment id {0} ({1} --> {2}) to stored list of shipments.'.format(id_current, self.json[i]['sender']['code'], self.json[i]['recipient']['code']))
            except (IndexError, TypeError):
                pass
        self.shipments = list(reversed(sorted(self.shipments, key = lambda shipment: shipment.json['history'][-1]['dateTime'])))
        return True

    def clearShipments(self, *args):

        '''
        Clear stored hipments from self.shipmentss.

        Args:
            args (int): the index(indices) of the shipment(s) in self.shipments to be removed.

        Notes:
            If args == (), then all of the shipments in self.shipments are removed.
            Args that are not integers are ignored
        '''

        if args == ():
            args = range(len(self.shipments))
        else:
            args = [arg for arg in args if isinstance(arg, int)]
        for i in sorted(args, reverse = True):
            try:
                id_current = self.shipments[i].json['id']
                sender_current = self.shipments[i].json['sender']['code']
                recipient_current = self.shipments[i].json['recipient']['code']
                del self.shipments[i]
                if self.verbose:
                    INFO('Deleted shipment id {0} ({1} --> {2}) from stored list of shipments.'.format(id_current, sender_current, recipient_current))
            except IndexError:
                pass
        return True

    def printFetchedList(self):

        '''
        Print a pretty summary of the shipments currently stored in self.json.
        '''

        if self.json == None:
            if self.verbose:
                WARNING('No shipment list currently fetched from the ITkPD -- nothing printed.')
        else:
            if self.verbose:
                INFO('Printing fetched list of shipments:\n')
            header = ['Index', 'ID', 'Shipment Name', 'Sender', 'Recipient', 'Shipping Service', 'Tracking Number', 'Type', 'Status']
            format_new = '    {:<10}{:<30}{:<20}{:<15}{:<15}{:<25}{:<20}{:<20}{:<20}'
            print(Colours.BOLD + Colours.WHITE + format_new.format(*header) + Colours.ENDC)
            for i, shipment in enumerate(self.json):
                row = [str(i), shipment['id'], shipment['name'], shipment['sender']['code'], shipment['recipient']['code'], shipment['shippingService'],
                        shipment['trackingNumber'], shipment['type'], shipment['status']]
                print(format_new.format(*row))
            if self.verbose:
                print('')
        return True

    def printStoredList(self):
        
        '''
        Print a pretty summary of the shipments currently stored in self.shipments.
        '''

        if self.verbose:
            INFO('Printing stored list of shipments:\n')
        header = ['Index', 'ID', 'Shipment Name', 'Sender', 'Recipient', 'Shipping Service', 'Tracking Number', 'Type', 'Status']
        format_new = '    {:<10}{:<30}{:<20}{:<15}{:<15}{:<25}{:<20}{:<20}{:<20}'
        print(Colours.BOLD + Colours.WHITE + format_new.format(*header) + Colours.ENDC)
        for i, shipment in enumerate(self.shipments):
            row = [str(i), shipment.json['id'], shipment.json['name'], shipment.json['sender']['code'], shipment.json['recipient']['code'],
                    shipment.json['shippingService'], shipment.json['trackingNumber'], shipment.json['type'], shipment.json['status']]
            print(format_new.format(*row))
        if self.verbose:
            print('')
        return True
