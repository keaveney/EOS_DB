#!/usr/bin/env python
# ITSDAQTestClasses_RETIRED.py -- classes relevant for representing ITSDAQ results summary files
# Created: 2018/07/29, Updated: 2019/01/28
# Written by Matthew Basso

import os
from itk_pdb.databaseUtilities import INFO, WARNING
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Include a class for skipping over components which cannot be identified in ResultSummaryFile.finalizeJSON()
class Skip(Exception):
    pass

# Define our ResultsSummaryFile object
class ResultsSummaryFile(object):

    # Define our init function and initialize tests
    def __init__(self, filepath, pspath = None, configpath = None):
        self.filepath = os.path.abspath(filepath)
        if pspath != None:
            self.pspath = os.path.abspath(pspath) + '/'
        else:
            self.pspath = None
        if configpath != None:
            self.configpath = os.path.abspath(configpath) + '/'
        else:
            self.configpath = None
        self.tests = []

    # Return every line in filepath
    def __getLines(self):
        with open(self.filepath, 'r') as file:
            lines = file.readlines()
        return lines

    # Parse lines in order to identify all of the tests performed, returned as a list of dictionaries
    # NOTE: the following function is heavily hardcoded and relies on the patterns present in most results summary files
    # As a result, it is important to check that the output of the function appears to make sense
    def getTests(self):

        # Get our lines
        lines = self.__getLines()

        # Initialize our list of tests and test_number (= number of tests found in the provided lines)
        tests = []
        test_number = 0

        # Read every line
        for i, line in enumerate(lines):

            # Throw away the line if the first character is not %
            if line[0] == '%':

                # Parse general info
                if '%NewTest' in line:
                    tests.append({'JSON': {'properties': {}, 'results': {}}, 'extra_data': {'NewTest_EXTRA': {}, 'DAQ_INFO_EXTRA': {}, 'DCS_INFO': {}, 'SCAN_INFO': {},
                                    'identifiers': {}}, 'files_to_upload': {}})

                    # Read serial number, user, location, run number, date, passed, and problem
                    # Properties which are needed for the JSON input to the database are thrown in extra_data
                    tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] = lines[i+2][17:-1]
                    tests[test_number]['JSON'].update({
                        'runNumber':        lines[i+5][17:-1],
                        'date':             lines[i+6][17:-1].replace('/', '.'),
                        'passed':           True if lines[i+7][17:-1] == 'YES' else (False if lines[i+7][17:-1] == 'NO' else None),
                        'problems':          True if lines[i+8][17:-1] == 'YES' else (False if lines[i+8][17:-1] == 'NO' else None)
                    })
                    tests[test_number]['extra_data']['NewTest_EXTRA'].update({
                        'user':             lines[i+3][17:-1],
                        'location':         lines[i+4][17:-1]
                    })

                # Parse DAQ info all tests
                elif '%DAQ_INFO' in line:

                    # Read host, version, DUT, and time
                    tests[test_number]['JSON']['properties'].update({
                        'ITSDAQ_VERSION': lines[i+5][1:-2],
                        'TIME':             lines[i+9][1:-2]
                    })
                    tests[test_number]['extra_data']['DAQ_INFO_EXTRA'].update({
                        'host':             lines[i+3][1:-2],
                        'DUT':              lines[i+7][1:-2]
                    })
                     
                # Parse DCS info
                elif '%DCS_INFO' in line:

                    # Read T0, T1, VDET, IDET, VCC, ICC, VDD, and IDD, and time_powered (all thrown into extra_data)
                    tests[test_number]['extra_data']['DCS_INFO'].update({
                        'T0':               float(lines[i+3].split()[0]),
                        'T1':               float(lines[i+3].split()[1]),
                        'VDET':             float(lines[i+5].split()[0]),
                        'IDET':             float(lines[i+5].split()[1]),
                        'VCC':              float(lines[i+7].split()[0]),
                        'ICC':              float(lines[i+7].split()[1]),
                        'VDD':              float(lines[i+9].split()[0]),
                        'IDD':              float(lines[i+9].split()[1]),
                        'time_powered':     lines[i+11][:-2]
                    })

                # Parse scan info (only for 3PG, response curve, and trim range)
                elif '%SCAN_INFO' in line:

                    # Read point_type, N_points, and points (all thrown into extra data)

                    # Use a special function to get the points as sometimes the points can be distributed over 2 lines or have .'s included
                    j = 7
                    points = []
                    while True:
                        if '#' in lines[i+j]:
                            break
                        else:
                            points += list(map(float, filter(lambda point: point != '.', lines[i+j].split())))
                            j += 1

                    tests[test_number]['extra_data']['SCAN_INFO'].update({
                        'point_type':       lines[i+3][1:-2],
                        'N_points':         int(lines[i+5]),
                        'points':           points
                    })

                    # Save the scan info to SCAN_INFO for the type = -1 trim range scan
                    SCAN_INFO = tests[test_number]['extra_data']['SCAN_INFO']

                # Parse StrobeDelay specific info
                elif '%StrobeDelay' in line:

                    # Read test type
                    tests[test_number]['JSON']['testType'] = 'STROBE_DELAY'

                    # Read the strobe delay fraction
                    # We use this while loop to skip defects
                    j = 11
                    while True:
                        if 'Strobe Delay Fraction' in lines[i+j]:
                            break
                        else:
                            j += 1
                    tests[test_number]['JSON']['properties']['FRACTION'] = float(lines[i+j].split()[5])

                    # Read stream delays (excluding delays = -1 as they indicate missing ABCs)
                    delays_stream0 = list(map(int, lines[i+4].split()))
                    delays_stream1 = list(map(int, lines[i+7].split()))
                    tests[test_number]['JSON']['results'].update({
                        'STREAM0_DELAYS':   [delay for delay in delays_stream0 if delay != -1],
                        'STREAM1_DELAYS':   [delay for delay in delays_stream1 if delay != -1]
                    })

                    # Read our identifiers
                    identifiers_stream0 = lines[i+3].split()[1:]
                    identifiers_stream1 = lines[i+6].split()[1:]
                    tests[test_number]['extra_data']['identifiers'].update({
                        'stream0':          [identifiers_stream0[i] for i in range(len(identifiers_stream0)) if delays_stream0[i] != -1],
                        'stream1':          [identifiers_stream1[i] for i in range(len(identifiers_stream1)) if delays_stream1[i] != -1]
                    })


                    # Include the files to be uploaded
                    if self.pspath != None:
                        strobe_delay_path = self.pspath + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_StrobeDelayPlot_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                        if os.path.exists(strobe_delay_path):
                            tests[test_number]['files_to_upload']['strobe_delay_path'] = strobe_delay_path
                    if self.configpath != None:
                        det_path = self.configpath + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '.det' 
                        if os.path.exists(det_path):
                            tests[test_number]['files_to_upload']['det_path'] = det_path

                    # Increment test_number
                    test_number += 1

                # Parse ThreePointGain specific info
                elif '%ThreePointGain' in line:

                    # Read test type
                    tests[test_number]['JSON']['testType'] = 'THREE_POINT_GAIN'

                    # We fetched the midpoint earlier (the second value in points in SCAN_INFO)
                    tests[test_number]['JSON']['properties']['MIDPOINT'] = tests[test_number]['extra_data']['SCAN_INFO']['points'][1]

                    # The following lists contains the keys for our results dictionary in the order in which the keys will be read from the lines in the summary file
                    stream0_keys = ['STREAM0_P0', 'STREAM0_P1', 'STREAM0_VT50', 'STREAM0_VT50_RMS', 'STREAM0_GAIN', 'STREAM0_GAIN_RMS', 'STREAM0_OFFSET', 'STREAM0_OFFSET_RMS',
                                    'STREAM0_OUTNSE', 'STREAM0_INNSE', 'STREAM0_INNSE_RMS']
                    stream1_keys = ['STREAM1_P0', 'STREAM1_P1', 'STREAM1_VT50', 'STREAM1_VT50_RMS', 'STREAM1_GAIN', 'STREAM1_GAIN_RMS', 'STREAM1_OFFSET', 'STREAM1_OFFSET_RMS',
                                    'STREAM1_OUTNSE', 'STREAM1_INNSE', 'STREAM1_INNSE_RMS']

                    # Initialize our results dictionary for all of our stream 0/1 keys
                    results = {}
                    for key in stream0_keys:
                        results[key] = []
                    for key in stream1_keys:
                        results[key] = []

                    # j_loopA_identifier refers to the number of lines below line i (i.e., '%ThreePointGain') where the chip identifiers (e.g., '#M16') begin for Loop A
                    j_loopA_identifier = 4
                    j = j_loopA_identifier

                    # We'll dump the data from Loop A into data_loopA and our identifiers (chip IDs)
                    data_loopA = []
                    identifiers = []

                    while True:
                        
                        # If the line has only '#\n' on it, we know we reached the end of Loop A and need to break
                        if lines[i+j] == '#\n':
                            break

                        # Else we'll append the data line (1 line below i+j) to data_loopA as well as our identifiers to identifiers
                        else:
                            data_loopA.append(lines[i+j+1].split()[1:3])
                            identifiers.append(lines[i+j][1:-1])
                            j += 2

                    # Calculate the number of chips
                    number_of_chips = (j - j_loopA_identifier) / 4

                    # j_loopB_data refers to the number of lines below line i where the data lines begin for Loop B
                    j_loopB_data = j + 4

                    # Iterate over the number of chips
                    for k in range(0, number_of_chips):

                        # Get the line data for both stream 0/1 for Loop B and add it to the corresponding line for Loop A
                        # We filter the lines so nan's go to -1000000 and so do the 'Too many defects in this chip!' Loop B rows (should be recognized as an error)
                        if 'Too many defects in this chip!' in lines[i+j_loopB_data+2*k]:
                            line_data_stream0 = data_loopA[k] + 9 * ['-1000000']
                        else:
                            line_data_stream0 = data_loopA[k] + [datum if 'nan' not in datum else '-1000000' for datum in lines[i+j_loopB_data+2*k].split()]
                        if 'Too many defects in this chip!' in lines[i+j_loopB_data+2*(number_of_chips+k)]:
                            line_data_stream1 = data_loopA[k+number_of_chips] + 9 * ['-1000000']
                        else:
                            line_data_stream1 = data_loopA[k+number_of_chips] + [datum if 'nan' not in datum else '-1000000' for datum in
                                                                                    lines[i+j_loopB_data+2*(number_of_chips+k)].split()]

                        # Assuming len(stream0_keys) == len(stream1_keys), we can append the data lines from above to their respective dictionaries
                        # 'STREAM0/1_INNSE' and 'STREAM0/1_INNSE_RMS' look like integers?
                        for ii in range(len(stream0_keys)):
                            results[stream0_keys[ii]].append(int(line_data_stream0[ii]) if (stream0_keys[ii] == 'STREAM0_INNSE' or  stream0_keys[ii] == 'STREAM0_INNSE_RMS')
                                                                else float(line_data_stream0[ii]))
                            results[stream1_keys[ii]].append(int(line_data_stream1[ii]) if (stream1_keys[ii] == 'STREAM1_INNSE' or  stream1_keys[ii] == 'STREAM1_INNSE_RMS') 
                                                                else float(line_data_stream1[ii]))

                    # Update results and identifiers and increment test_number
                    tests[test_number]['JSON']['results'] = results
                    tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_chips], 'stream1': identifiers[number_of_chips:]})
                    if self.pspath != None:
                        three_point_gain_path = self.pspath + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_RCPlot_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                        if os.path.exists(three_point_gain_path):
                            tests[test_number]['files_to_upload']['three_point_gain_path'] = three_point_gain_path
                    test_number += 1

                # Parse ResponseCurve specific info
                elif '%ResponseCurve' in line:

                    # Read test type
                    tests[test_number]['JSON']['testType'] = 'RESPONSE_CURVE'

                    # CHECK ME: We fetched the input charge earlier (the sixth value in points in SCAN_INFO)
                    tests[test_number]['JSON']['properties']['INPUT_CHARGE'] = tests[test_number]['extra_data']['SCAN_INFO']['points'][5]
           
                    # The following lists contains the keys for our results dictionary in the order in which the keys will be read from the lines in the summary file
                    stream0_keys = ['STREAM0_P0', 'STREAM0_P1', 'STREAM0_P2', 'STREAM0_VT50', 'STREAM0_VT50_RMS', 'STREAM0_GAIN', 'STREAM0_GAIN_RMS', 'STREAM0_OFFSET',
                                    'STREAM0_OFFSET_RMS', 'STREAM0_OUTNSE', 'STREAM0_INNSE', 'STREAM0_INNSE_RMS']
                    stream1_keys = ['STREAM1_P0', 'STREAM1_P1', 'STREAM1_P2', 'STREAM1_VT50', 'STREAM1_VT50_RMS', 'STREAM1_GAIN', 'STREAM1_GAIN_RMS', 'STREAM1_OFFSET',
                                    'STREAM1_OFFSET_RMS', 'STREAM1_OUTNSE', 'STREAM1_INNSE', 'STREAM1_INNSE_RMS']

                    # Initialize our results dictionary for all of our stream 0/1 keys
                    results = {}
                    for key in stream0_keys:
                        results[key] = []
                    for key in stream1_keys:
                        results[key] = []

                    # j_loopA_identifier refers to the number of lines below line i (i.e., '%ResponseCurve') where the chip identifiers (e.g., '#M16') begin for Loop A
                    j_loopA_identifier = 4
                    j = j_loopA_identifier

                    # We'll dump the data from Loop A into data_loopA and our identifiers (chip IDs) to identifiers
                    data_loopA = []
                    identifiers = []

                    while True:
                        
                        # If the line has only '#\n' on it, we know we reached the end of Loop A and need to break
                        if lines[i+j] == '#\n':
                            break

                        # Else we'll append the data line (1 line below i+j) to data_loopA as well as our identifiers to identifiers
                        else:
                            data_loopA.append(lines[i+j+1].split()[1:])
                            identifiers.append(lines[i+j][1:-1])
                            j += 2

                    # Calculate the number of chips
                    number_of_chips = (j - j_loopA_identifier) / 4

                    # j_loopB_data refers to the number of lines below line i where the data lines begin for Loop B
                    j_loopB_data = j + 4

                    # Iterate over the number of chips
                    for k in range(number_of_chips):

                        # Get the line data for both stream 0/1 for Loop B and add it to the corresponding line for Loop A
                        # We filter the lines so nan's go to -1000000 and so do the 'Too many defects in this chip!' Loop B rows (should be recognized as an error)
                        if 'Too many defects in this chip!' in lines[i+j_loopB_data+2*k]:
                            line_data_stream0 = data_loopA[k] + 9 * ['-1000000']
                        else:
                            line_data_stream0 = data_loopA[k] + [datum if 'nan' not in datum else '-1000000' for datum in lines[i+j_loopB_data+2*k].split()]
                        if 'Too many defects in this chip!' in lines[i+j_loopB_data+2*(number_of_chips+k)]:
                            line_data_stream1 = data_loopA[k+number_of_chips] + 9 * ['-1000000']
                        else:
                            line_data_stream1 = data_loopA[k+number_of_chips] + [datum if 'nan' not in datum else '-1000000' for datum in
                                                                                    lines[i+j_loopB_data+2*(number_of_chips+k)].split()]

                        # Assuming len(stream0_keys) == len(stream1_keys), we can append the data lines from above to their respective dictionaries
                        # 'STREAM0/1_INNSE' and 'STREAM0/1_INNSE_RMS' look like integers?
                        for ii in range(len(stream0_keys)):
                            results[stream0_keys[ii]].append(int(line_data_stream0[ii]) if (stream0_keys[ii] == 'STREAM0_INNSE' or  stream0_keys[ii] == 'STREAM0_INNSE_RMS')
                                                                else float(line_data_stream0[ii]))
                            results[stream1_keys[ii]].append(int(line_data_stream1[ii]) if (stream1_keys[ii] == 'STREAM1_INNSE' or  stream1_keys[ii] == 'STREAM1_INNSE_RMS') 
                                                                else float(line_data_stream1[ii]))

                    # Update results and identifiers and increment test_number
                    tests[test_number]['JSON']['results'] = results
                    tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_chips], 'stream1': identifiers[number_of_chips:]})
                    if self.pspath != None:
                        response_curve_path = self.pspath + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_RCPlot_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                        if os.path.exists(response_curve_path):
                            tests[test_number]['files_to_upload']['response_curve_path'] = response_curve_path
                    test_number += 1

                # Parse Trim specific info
                elif '%Trim' in line:

                    # We only want the last trim range scan of a given set (type = -1)
                    trim_type = int(lines[i+3].split()[1])
                    if trim_type == -1:

                        # Update the test type
                        tests[test_number]['JSON']['testType'] = 'TRIM_RANGE'

                        # Assuming the scan info is the same for every trim range scan up to the type = -1 scan, we can grab scan info from the last scan
                        # Scan info must be passed to the type = -1 scan as it does not have scan info associated with its %NewTest
                        tests[test_number]['extra_data']['SCAN_INFO'].update(SCAN_INFO)

                        # Initialize our results dictionary
                        results = {'STREAM0_RANGE': [], 'STREAM0_TARGET': [], 'STREAM1_RANGE': [], 'STREAM1_TARGET': []}

                        # j_identifier refers to the number of lines below line i (i.e., '%Trim') where the channel identifiers (e.g., '#Ch16') begin
                        j_identifier = 7
                        j = j_identifier

                        # We'll dump the data from Loop A into data_loopA and our identifiers (channels) to identifiers
                        data = []
                        identifiers = []

                        while True:
                        
                            # If the line has only '#\n' on it, we break
                            if lines[i+j] == '#\n':
                                break

                            # Else we'll append the data line (1 line below i+j) to data as well as our identifiers to identifiers
                            else:
                                data.append(lines[i+j+1].split()[0:2])
                                identifiers.append(lines[i+j][1:-1])
                                j += 2

                        # Calculate the number of channels
                        number_of_channels = (j - j_identifier) / 4

                        # Iterate over the number of channels
                        for ii in range(number_of_channels):

                            # Sort through the elements of data and append them appropriately to results
                            results['STREAM0_RANGE'].append(int(data[ii][0]))
                            results['STREAM0_TARGET'].append(float(data[ii][1]))
                            results['STREAM1_RANGE'].append(int(data[ii+number_of_channels][0]))
                            results['STREAM1_TARGET'].append(float(data[ii+number_of_channels][1]))

                        # Update results and identifiers and increment test_number
                        tests[test_number]['JSON']['results'] = results
                        tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_channels], 'stream1': identifiers[number_of_channels:]})
                        trim_path = os.path.dirname(self.filepath) + '/' + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_tr-1_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '.trim'
                        mask_path = os.path.dirname(self.filepath) + '/' + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_tr-1_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '.mask'
                        if os.path.exists(trim_path):
                            tests[test_number]['files_to_upload']['trim_path'] = trim_path
                        if os.path.exists(mask_path):
                            tests[test_number]['files_to_upload']['mask_path'] = mask_path
                        test_number += 1

                    # If it's not the type = -1 trim range test, we want to delete it from tests
                    else:
                        del tests[test_number]

                # Parse noise occupancy specific info
                elif '%NO' in line:

                    # Read test type
                    tests[test_number]['JSON']['testType'] = 'NOISE_OCCUPANCY'

                    # j_identifier refers to the number of lines below line i (i.e., '%NO') where the chip identifiers (e.g., '#M16') begin
                    j_identifier = 3
                    j = j_identifier

                    # We'll dump the data from the chips to data as well as our identifiers to identifiers
                    data = []
                    identifiers = []

                    while True:

                        # If the line has only '#\n' on it, we break
                        if lines[i+j] == '#\n':
                                break

                        # Else if the line is all 0's, we don't want to include it
                        elif [float(datum) for datum in lines[i+j+1].split()] == [0, 0, 0, 0]:
                            j += 2

                        # Else we can append the last element in the row (EstENC) to data as well as our identifiers to identifiers
                        else:
                            data.append(-1000000 if 'nan' in lines[i+j+1].split()[3] else int(lines[i+j+1].split()[3]))
                            identifiers.append(lines[i+j][1:-1])
                            j += 2

                    # Get the number of chips
                    number_of_chips = len(data) / 2

                    # Update results and identifiers and increment test_number
                    tests[test_number]['JSON']['results'].update({'STREAM0_ESTENC':   data[:number_of_chips], 'STREAM1_ESTENC':   data[number_of_chips:]})
                    tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_chips], 'stream1': identifiers[number_of_chips:]})
                    if self.pspath != None:
                        NO_path = self.pspath + tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_NoScurve_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                        if os.path.exists(NO_path):
                            tests[test_number]['files_to_upload']['NO_path'] = NO_path
                    test_number += 1

        # Update self.tests
        self.tests = tests

        # Explicitly delete lines (?)
        del lines

    # Define a function for accessing filepath without specifically targeting the member variable
    def returnFilepath(self):
        return self.filepath

    # Define a function for accessing tests without specifically targeting the member variable
    def returnTests(self, *args):
        if args == ():
            return self.tests
        tests = []
        for test_number in args:
            try:
                tests.append(self.tests[test_number])
            except (IndexError, TypeError):
                pass
        return tests[0] if len(tests) == 1 else tests

    # Return the length of tests
    def returnLengthTests(self):
        return len(self.tests)

    # Print a summary table of the tests found in the results summary file
    def printSummary(self):
        row_format = '{:<10}{:<25}' + 6 * '{:<20}'
        header = ['Index', 'Serial number', 'Test type', 'Date', 'Time', 'Run number', 'Passed', 'Problems']
        print(row_format.format(*header))
        print(150 * '-')
        for i, test in enumerate(self.tests):
            row = [str(i), test['JSON']['properties']['SERIAL_NUMBER'], test['JSON']['testType'], test['JSON']['date'], test['JSON']['properties']['TIME'],
                    test['JSON']['runNumber'], 'YES' if test['JSON']['passed'] == True else 'NO', 'YES' if test['JSON']['problems'] == True else 'NO']
            print(row_format.format(*row))

    # Check if the serial number for a component is a valid ATLAS ITk serial number
    # See: https://indico.cern.ch/event/718637/contributions/2963483/attachments/1634097/2607226/serial_numbers_testbeam2.pdf
    def __checkSerialNumber(self, serial_number):
        XX = ['SB', 'SE', 'SG', 'PB', 'PE', 'PG']
        YY = ['HX', 'HY', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5', 'ML', 'MS', 'M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'AB', 'AH', 'AA', 'AM']
        if ((serial_number[0:3] == '20U') and (len(serial_number) == 14) and (serial_number[3:5] in XX) and (serial_number[5:7] in YY)
            and (serial_number[7] in ['0', '1', '2', '3']) and (serial_number[8] in ['0', '1', '2']) and serial_number[9:].isdigit()):
            return True
        else:
            return False

    # Add the component codes, local object names, and institutions to the JSON for each test
    # Also validate the serial number and replace it if necessary
    def finalizeJSON(self, ITkPDSession, *args):

        if args == ():
            args = range(len(self.tests))

        for test_number in args:
            try:

                # Get the serial number
                serial_number = self.tests[test_number]['JSON']['properties']['SERIAL_NUMBER']

                # If it looks like a real serial number, we can probe the database directly
                if self.__checkSerialNumber(serial_number):

                    # Fetch the component and update the component code and institution
                    component = ITkPDSession.doSomething(action = 'getComponent', method = 'GET', data = {'component': serial_number})
                    self.tests[test_number]['JSON'].update({'component': component['code'], 'institution': component['institution']['code']})

                    # If it has a local object name, include that in properties
                    for property in component['properties']:
                        if (property['code'] == 'LOCALNAME') or (property['code'] == 'LOCAL_NAME'):
                            self.tests[test_number]['JSON']['properties']['LOCAL_OBJECT_NAME'] = property['value']
                    if 'LOCAL_OBJECT_NAME' not in self.tests[test_number]['JSON']['properties'].keys():
                        self.tests[test_number]['JSON']['properties']['LOCAL_OBJECT_NAME'] = None

                # Else -- if it is not a valid serial number
                else:

                    # We'll filter the database contents by the local name and RFID, hoping that the serial number actually points to one of those
                    property_filter = [{'code': 'LOCALNAME', 'operator': '=', 'value': serial_number}, {'code': 'LOCAL_NAME', 'operator': '=', 'value': serial_number},
                                        {'code': 'RFID', 'operator': '=', 'value': serial_number}]

                    # Get a list of components with our filter
                    component_list = ITkPDSession.doSomething(action = 'listComponentsByProperty', method = 'POST', data = {'project': 'S', 'componentType': 'HYBRID', 'propertyFilter': property_filter})

                    # Assert that the list be of length 1, or else we did not find the proper component (e.g., maybe local name is not unique?)
                    if len(component_list) == 1:

                        component = component_list[0]

                        # Update JSON with the component code, real serial number, institution, and local name
                        self.tests[test_number]['JSON'].update({'component': component['code'], 'institution': component['institution']['code']})
                        if component['serialNumber'] == None:
                            self.tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] = None
                        else:
                            self.tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] = component['serialNumber']
                        for property in component['properties']:
                            if (property['code'] == 'LOCALNAME') or (property['code'] == 'LOCAL_NAME'):
                                self.tests[test_number]['JSON']['properties']['LOCAL_OBJECT_NAME'] = property['value']
                        if 'LOCAL_OBJECT_NAME' not in self.tests[test_number]['JSON']['properties'].keys():
                            self.tests[test_number]['JSON']['properties']['LOCAL_OBJECT_NAME'] = None

                    else:
                        WARNING('Component could not be identified using the serial number in the results file -- skipping.')
                        raise Skip

            except (IndexError, TypeError):
                pass

    # Define a pretty printing function to print all of the data associated with a test(s)
    def printTests(self, *args):
        if args == ():
            args = range(len(self.tests))
        for test_number in args:
            try:
                pp.pprint(self.tests[test_number])
            except (IndexError, TypeError):
                pass

    # Define a pretty printing function to print the JSON associated with a test(s)
    def printJSON(self, *args):
        if args == ():
            args = range(len(self.tests))
        for test_number in args:
            try:
                pp.pprint(self.tests[test_number]['JSON'])
            except (IndexError, TypeError):
                pass

    # Upload the JSON associated with a test(s)
    def uploadTests(self, ITkPDSession, *args):
        if args == ():
            args = range(len(self.tests))
        for test_number in args:
            try:
                ITkPDSession.doSomething(action = 'uploadTestRunResults', method = 'POST', data = self.tests[test_number]['JSON'])
            except (IndexError, TypeError):
                pass

    def __uploadFile(self, ITkPDSession, test_number, path_type):
        try:
            fields = {  'data': (os.path.basename(self.tests[test_number]['files_to_upload'][path_type]), open(self.tests[test_number]['files_to_upload'][path_type], 'rb')),
                        'type': 'file',
                        'component': self.tests[test_number]['JSON']['component'],
                        'title': os.path.basename(self.tests[test_number]['files_to_upload'][path_type])}
            if path_type == 'strobe_delay_path':
                fields['description'] = ' ITSDAQ strobe delay scan PDF file.'
            elif path_type == 'det_path':
                fields['description'] = 'ITSDAQ hybrid config file.'
            elif path_type == 'three_point_gain_path':
                fields['description'] = 'ITSDAQ three point gain scan PDF file.'
            elif path_type == 'response_curve_path':
                fields['description'] = 'ITSDAQ response curve PDF file.'
            elif path_type == 'trim_path':
                fields['description'] = 'ITSDAQ trim range scan trim file.'
            elif path_type == 'mask_path':
                fields['description'] = 'ITSDAQ trim range scan mask file.'
            elif path_type == 'NO_path':
                fields['description'] = 'ITSDAQ noise occupancy scan PDF file.'
            data = MultipartEncoder(fields = fields)
            ITkPDSession.doSomething(action = 'createComponentAttachment', method = 'POST', data = data)
        except KeyError:
            WARNING('File specified by path \'%s\' could not be found for run number %s (%s) -- skipping.' % (path_type, self.tests[test_number]['JSON']['runNumber'], self.tests[test_number]['JSON']['testType']))

    def uploadFiles(self, ITkPDSession, *args):
        if args == ():
            args = range(len(self.tests))
        for test_number in args:
            try:
                if self.tests[test_number]['JSON']['testType'] == 'STROBE_DELAY':
                    self.__uploadFile(ITkPDSession, test_number, 'strobe_delay_path')
                    self.__uploadFile(ITkPDSession, test_number, 'det_path')
                elif self.tests[test_number]['JSON']['testType'] == 'THREE_POINT_GAIN':
                    self.__uploadFile(ITkPDSession, test_number, 'three_point_gain_path')
                elif self.tests[test_number]['JSON']['testType'] == 'RESPONSE_CURVE':
                    self.__uploadFile(ITkPDSession, test_number, 'response_curve_path')
                elif self.tests[test_number]['JSON']['testType'] == 'TRIM_RANGE':
                    self.__uploadFile(ITkPDSession, test_number, 'trim_path')
                    self.__uploadFile(ITkPDSession, test_number, 'mask_path')
                elif self.tests[test_number]['JSON']['testType'] == 'NOISE_OCCUPANCY':
                    self.__uploadFile(ITkPDSession, test_number, 'NO_path')
            except (IndexError, TypeError):
                pass

