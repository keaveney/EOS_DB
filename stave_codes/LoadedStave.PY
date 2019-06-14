#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import argparse
import json
import os, sys
import numpy as np
import ReadSurvey as RS
import time
from itk_pdb.databaseUtilities import commands

class STAVE(object):
    def __init__(self, LOCALNAME=None, dir='./', assemblySite='BU', STAGE='reception'):
        self.component='STAVE'
        self.directory=dir
        self.type=None #from addCore
        self.side=None #from addCore
        self.localname=LOCALNAME
        self.site=assemblySite
        self.code=None #get from registerSTAVE
        self.stage=STAGE
        self.modules={}#from addModule
        self.slotIDs=[]
        self.EoS={}
        self.core={}

    def registerSTAVE(self):
        #need to self.addCore first
        JSON={}
        JSON['institution']=self.site
        JSON['componentType']=self.component
        JSON['project']='S'
        JSON['subproject']='SB'
        staveProperties={}
        staveProperties['SIDE']=self.type
        staveProperties['LOCALNAME']=self.localname
        if self.type=='LS' or self.type =='Long': ##uncertain how the type is gonna be called for core yet
            type='LS'
        else:# self.type == 'SS' or self.type='Short':
            type='SS'
        JSON['type']=type
        JSON['properties']=staveProperties
        print JSON
        new_stave=commands['registerComponent'].run(**JSON)['component'] #does not have children info
        #save a local json of
        #with open(self.directory+'STAVEinfo.json','w') as outfile:
        #    json.dump(new_stave,outfile)
        #print 'saved stave information in ', self.directory+'STAVEinfo.json'
        print 'finished registering new STAVE'
        self.code=new_stave['code']
        STAVE=commands['getComponent'].run(component=self.code)
        self.childrenSlots(STAVE)
        return STAVE

    def StaveINFO(self):
        stave=FindComp(LOCALNAME=self.localname,comp_type=self.component)
        stave_id = stave['code']
        self.code=stave_id
        STAVE = commands['getComponent'].run(component=stave_id)
        #print(STAVE)
        self.type=STAVE['type']['name']
        STAVE_properties=STAVE['properties']
        for property in STAVE_properties:
            if property['code']=='SIDE':
                self.side=property['value']
        #also has child information
        self.childrenSlots(STAVE)
        return STAVE

    def childrenSlots(self,STAVE):
        children=STAVE['children']
        slotid=[]
        for component in children:
            id=component['id']
            slotid.append(id)
        #print(slotid)
        #print(len(slotid))
        self.slotIDs=slotid


    def addCore(self, core):
        #in the future, input should be an ID to find core, read type and side from there
        self.type=core.type
        self.side=core.side
        self.core['name']=core.name
        #assemble core and stave

    def addModule(self,module): #add module according to its position on the stave
        dir=self.directory
        position=module.position
        if self.stage=='reception':
            self.stage='assembly'
            commands['setComponentStage'].run(component=self.code,stage='MODULE_LOADING')
            print 'changed STAVE stage to be assembly!'
            #setstage to assembly for this stave
        #----find module code and fill in properties from cali file-----#
        module.readCSV(dir) #read modulesID.csv to update local ID (RFID/LOCALNAME) according to position
        module_code=module.code #code is updated as soon as local ID is found
        module.Calibration(dir) #update calibration timestamp and SIDE
        module.Survey() #update survey timestamp
        #if module.pass_reception==False:
            #print 'module did not pass tests at reception! Check for defects!'
        ###------fill in more properties--------###
        child_properties=module.childProperties
        child_properties['SITE']=self.site
        if 'LHS' in self.side:
            child_slot=self.slotIDs[position-1]
        else:
            child_slot=self.slotIDs[14+position-1]
        #if self.code==None:
            #self.code=FindComp(LOCALNAME=self.localname,comp_type=self.component)['code']
        #print 'getting ready to assemble...'
        #print 'assemble Stave:',self.code
        #print 'and module:', module_code
        print 'childProperties are:', child_properties
        print 'about to assemble module at position', position
        if getYesOrNo('are you sure you want to assemble? (inset \'y\' or\'n\')'):
            #commands['assembleComponent'].run(parent=self.code,child=module_code,properties=child_properties)
            commands['assembleComponentBySlot'].run(parent=self.code,child=module_code,slot=child_slot,properties=child_properties)
            print 'assembled successfully'
            #location=str(child_properties['SIDE']) + str(child_properties['POSITION'])
            #self.modules[location]={}
            #for key in child_properties.keys(): #save information in this local stave object
                #self.modules[location]['id']=module.id
                #self.modules[location]['serial']=module.findMODULE()['serialNumber']
                #self.modules[location]['type']=module.findMODULE()['type']['name']
                #self.modules[location][key]=properties[key]

            ###----update module object for cross checking later (prevent assemble same module again)---##
            module.stage='assembly'
            module.assembled=True
            #commands['assembleComponent'].run(parent = self.code , child=module['code'] , properties=)
            #print self.modules
            ###------finished assembly this module--------###
        else:
            print 'Canceled module %i assembly' % position
        ##---save assembled module information locally at this stave object--------##

