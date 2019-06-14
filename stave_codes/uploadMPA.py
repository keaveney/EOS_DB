#!/usr/bin/env python

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import numpy as np
import collections
import argparse
import ReadSurvey as RS
import json
from itk_pdb.databaseUtilities import commands
from LoadedStave import FindComp
from datetime import date

#module_num=np.arange(2,14,1)

class MPAtest(object):
    def __init__(self,LOCALNAME=None,institution='BU',side="RHS"):
        self.localname=LOCALNAME
        self.institution=institution
        self.stave_side=side #run number
        self.stave_code=FindComp(LOCALNAME=self.localname,comp_type='STAVE')['code']
        self.slotIDs=self.childrenSlots()
        self.json=self.initiateSurvey()

    def childrenSlots(self):
        STAVE = commands['getComponent'].run(component=self.stave_code)
        children=STAVE['children']
        slotid=[]
        for component in children:
            id=component['id']
            slotid.append(id)
        return slotid

    def initiateSurvey(self):
        DTO={
        "component": self.stave_code,
        "testType": "SURVEY2",
        "institution": self.institution,
        "runNumber":self.stave_side,
        "date": date.today().strftime("%d.%m.%Y"),
        "passed": False,
        "problems": True,
        "properties": {},
        "results":{"PASS":[],"FAIL-X":[],"FAIL-Y":[],"FAIL-XY":[]}}

        return DTO
    def fillResults(self,dir=None,modules=[2]):
        fillFiducial=False
        Passed=True
        num_fail=0
        for module in modules:
            survey = RS.TheSurveys("Module"+str(module), "Module_"+str(module) +".txt",dir)
            survey.PrintTheFailures()
            #
            if not fillFiducial:
                for line in survey.lines:
                    if "FiducialMark" in line:
                        fiducial=line[line.find("=")+3:-3]
                        self.json["properties"]["FIDUCIAL"]=fiducial
                fillFiducal=True
            result={}
            slot=module-1
            if self.stave_side=='RHS':
                slot+=14
            result["childParentRelation"]=self.slotIDs[slot]
            if 'ABR' in survey.stages:
                result["value"]=survey.DeltaXY['ABR']
            else:
                print 'Stage ABR not in the stages, here are the stages:',survey.stages
                while True:
                    try:
                        stage=raw_input('enter the stage you want:')
                        result["value"]=survey.DeltaXY[stage]
                        break
                    except KeyError:
                        print 'wrong input, please insert one of the following stages:'
                        print survey.stages

            if survey.passed==True:
                self.json["results"]["PASS"].append(result)
            else:
                Passed=False
                num_fail+=1
                if survey.failX==True and survey.failY==False:
                    self.json["results"]["FAIL-X"].append(result)
                elif survey.failX==False and survey.failY==True:
                    self.json["results"]["FAIL-Y"].append(result)
                else:
                    self.json["results"]["FAIL-XY"].append(result)
        self.json["passed"]=Passed
        self.json["problem"]=not Passed
        self.json["properties"]['FAILURE']=num_fail

def main(args):
    print('')
    print('*************************************************************************')
    print('* *                                                                 *   *')
    print('*                            uploadMPA.py --JiayiChen                 *')
    print('* *                                                                 *   *')
    print('*************************************************************************')
    print('')
    test=MPAtest(LOCALNAME='ShortTestingJiayi',side=args.stave_side)
    modu_positions=np.arange(2,14,1)
    test.fillResults(dir='../../electricalStave/',modules=modu_positions) #needs to be changed for real final survey
    if args.command=='upload':
        commands['uploadTestRunResults'].run(**test.json)
        print 'finished uploading'
    else:
        print 'filled the DTO:'
        print test.json

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='upload Module Placement Accuracy test to ITk PD')
    parser.add_argument('command',type=str,choices=['testing','upload'],help='testing: will show the json only; upload: will upload json to PD')
    parser.add_argument('--stave-side',type=str, help='the side of the stave modules are loaded on')
    args=parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        print ''
        print 'Exectution terminated.'
        print 'Finished with error.'
        exit()