# Define our ResultsDirectory object
class ResultsDirectory(object):

    # Define our init function and initialize filepaths and files
    def __init__(self, dirpath, pspath = None, configpath = None):
        self.dirpath = os.path.abspath(dirpath) +'/'
        if pspath != None:
            self.pspath = os.path.abspath(pspath) + '/'
        else:
            self.pspath = None
        if configpath != None:
            self.configpath = os.path.abspath(configpath) + '/'
        else:
            self.configpath = None
        self.filepaths = []
        self.files = []

    # Return a list of the full filepaths of all files (subdirectories) in self.dirpath
    def __returnAllFilepaths(self):
        return [os.path.join(self.dirpath, file) for file in os.listdir(self.dirpath)]

    # Filter the full filepath list to only include .txt files
    # This is because ITSDAQ results summary files are suffixed by .txt
    def getResultsSummaryFilepaths(self):
        self.filepaths = sorted(list(filter(lambda filepath: filepath[-4:] == '.txt' and 'st_diagnostics_' not in filepath and '_RC_' not in filepath, self.__returnAllFilepaths())), key = str.lower)

    # Print a summary table of the files found in hte results directory
    def printSummary(self):
        row_format = '{:<10}{:}'
        header = ['Index', 'Filename']
        print(row_format.format(*header))
        print(150 * '-')
        for i, filepath in enumerate(self.filepaths):
            print(row_format.format(str(i), os.path.basename(filepath)))

    # Define a function for accessing dirname without specifically targeting the member variable
    def returnDirpath(self):
        return self.dirpath

    # Define a function for accessing filepaths without specifically targeting the member variable
    def returnFilepaths(self, *args):
        if args == ():
            return self.filepaths
        filepaths = []
        for filepath_number in args:
            try:
                filepaths.append(self.filepaths[filepath_number])
            except (IndexError, TypeError):
                pass
        return filepaths[0] if len(filepaths) == 1 else filepaths

    # Return the length of filepaths
    def returnLengthFilepaths(self):
        return len(self.filepaths)

    # Define a function for accessing files without specifically targeting the member variable
    def returnFiles(self, *args):
        if args == ():
            return self.files
        files = []
        for file_number in args:
            try:
                files.append(self.files[file_number])
            except (IndexError, TypeError):
                pass
        return files[0] if len(files) == 1 else files

    # Return the length of files
    def returnLengthFiles(self):
        return len(self.files)

    # Open a results summary file(s) (i.e., add it to files)
    def openResultsSummaryFiles(self, *args):
        if args == ():
            args = range(len(self.filepaths))
        for file_number in args:
            try:
                self.files.append(ResultsSummaryFile(self.filepaths[file_number], self.pspath, self.configpath))
            except (IndexError, TypeError):
                pass

    # Return a results summary file(s)
    def returnResultsSummaryFiles(self, *args):
        if args == ():
            args = range(len(self.files))
        files = []
        for file_number in args:
            try:
                files.append(self.files[file_number])
            except (IndexError, TypeError):
                pass
        return files

    # Close a results summary files (i.e., delete it from files)
    def closeResultsSummaryFiles(self, *args):
        if args == ():
            args = range(len(self.files))
        for file_number in args:
            try:
                del self.files[file_number]
            except (IndexError, TypeError):
                pass