class MODULE(object):
    def __init__(self, name, ID=None, position=None, STAGE='reception'):
        self.component='MODULE'
        self.name=name
        self.id=ID #assume RFID; but test with local name
        self.code=None
        self.position=position
        self.directory=None #this module's calibration directory path
        self.stage=STAGE
        self.pass_reception = False
        self.assembled = False
        self.childProperties={}

    def findMODULE(self):
        module = FindComp(LOCALNAME=self.id,comp_type=self.component)
        self.code=module['code']
        return module

    def readCSV(self,dir): #get all child parent Properties
        csv = np.genfromtxt(dir+'modulesID.csv',delimiter=",",dtype=str)
        IDs=csv[1:,0]
        Positions=csv[1:,1]
        #print IDs
        #print Positions
        if self.position!=None:
            self.id=IDs[Positions.tolist().index(str(self.position))]
            #print 'updated module (%s) ID (LOCALNAME): %s' %(self.name,self.id)
            self.findMODULE()
        elif self.id!=None:
            self.position=Positions[IDs.tolist().index(str(self.id))]
            #print 'updated moduel (%s) position' %(self.name,self.position)

    def modulesInCali(self,dir):
        import os
        dir += 'ModulePlacement/'
        module_num=[]
        total=len([file for file in os.listdir(dir)])
        for i in range(1,total+1):
            checkFolder=dir+str(i)+'/'
            Survey= checkFolder+'/Module_'+str(i)+'.txt'
            input=open(Survey,"r")
            lines=input.readlines()
            input.close()
            if len(lines) > 26:
                #print('module %i is loaded using calibration in %s' %(i,dir))
                module_num.append(i)
        if len(module_num)==0:
            print 'no module loading in this file; only a testing calibration'
        return module_num

    def Calibration(self,dir): #directory to all the calibration folders
        calibrations=[] #paths to each calibration folder
        for file in os.listdir(dir):
            if os.path.isdir(dir+file):
                calibrations.append(dir+file+'/') # all calibrations folders
        print 'there are %i calibrations' %len(calibrations)
        cali_mod={}
        self.childProperties['CALIBRATION']=None
        self.childProperties['SIDE']=None
        self.childProperties['POSITION']=str(self.position) #must be string
        for calibration in calibrations:
            module_num=self.modulesInCali(calibration)#array of the modules' POSITIONS in this calibration
            if self.position in module_num:
                self.directory=calibration
                print 'module at position %i is in calibration:%s' %(self.position,calibration)
                #find properties in calibration file
                input=open(calibration+'CalibrationResults.ini',"r")
                lines=input.readlines()
                input.close()
                for line in lines:
                    if 'StaveOrientation' in line:
                        ind=line.index('=')+3
                        self.childProperties['SIDE']=line[ind:-3]
                    if 'Date' in line:
                        ind=line.index('=')+3
                        cali_timestamp=line[ind:-3]
                        if 'EST' not in line:
                            cali_timestamp+=' EST'
                        self.childProperties['CALIBRATION']=cali_timestamp
                print 'updated Calibration timestamp and SIDE for module', self.name
                return calibration
        if self.childProperties['CALIBRATION']==None:
            print 'no module at this position; or calibration is saved in a different directory'

    def Survey(self):
        dir=self.directory+"ModulePlacement/"+str(self.position)+"/"
        survey=RS.TheSurveys("Module"+str(self.position),"Module_"+str(self.position)+".txt",dir)
        print survey.timestamps
        if 'AG' in survey.GetAllTime().keys():
            GlueTime=survey.GetAllTime()['AG']
            if 'EST' not in GlueTime:
                GlueTime+=' EST'
            self.childProperties['SURVEY']=GlueTime
            return GlueTime
        else:
            print('no After Glue timestamp, left survey timestamp in child properties blank...')

class CORE(object):
    def __init__(self,name='coreName',type='LS',side='A'):
        self.component='CORE'
        #self.id=ID
        self.name=name
        self.side=side
        self.type=type

class EoS(object):
    def __init__(self,ID):
        self.component='EoS'
        self.id=ID


def getYesOrNo(prompt):
    print prompt
    while True:
        # Get our input
        response = raw_input().strip() # changed input()-->raw_input
        # Skip empty inputs
        if response == '':
            continue
        # If yes, return True
        elif response in ['y', 'Y', 'yes', 'Yes', 'YES', '1','true','True']:
            return True
        # If no, return False
        elif response in ['n', 'N', 'no', 'No', 'NO', '0','false','False']:
            return False
        # Else the input is invalid and ask again
        else:
            del response
            print 'Invalid input. Please enter \'y/Y\', or \'n/N\':'
            continue

