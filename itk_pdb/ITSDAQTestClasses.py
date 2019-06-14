#!/usr/bin/env python
# ITSDAQTestClasses.py -- (updated!) classes relevant for representing ITSDAQ results summary files
# Created: 2019/01/17, Updated: 2019/03/11
# Written by Matthew Basso

import os, re
from itk_pdb.databaseUtilities import INFO, WARNING, Colours
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)
from requests_toolbelt.multipart.encoder import MultipartEncoder

# ComponentNotFound := component could not be identified in the ITkPD
class ComponentNotFound(Exception):
    pass

# Define our ResultsFile object
class ResultsFile(object):

    def __init__(self, results_file_path, enable_printing = True):
        self.results_file_path = results_file_path
        self.tests = []
        self.full_test = {'state': False, 'lower_index': None, 'upper_index': None}
        self.iter_index = 0
        self.enable_printing = enable_printing

    def reset(self, results_file_path, enable_printing = True):
        self.results_file_path = results_file_path
        self.tests = []
        self.full_test = {'state': False, 'lower_index': None, 'upper_index': None}
        self.iter_index = 0
        self.enable_printing = enable_printing

    # Return a selected test from self.tests as a dictionary (called as ResultsFile()[test_number])
    def __getitem__(self, test_number):
        return self.tests[test_number]

    # Return the length self.tests (called as len(ResultsFile()))
    def __len__(self):
        return len(self.tests)

    # Return the filepath for the results file
    def __str__(self):
        return self.results_file_path

    # Define our iterator, returning a test's JSON at each step
    def __iter__(self):
        self.iter_index = 0
        return self

    # Define the function for incrementing our iterator
    def __next__(self):
        if self.iter_index <= (len(self.tests) - 1):
            test = self.tests[self.iter_index]
            self.iter_index += 1
            return test
        else:
            raise StopIteration

    # Python 2 iterator fix, see: https://stackoverflow.com/questions/29578469/how-to-make-an-object-both-a-python2-and-python3-iterator
    next = __next__
        
    # Return every line in results file
    def __getLines(self):
        with open(self.results_file_path, 'r') as file:
            lines = file.readlines()
        return lines

    # Parse lines in order to identify all of the tests performed, returned as a list of dictionaries
    ######################################################################################################################
    # NOTE: the following function is heavily hardcoded and relies on the patterns present in most results summary files #
    # As a result, it is important to check that the output of the function appears to make sense                        #
    ######################################################################################################################
    def getTests(self, debug = False):

        # Get our lines
        lines = self.__getLines()

        # Initialize our list of tests and test_number (= number of tests found in the provided lines)
        tests = []
        test_number = 0

        # DEBUG
        if debug:
            print('ResultsFile.getTests() -- DEBUG : looking in file: %s' % self.results_file_path)

        # Read every line
        for i, line in enumerate(lines):

            # DEBUG
            if debug:
                print('ResultsFile.getTests() -- DEBUG : looking at line: %s' % i)

            # Throw away the line if the first character is not %
            if line[0] == '%':

                ######################
                # Parse general info #
                ######################
                if '%NewTest' in line:

                    # NOTE: check for the peculiar cases where we have a %NewTest but no results associated with it
                    # i.e., test_number does not get incremented, in which case we should purge the results
                    if len(tests) != test_number:
                        if tests[test_number]['JSON']['results'] == {}:
                            if debug:
                                print('ResultsFile.getTests() -- DEBUG : previous NewTest yielded empty test[\'JSON\'][\'results\'] -- PURGING!')
                            del tests[test_number]

                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding NewTest at line: %s' % i)
                    tests.append({'JSON': {'properties': {}, 'results': {}}, 'extra_data': {'NewTest_EXTRA': {}, 'DAQ_INFO_EXTRA': {}, 'DCS_INFO': {}, 'SCAN_INFO': {},
                                    'identifiers': {}}, 'files_to_upload': {}, 'files_to_upload_FULL': {}})

                    # Read serial number, user, location, run number, date, passed, and problem
                    # Properties which are needed for the JSON input to the database are thrown in extra_data
                    tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] = lines[i+2][17:-1]
                    tests[test_number]['JSON'].update({
                        'runNumber':        lines[i+5][17:-1],
                        'date':             lines[i+6][17:-1].replace('/', '.'),
                        'passed':           True if lines[i+7][17:-1] == 'YES' else (False if lines[i+7][17:-1] == 'NO' else None),
                        'problems':         True if lines[i+8][17:-1] == 'YES' else (False if lines[i+8][17:-1] == 'NO' else None)
                    })
                    tests[test_number]['extra_data']['NewTest_EXTRA'].update({
                        'user':             lines[i+3][17:-1],
                        'location':         lines[i+4][17:-1]
                    })

                ############################
                # Parse DAQ info all tests #
                ############################
                elif '%DAQ_INFO' in line:
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding DAQ_INFO at line: %s' % i)

                    # Read host, version, DUT, and time
                    tests[test_number]['JSON']['properties'].update({
                        'ITSDAQ_VERSION':   lines[i+5][1:-2],
                        'TIME':             lines[i+9][1:-2]
                    })
                    tests[test_number]['extra_data']['DAQ_INFO_EXTRA'].update({
                        'host':             lines[i+3][1:-2],
                        'DUT':              lines[i+7][1:-2]
                    })
                
                ##################
                # Parse DCS info #
                ##################
                elif '%DCS_INFO' in line:
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding DCS_INFO at line: %s' % i)

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

                ##################################################################
                # Parse scan info (only for 3PG, response curve, and trim range) #
                ##################################################################
                elif '%SCAN_INFO' in line:
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding SCAN_INFO at line: %s' % i)

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

                ###################################
                # Parse StrobeDelay specific info #
                ###################################
                elif '%StrobeDelay' in line:
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding StrobeDelay at line: %s' % i)

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

                    # Include the filename(s) to be uploaded
                    tests[test_number]['files_to_upload']['strobe_delay_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_StrobeDelayPlot_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                    tests[test_number]['files_to_upload']['det_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '.det'

                    # Increment test_number
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : the following test (test_number = %s) has been parsed:' % test_number)
                        print('')
                        pp.pprint(tests[test_number])
                        print('')
                    test_number += 1

                ######################################
                # Parse ThreePointGain specific info #
                ######################################
                elif '%ThreePointGain' in line:
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding ThreePointGain at line: %s' % i)

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
                    number_of_chips = int((j - j_loopA_identifier) / 4)

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

                    # Update results, identifiers, filename(s), and increment test_number
                    tests[test_number]['JSON']['results'] = results
                    tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_chips], 'stream1': identifiers[number_of_chips:]})
                    tests[test_number]['files_to_upload']['three_point_gain_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_RCPlot_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : the following test (test_number = %s) has been parsed:' % test_number)
                        print('')
                        pp.pprint(tests[test_number])
                        print('')
                    test_number += 1

                #####################################
                # Parse ResponseCurve specific info #
                #####################################
                elif '%ResponseCurve' in line:

                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding ResponseCurve at line: %s' % i)

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
                    number_of_chips = int((j - j_loopA_identifier) / 4)

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

                    # Update results, identifiers, filename(s), and increment test_number
                    tests[test_number]['JSON']['results'] = results
                    tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_chips], 'stream1': identifiers[number_of_chips:]})
                    tests[test_number]['files_to_upload']['response_curve_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_RCPlot_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : the following test (test_number = %s) has been parsed:' % test_number)
                        print('')
                        pp.pprint(tests[test_number])
                        print('')
                    test_number += 1

                ############################
                # Parse Trim specific info #
                ############################
                elif '%Trim' in line:

                    # We only want the last trim range scan of a given set (type = -1)
                    trim_type = int(lines[i+3].split()[1])
                    if trim_type == -1:

                        if debug:
                            print('ResultsFile.getTests() -- DEBUG : adding Trim at line: %s' % i)

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
                        number_of_channels = int((j - j_identifier) / 4)

                        # Iterate over the number of channels
                        for ii in range(number_of_channels):

                            # Sort through the elements of data and append them appropriately to results
                            results['STREAM0_RANGE'].append(int(data[ii][0]))
                            results['STREAM0_TARGET'].append(float(data[ii][1]))
                            results['STREAM1_RANGE'].append(int(data[ii+number_of_channels][0]))
                            results['STREAM1_TARGET'].append(float(data[ii+number_of_channels][1]))

                        # Update results, identifiers, filename(s), and increment test_number
                        tests[test_number]['JSON']['results'] = results
                        tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_channels], 'stream1': identifiers[number_of_channels:]})
                        tests[test_number]['files_to_upload']['trim_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_tr-1_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '.trim'
                        tests[test_number]['files_to_upload']['mask_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_tr-1_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '.mask'                           
                        if debug:
                            print('ResultsFile.getTests() -- DEBUG : the following test (test_number = %s) has been parsed:' % test_number)
                            print('')
                            pp.pprint(tests[test_number])
                            print('')
                        test_number += 1

                    # If it's not the type = -1 trim range test, we want to delete it from tests
                    else:
                        del tests[test_number]

                #######################################
                # Parse noise occupancy specific info #
                #######################################
                elif '%NO' in line:
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : adding NO at line: %s' % i)

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
                    number_of_chips = int(len(data) / 2)

                    # Update results and identifiers and increment test_number
                    tests[test_number]['JSON']['results'].update({'STREAM0_ESTENC':   data[:number_of_chips], 'STREAM1_ESTENC':   data[number_of_chips:]})
                    tests[test_number]['extra_data']['identifiers'].update({'stream0': identifiers[:number_of_chips], 'stream1': identifiers[number_of_chips:]})
                    tests[test_number]['files_to_upload']['no_filename'] = tests[test_number]['JSON']['properties']['SERIAL_NUMBER'] + '_NoScurve_' + ''.join(tests[test_number]['JSON']['date'].split('.')[::-1]) + '_' + ''.join(tests[test_number]['JSON']['properties']['TIME'].split(':')) + '.pdf'
                    if debug:
                        print('ResultsFile.getTests() -- DEBUG : the following test (test_number = %s) has been parsed:' % test_number)
                        print('')
                        pp.pprint(tests[test_number])
                        print('')
                    test_number += 1

        # DEBUG
        if debug:
            print('ResultsFile.getTests() -- DEBUG : %s tests found.' % len(tests))
            print('ResultsFile.getTests() -- DEBUG : the following tests have been parsed:')
            print('')
            pp.pprint(tests)
            print('')

        # Check to see if a fullTest is present
        if len(tests) >= 7:
            for i in range(len(tests) - 6):
                if (tests[i]['JSON']['runNumber'].split('-')[0] == tests[i+6]['JSON']['runNumber'].split('-')[0]) and ((int(tests[i+6]['JSON']['runNumber'].split('-')[1]) - int(tests[i]['JSON']['runNumber'].split('-')[1])) == 41):
                    self.full_test.update({'state': True, 'lower_index': i, 'upper_index': i+6})

        # Update self.tests
        self.tests = tests

        # Explicitly delete lines (?)
        del lines

        # DEBUG
        if debug:
            print('ResultsFile.getTests() -- DEBUG : file scanned successfully!')

    # Check if the serial number for a component is a valid ATLAS ITk serial number
    # See: https://indico.cern.ch/event/718637/contributions/2963483/attachments/1634097/2607226/serial_numbers_testbeam2.pdf
    def __checkSerialNumber(self, serial_number):
        XX = ['SB', 'SE', 'SG', 'PB', 'PE', 'PG']
        YY = ['HX', 'HY', 'H0', 'H1', 'H2', 'H3', 'H4', 'H5', 'ML', 'MS', 'M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'AB', 'AH', 'AA', 'AM', '00']
        if ((serial_number[0:3] == '20U') and (len(serial_number) == 14) and (serial_number[3:5] in XX) and (serial_number[5:7] in YY)
            and (serial_number[7] in ['0', '1', '2', '3']) and (serial_number[8] in ['0', '1', '2']) and serial_number[9:].isdigit()):
            return True
        else:
            return False

    # Add the component codes, local object names, and institutions to the JSON for each test
    # Also validate the serial number and, if necessary, replace it
    # We also add the full filepaths for the files which will be uploaded to the ITkPD
    def finalizeTest(self, test_number, ITkPDSession, upload_files = False, ResultsFolder = None, depth = 0, full_test = False):

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
            property_filter = [ {'code': 'LOCALNAME', 'operator': '=', 'value': serial_number},
                                {'code': 'LOCAL_NAME', 'operator': '=', 'value': serial_number},
                                {'code': 'RFID', 'operator': '=', 'value': serial_number}   ]

            # Get a list of components with our filter
            component_list = ITkPDSession.doSomething(action = 'listComponentsByProperty', method = 'POST',
                                                        data = {'project': 'S', 'componentType': 'HYBRID', 'propertyFilter': property_filter})

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
                if self.enable_printing:
                    WARNING('Component \'%s\' could not be identified using the serial number in the results file -- skipping.' % self.tests[test_number]['JSON']['properties']['SERIAL_NUMBER'])
                raise ComponentNotFound

        # Now find the files which need to be uploaded alongside our data (if the upload_files is specified)
        if upload_files:

            ############################################################
            ########## 2019/03/11 -- DISABLE FULLTEST FOR NOW ##########
            ############################################################
            full_test = False                                          #
            ############################################################

            # If it's a FullTest, we know what files we already want
            if full_test and self.full_test['state']:

                # If it's a FullTest, we know what test numbers correspond to tests where we would like to keep files
                lower_index = self.full_test['lower_index']

                # We want the .det config file
                if test_number - lower_index == 0:
                    self.tests[test_number]['files_to_upload_FULL']['det_filename'] = ResultsFolder.findFile(filename = self.tests[test_number]['files_to_upload']['det_filename'], folder = 'config', depth = depth)
                    # del self.tests[test_number]['files_to_upload']['strobe_delay_filename']
                
                # We want the .trim/.mask files
                elif test_number - lower_index == 2:
                    self.tests[test_number]['files_to_upload_FULL']['trim_filename'] = ResultsFolder.findFile(filename = self.tests[test_number]['files_to_upload']['trim_filename'], folder = 'results', depth = depth)
                    self.tests[test_number]['files_to_upload_FULL']['mask_filename'] = ResultsFolder.findFile(filename = self.tests[test_number]['files_to_upload']['mask_filename'], folder = 'results', depth = depth)
                
                # We want the post-trim response curve .pdf output file
                elif test_number - lower_index == 4:
                    self.tests[test_number]['files_to_upload_FULL']['response_curve_filename'] = ResultsFolder.findFile(filename = self.tests[test_number]['files_to_upload']['response_curve_filename'], folder = 'ps', depth = depth)
                
                # Everything else can be deleted
                else:
                    pass
                    # self.tests[test_number]['files_to_upload'] = {}

            # If it's not a FullTest, we'll assume we want to keep everything
            else:
                for filetype in self.tests[test_number]['files_to_upload'].keys():
                    if filetype in ['det_filename']:
                        folder = 'config'
                    elif filetype in ['trim_filename', 'mask_filename']:
                        folder = 'results'
                    elif filetype in ['strobe_delay_filename', 'three_point_gain_filename', 'response_curve_filename', 'no_filename']:
                        folder = 'ps'
                    self.tests[test_number]['files_to_upload_FULL'][filetype] = ResultsFolder.findFile(filename = self.tests[test_number]['files_to_upload'][filetype], folder = folder, depth = depth)

    # Print a table of the tests found in the results file and their associated indices
    def printSummaryOfTests(self):
        if self.enable_printing:
            row_format = '{:<10}{:<25}' + 6 * '{:<20}'
            header = ['Index', 'Serial number', 'Test type', 'Date', 'Time', 'Run number', 'Passed', 'Problems']
            print(row_format.format(*header))
            print(150 * '-')
            for i, test in enumerate(self.tests):
                row = [str(i), test['JSON']['properties']['SERIAL_NUMBER'], test['JSON']['testType'], test['JSON']['date'], test['JSON']['properties']['TIME'],
                        test['JSON']['runNumber'], 'YES' if test['JSON']['passed'] == True else 'NO', 'YES' if test['JSON']['problems'] == True else 'NO']
                print(row_format.format(*row))

    # Print the JSON associated with a test
    def printJSON(self, test_number):
        if self.enable_printing:
            pp.pprint(self.tests[test_number]['JSON'])

    # Print the entire dictionary associated with a test
    def printTest(self, test_number):
        if self.enable_printing:
            pp.pprint(self.tests[test_number])

    # Upload the JSON associated with a test
    def uploadJSON(self, test_number, ITkPDSession):
        ITkPDSession.doSomething(action = 'uploadTestRunResults', method = 'POST', data = self.tests[test_number]['JSON'])
        if self.enable_printing:
            INFO(Colours.BOLD + Colours.GREEN + 'Successfully' + Colours.ENDC + ' uploaded JSON for run number \'' + self.tests[test_number]['JSON']['runNumber'] + '\'.')
        return True

    # Upload the files associated with a test
    # upload_files := enable/disable uploading files
    # filestypes := only upload these filetypes (if not None)
    def uploadFiles(self, test_number, ITkPDSession, upload_files = False, filetypes = None):
        if upload_files:
            status = True
            if filetypes is None:
                files_to_upload = self.tests[test_number]['files_to_upload_FULL']
            else:
                files_to_upload = {key: self.tests[test_number]['files_to_upload_FULL'][key] for key in filetypes}
            run_number = self.tests[test_number]['JSON']['runNumber']
            date = self.tests[test_number]['JSON']['date']
            for filetype in files_to_upload.keys():
                if files_to_upload[filetype] != None:
                    if filetype == 'det_filename':
                        description = 'ITSDAQ config file.'
                    elif filetype == 'strobe_delay_filename':
                        description = 'ITSDAQ strobe delay scan PDF file, run number %s. Obtained on %s.' % (run_number, date)
                    elif filetype == 'three_point_gain_filename':
                        description = 'ITSDAQ 3PG scan PDF file, run number %s. Obtained on %s.' % (run_number, date)
                    elif filetype == 'response_curve_filename':
                        description = 'ITSDAQ response curve scan PDF file, run number %s. Obtained on %s.' % (run_number, date)
                    elif filetype == 'trim_filename':
                        description = 'ITSDAQ trim file, run number %s. Obtained on %s.' % (run_number, date)
                    elif filetype == 'mask_filename':
                        description = 'ITSDAQ mask file, run number %s. Obtained on %s.' % (run_number, date)
                    elif filetype == 'no_filename':
                        description = 'ITSDAQ noise occupancy scan PDF file, run number %s. Obtained on %s.' % (run_number, date)
                    fields = {  'data': (os.path.basename(files_to_upload[filetype]), open(files_to_upload[filetype], 'rb')),
                                'type': 'file',
                                'component': self.tests[test_number]['JSON']['component'],
                                'title': os.path.basename(files_to_upload[filetype]),
                                'description': description  }
                    data = MultipartEncoder(fields = fields)
                    ITkPDSession.doSomething(action = 'createComponentAttachment', method = 'POST', data = data)
                    if self.enable_printing:
                        INFO(Colours.BOLD + Colours.GREEN + 'Successfully' + Colours.ENDC + ' uploaded file \'%s\' for run number \'%s\'.' % (files_to_upload[filetype], run_number))
                    status |= True
                else:
                    if self.enable_printing:
                        WARNING('File \'%s\' could not be found for run number \'%s\' -- skipping.' % (filetype, run_number))
                    status |= False
            return status
        else:
            return True

    # Filter the tests stored in the object, selecting only those with indices given by selected_test_indices
    def filterTests(self, selected_test_indices):
        self.tests = [self.tests[i] for i in range(len(self.tests)) if i in selected_test_indices]

# Define an object for representing the contents of our SCTVAR/results/ folder
class ResultsFolder(object):

    # Define our init
    # If ps/config_folder_path == None, then treat sctvar_folder_path as having the actual structure of SCTVAR (/results/, /ps/, /config/, etc.)
    # --> if False, then we assume sctvar_folder_path actually points to /results/ and the user will have to define BOTH the /ps/, /config/ paths
    # self.files := contains all or a subset of the results summary files in SCTVAR or equivalent
    # self.iter_index := index being considered for our iterator over the ResultsFile objects in self.files
    def __init__(self, sctvar_folder_path, ps_folder_path = None, config_folder_path = None, enable_printing = True):
        if ps_folder_path == None and config_folder_path == None:
            self.results_folder_path = os.path.dirname(sctvar_folder_path) + '/results'
            self.ps_folder_path = os.path.dirname(sctvar_folder_path) + '/ps'
            self.config_folder_path = os.path.dirname(sctvar_folder_path) + '/config'
        else:
            self.results_folder_path = os.path.dirname(sctvar_folder_path)
            self.ps_folder_path = os.path.dirname(ps_folder_path) if ps_folder_path != None else None
            self.config_folder_path = os.path.dirname(config_folder_path) if config_folder_path != None else None
        self.files = []
        self.iter_index = 0
        self.enable_printing = enable_printing

    def reset(self, sctvar_folder_path, ps_folder_path = None, config_folder_path = None, enable_printing = True):
        if ps_folder_path == None and config_folder_path == None:
            self.results_folder_path = os.path.dirname(sctvar_folder_path) + '/results'
            self.ps_folder_path = os.path.dirname(sctvar_folder_path) + '/ps'
            self.config_folder_path = os.path.dirname(sctvar_folder_path) + '/config'
        else:
            self.results_folder_path = os.path.dirname(sctvar_folder_path)
            self.ps_folder_path = os.path.dirname(ps_folder_path) if ps_folder_path != None else None
            self.config_folder_path = os.path.dirname(config_folder_path) if config_folder_path != None else None
        self.files = []
        self.iter_index = 0
        self.enable_printing = enable_printing

    # Return a selected file from self.files as a ResultsFile object (called as SctVarFolder()[file_number])
    def __getitem__(self, file_number):
        return ResultsFile(self.files[file_number], enable_printing = self.enable_printing)

    # Return the length self.files (called as len(SctvarFolder()))
    def __len__(self):
        return len(self.files)

    # Return the /results/ directory path
    def __str__(self):
        return self.results_folder_path

    # Define our iterator, returning a ResultsFile object at each step
    def __iter__(self):
        self.iter_index = 0
        return self

    # Define the function for incrementing our iterator
    def __next__(self):
        if self.iter_index <= (len(self.files) - 1):
            results_file = ResultsFile(self.files[self.iter_index], enable_printing = self.enable_printing)
            self.iter_index += 1
            return results_file
        else:
            raise StopIteration

    # Python 2 iterator fix, see: https://stackoverflow.com/questions/29578469/how-to-make-an-object-both-a-python2-and-python3-iterator
    next = __next__

    # Define a function for finding all of the results summary files in SCTVAR
    # depth := level of recursion in SCTVAR/results/ (0 := just search in /results/, 1 := one level deeper, etc.)
    # extension := file extension for results summary files
    # ignore_files := ignore filenames containing these strings which end with the above extension
    # ignore_folders := ignore the contents of these folders in /results/
    def getFiles(self, depth = 0):
        self.files = []
        extension = '.txt'
        ignore_files = ['st_diagnostics_', '_RC_']
        ignore_folders = ['IGNORE']
        for root, dirs, files in os.walk(self.results_folder_path):
            dirs = [d for d in dirs if d not in ignore_folders]
            if root[len(self.results_folder_path):].count(os.sep) < (depth + 1):
                files = sorted(list(filter(lambda file: os.path.splitext(file)[1] == extension and [flag for flag in ignore_files if flag in os.path.basename(os.path.splitext(file)[0])] == [], files)))
                self.files += [os.path.join(root, f) for f in files]

    # Print a table of the results files stored in the object and their associated indices
    def printSummaryOfFiles(self):
        if self.enable_printing:
            row_format = '{:<10}{:}'
            header = ['Index', 'Filename']
            print(row_format.format(*header))
            print(150 * '-')
            for i, file in enumerate(self.files):
                print(row_format.format(str(i), file))

    # Filter the results files stored in the object, selecting only those with indices given by selected_file_indices
    def filterFiles(self, selected_file_indices):
        self.files = [self.files[i] for i in range(len(self.files)) if i in selected_file_indices]

    # Filter files by applying a regex(es) to the filenames
    def filterFilesByRegex(self, regexes = []):
        if regexes != []:
            files_temp = []
            pass_file = True
            for file in self.files:
                for regex in regexes:
                    pass_file &= bool(re.search(r'' + regex, file, re.IGNORECASE))
                if pass_file:
                    files_temp.append(file)
                pass_file = True
            self.files = files_temp
        else:
            pass

    # Find a file available in the results folder file structure up to a certain depth
    def findFile(self, filename, folder, depth = 0):
        ignore_folders = ['IGNORE']
        regex = re.compile(r'^(?=.*' + r')(?=.*'.join(os.path.splitext(filename)[0][:-1].split('_')) + r').*$')
        if folder == 'results':
            folder = self.results_folder_path
        elif folder == 'ps':
            folder = self.ps_folder_path
        elif folder == 'config':
            folder = self.config_folder_path
        for root, dirs, files in os.walk(folder):
            dirs = [d for d in dirs if d not in ignore_folders]
            if root[len(folder):].count(os.sep) < (depth + 1):
                for file in files:
                    if filename == file:
                        return os.path.join(root, filename)
                    elif regex.search(file):
                        return os.path.join(root, file)
        return None
