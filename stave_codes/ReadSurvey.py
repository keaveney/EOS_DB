#!/usr/bin/env python3
import numpy as np
#import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
import collections
import argparse
#import pandas as pd


def StringtoFlt(string):
    flt = None
    if ("\n" in string):
        string.replace("\n", "")
    if ("=" in string):
        string = string[string.find("=") + 1:]
    try:
        flt = float(string)
    except ValueError:
        print("Cannot convert string to float!")
    return flt

def RepealAndReplace(string, repeal, replace = 1):
    if (repeal in string):
        ind = string.index(repeal)
        string = string[0 : ind + replace] + string[ind + len(repeal) : ]
    return string

def RenameStages(stages):
    output = []
    for ind,stage in enumerate(stages):

        stage = RepealAndReplace(stage, 'Right', 0)
        stage = RepealAndReplace(stage, 'Before')
        stage = RepealAndReplace(stage, 'After')
        stage = RepealAndReplace(stage, 'Gluing')
        stage = RepealAndReplace(stage,'Glue')
        stage = RepealAndReplace(stage, 'Bridge') #, 2),Changed this, otherwise -- BBrR
        stage = RepealAndReplace(stage, 'Removal')
        while ('_' in stage):
            stage = stage.replace('_','')

        BBR1=-1
        ABR1=-1
        if "BBR" in stage:
            if BBR1 == -1:
                BBR1=ind
                stage="BBR"
        if "ABR" in stage:
            if ABR1 == -1:
                BBR1=ind
                stage="ABR"
        output.append(stage)
    #print(output)
    return output

class TheSurveys(object):
    def __init__(self, name, infile, dir):
        self.name = name
        self.infile = dir + infile
        self.lines = self.GetLines()
        self.timestamps=self.GetAllTime()
        self.corners = self.SeparateByCorner()
        self.stages = self.GetStages()
        self.results = self.GetResults()
        self.tolerance = 25
        self.passed, self.failures,self.failX,self.failY, self.DeltaXY= self.DidItPass()
        self.glued = self.WasItGlued()

    def GetLines(self):
        input = open(self.infile,"r")
        lines = input.readlines()
        input.close()
        return lines

    def SeparateByCorner(self):
        indA, indB, indC, indD = 0, 0, 0, 0
        for ind, line in enumerate(self.lines):
            if ("CornerA" in line):
                indA = ind + 1
            elif ("CornerB" in line):
                indB = ind + 1
            elif ("CornerC" in line):
                indC = ind + 1
            elif ("CornerD" in line):
                indD = ind + 1

        corners = collections.OrderedDict()
        corners['A'] = self.lines[indA : indB - 2]
        corners['B'] = self.lines[indB : indC - 2]
        corners['C'] = self.lines[indC : indD - 2]
        corners['D'] = self.lines[indD : ]

        return corners

    def GetStages(self):
        stages = []
        for line in self.corners['A']:
            stage = line[line.find("_") + 1: line.find("=") - 1]
            if (stage not in stages):
                stages.append(stage)
        stages = RenameStages(stages)

        if "AG" not in stages:
            print("WARNING: no AG for %s." %self.name)
        if "BBR" not in stages:
            print("WARNING: no BBR for %s, possibly glue not cured yet." %self.name)
        if "ABR" not in stages:
            print("WARNING: no ABR for %s, possibly bridge not removed yet" %self.name)
        return stages

    def GetAllTime(self):
        DateAndTime = collections.OrderedDict()
        for line in self.lines:
            if "Date" in line:
                if "AG" in line or "AfterGlue" in line or "After Glue" in line:
                    AGtime=line[line.find("=")+3:line.find(".")-2]
                    DateAndTime['AG']=AGtime
                    #print("Date and time of gluing:", AGtime)
                if "ABR" in line or "AfterBridgeRemoval" in line or "After Bridge" in line:
                    ABRtime=line[line.find("=")+3:line.find(".")-2]
                    DateAndTime['ABR']=ABRtime
                    #print("Date and time of bridge removal:", ABRtime)
        return DateAndTime

    #def GetCureTime(self):

    def GetResults(self):
        results = collections.OrderedDict()

        for ind, stage in enumerate(self.stages):
            results[stage] = collections.OrderedDict()
            for corner in self.corners.keys():
                results[stage][corner] = []
                for xyz in range(3):
                    pos = StringtoFlt(self.corners[corner][(3 * ind) + xyz])
                    results[stage][corner].append(pos)
        return results

    def DidItPass(self):
        dims = ['X', 'Y']
        passed = True
        failures = []
        failX=False
        failY=False
        DeltaXY=collections.OrderedDict()
        for stage in self.stages:
            DeltaXY[stage]={}
            for corner in self.corners.keys():
                DeltaXY[stage][corner]=[]
                for xyz, dim in enumerate(dims):
                    movement = 1000 * (self.results[stage][corner][xyz] - self.results[self.stages[0]][corner][xyz])
                    DeltaXY[stage][corner].append(float('%.3g' % movement)) #3 sig fig)
                    if (abs(movement) >= self.tolerance):
                        passed = False
                        if failX==False and dim=='X':
                            failX=True
                        if failY==False and dim=='Y':
                            failY=True
                        failures.append(corner + ' - ' + stage + ': delta' + dim + ' = ' + str(movement) + ' um')

        return passed, failures, failX, failY, DeltaXY

    def WasItGlued(self):
        glued=True
        stages=self.stages
        if "AG" not in stages and "ABR" not in stages and "BBR" not in stages:
            glued=False
        return glued

    def PrintTheFailures(self):
        print('')
        print('----------------------------------------')
        if self.passed:
            print(self.name)
            print("Passed! All surveys within " + str(self.tolerance) + " um tolerance.")
        else:
            print(self.name)
            print("Failed! The following corners are out of " + str(self.tolerance) + " um tolerance: ")
            for failure in self.failures:
                print(failure)
        print('----------------------------------------')
        print('')


if __name__ == '__main__':

    # Define our parser
    parser = argparse.ArgumentParser(description = 'read a survey file')
    #parser._action_groups.pop()

    # Define our required arguments
    #required = parser.add_argument_group('required arguments')
    parser.add_argument('--surveyPath', dest = 'survey_path', type = str, help = 'path to the survey')
    parser.add_argument('--module-num', dest= 'module_num',type=int,help='read survey file of this module')
    # Define our optional arguments
    #optional = parser.add_argument_group('optional arguments')

    #optional.add_argument('--getConfirm', dest = 'confirm', action = 'store_true', help = 'print survey stages')

    args = parser.parse_args()

    modules = [args.module_num]
    for module in modules:
        dir=args.survey_path+"ModulePlacement/"+str(module)+"/"
        survey = TheSurveys("Module" + str(module), "Module_" + str(module) + ".txt",dir)

        #print(survey.name)
        #print(survey.infile)
        #print(survey.timestamps['ABR'])
        survey.PrintTheFailures()