def FindComp(LOCALNAME=None, RFID=None,comp_type=None):
    if LOCALNAME==None and RFID==None:
        ID=raw_input("Please insert a local name or RFID:")
        while ID==None:
            ID=raw_input("Invalid input. Please insert a local name or RFID:")
    elif LOCALNAME!=None:
        ID = LOCALNAME
    elif RFID!=None:
        ID = RFID
    if comp_type==None:
        comp_type=raw_input("Please insert the component type (STAVE/MODULE/EOS):")
        while comp_type==None:
            comp_type=raw_input("Invalid input. Please insert component type (STAVE/MODULE/EOS):")

    property_filter = [{'code': 'LOCALNAME', 'operator': '=', 'value': ID}, {'code': 'LOCAL_NAME', 'operator': '=', 'value': ID},
                                    {'code': 'RFID', 'operator': '=', 'value': ID}]
    component_list=commands['listComponentsByProperty'].run(project='S',componentType=comp_type,propertyFilter=property_filter)
    #if no component found, keep asking for correct local name till found at least one (exit by keyboard error, ex. ^C)
    while len(component_list)==0:
        print 'No %s was found using ID:'%comp_type,ID
        ID=raw_input("Please reenter the ID for this %s:" %comp_type)
        property_filter = [{'code': 'LOCALNAME', 'operator': '=', 'value': ID}, {'code': 'LOCAL_NAME', 'operator': '=', 'value': ID},
                                            {'code': 'RFID', 'operator': '=', 'value': ID}]
        component_list=commands['listComponentsByProperty'].run(project='S',componentType=comp_type,propertyFilter=property_filter)

    if len(component_list)>1:##in the case PD has multiple components with the same Local Name
        print "found more than 1 %s with ID %s" %(comp_type,ID)
        for ind, component in enumerate(component_list):
            print ind+1,'.   type:',component['type']['name'], ',  institution:',component['institution']['name'],',  current localtion:',component['currentLocation']['name']
        while True:
            try:
                i=raw_input('please give the index of the component:')
                i=int(i.strip())
                component = component_list[i-1]
                return component
            except IndexError:
                print 'Invalid index, try again'
    elif len(component_list)==1:
        return component_list[0]


def main(args):
    print('')
    print('*************************************************************************')
    print('* *                                                                 *   *')
    print('*                            LoadedStave.py --JiayiChen                 *')
    print('* *                                                                 *   *')
    print('*************************************************************************')
    print('')

    directory=args.directory

    while not os.path.exists(directory):
        print 'calibration path (%s) not found' %directory
        directory=raw_input("Please enter the path to calibtration again:")
    if directory[-1]!='/':
        directory+='/'

    if args.positions!='all':
        positions=[int(x) for x in args.positions.split(",")]
    else:
        positions=np.arange(1,15,1)

    if args.command=='initiate':
        print 'Welcome to ITk PD STAVE assembly DAY1!'
        localname=raw_input('please give the new STAVE a local name: ')
        newCore=CORE(type='SS',side='A')
        newStave=STAVE(LOCALNAME=localname,dir=directory) #default stage reception
        newStave.addCore(newCore)
        newStave.registerSTAVE()
        for position in positions:
            module=MODULE('Module'+str(position), position=position)
            newStave.addModule(module)

    if args.command=='update':
        print 'Welcome back to ITk PD STAVE assembly!!'
        localname=raw_input('please give the stave local name to find this STAVE: ')
        thisStave=STAVE(LOCALNAME=localname,dir=directory,STAGE='assembly') #since day2 start with assembly stage
        component=thisStave.StaveINFO()
        print 'Found the following stave using local name',localname
        print 'type(LS/SS):',component['type']['name']
        print 'institution:',component['institution']['name']
        print 'current localtion:',component['currentLocation']['name']

        if getYesOrNo('Is this the stave you are looking for? (insert \'y\' or \'n\')'):
            for position in positions:
                module=MODULE('Module'+str(position), position=position)
                thisStave.addModule(module)
        else:
            print('Wrong STAVE. Exiting program.')
            exit()



if __name__ =='__main__':
    parser=argparse.ArgumentParser(description='Load A STAVE in the ITk PD')
    parser.add_argument('command',type=str,choices=['initiate','update'],help='initiate: register new STAVE and assemble modules; update: find STAVE and assemble more modules')
    parser.add_argument('--directory',type=str, help='path to the stave assembly info folder(./Calibrations/)')
    parser.add_argument('--positions',type=str,help='enter module positions (ex. 2,3,4); enter \'all\' for all module 1-14')
    args=parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        print('')
        print 'Exectution terminated.'
        print 'Finished with error.'
        exit()
