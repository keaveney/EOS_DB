#!/usr/bin/env python
# uploadITSDAQTests_RETIRED.py -- an interface for uploading tests from ITSDAQ results summary files to the ITk Production Database
# Created: 2018/06/30, Updated: 2019/03/22
# Written by Matthew Basso

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import argparse, os, sys
from itk_pdb.dbAccess import ITkPDSession
from itk_pdb.databaseUtilities import INFO, PROMPT, WARNING, ERROR, STATUS, Colours
from itk_pdb.ITSDAQTestClasses_RETIRED import ResultsSummaryFile, ResultsDirectory, Skip

# Fix the input (python3) versus raw_input (python2) issue
# See: https://stackoverflow.com/questions/954834/how-do-i-use-raw-input-in-python-3
try:
    input = raw_input
except NameError: 
    pass

# Again, fix FileNotFoundError (python3) versus IOError (python2) issue
try:
    try:
        raise FileNotFoundError
    except FileNotFoundError:
        pass
except NameError:
    FileNotFoundError = IOError

# Define a function to get a list of indices from the user
# Note: a user can enter, e.g., 0 2-4 6 which would result in the list [0, 2, 3, 4, 6]
def getIndices(table_length):
    PROMPT('Enter a list of positive, space-separated, integer indices from the table above, \'all\' to select all items, or \'none\' to select no items:')
    while True:
            response = input().strip()
            try:
                if response == '':
                    continue
                elif response == 'none':
                    INFO('No items were seleted.')
                    return []
                elif response == 'all':
                    return list(range(table_length))
                else:
                    response_split = [item for sublist in response.strip().split() for item in sublist.split(',')]
                    indices = [[int(index)] if '-' not in index else list(range(int(index.split('-')[0]), int(index.split('-')[1])+1)) for index in response_split]
                    indices = [index for sublist in indices for index in sublist if index < table_length]
                    return sorted(list(set(indices)))
            except ValueError:
                del response
                PROMPT('Invalid input. Please enter a list of positive, space-separated integers, \'all\', or \'none\':')
                continue

# Define a function to get a 'yes' or 'no' answer from the user
def getYesOrNo(prompt):
    PROMPT(prompt)
    while True:
        response = input().strip().lower()
        if response == '':
            continue
        elif response in ['n', 'no', '0']:
            return False
        elif response in ['y', 'yes', '1']:
            return True
        else:
            del response
            PROMPT('Invalid input. Please enter \'y\', or \'n\':')
            continue

# Define our main function
def main(args):

    try:

        # Use the global definition of input
        global input

        print('')
        print('******************************************************************************')
        print('*                            {0}{1}uploadITSDAQTests.py{2}                            *'.format(Colours.WHITE, Colours.BOLD, Colours.ENDC))
        print('******************************************************************************')
        print('')

        # Rename our argument variables
        results_path, all_files, all_tests, get_confirm, ps_path, cfg_path, up_files = args.results_path, args.all_files, args.all_tests, args.get_confirm, args.ps_path, args.cfg_path, args.up_files
        if ps_path != None:
            ps_path = os.path.abspath(ps_path) + '/'
        elif up_files:
            ERROR('--psPath must not be None if uploading files.')
            STATUS('Finished with error.', False)
            sys.exit(1)
        if cfg_path !=None:
            cfg_path = os.path.abspath(cfg_path) + '/'
        elif up_files:
            ERROR('--cfgPath must not be None if uploading files.')
            STATUS('Finished with error.', False)
            sys.exit(1)
        if results_path != None:
            results_path = os.path.abspath(results_path) + '/' if os.path.isdir(results_path) else os.path.abspath(results_path)

        # Check if results_path/ps_path/cfg_path exists (and that ps_path/cfg_path are directories)
        if not os.path.exists(results_path):
            raise FileNotFoundError(results_path)
        if up_files:
            if not os.path.exists(ps_path):
                raise FileNotFoundError(ps_path)
            if not os.path.isdir(ps_path):
                ERROR('--psPath is not a directory: ' + ps_path)
                STATUS('Finished with error.', False)
                sys.exit(1)
            if not os.path.exists(cfg_path):
                raise FileNotFoundError(cfg_path)
            if not os.path.isdir(cfg_path):
                ERROR('--cfgPath is not a directory: ' + cfg_path)
                STATUS('Finished with error.', False)
                sys.exit(1)

        INFO('Using:')
        print('    results_path = %s' % results_path)
        print('    all_files    = %s' % all_files)
        print('    all_tests    = %s' % all_tests)
        print('    get_confirm  = %s' % get_confirm)
        print('    ps_path      = %s' % ps_path)
        print('    cfg_path     = %s' % cfg_path)
        print('    up_files     = %s' % up_files)
        INFO('Launching ITkPDSession.')

        session = ITkPDSession()
        session.authenticate()

        fullTest = False

        # Check if results_path points to a directory
        if os.path.isdir(results_path):

            # Open our results directory
            results_directory = ResultsDirectory(results_path, ps_path, cfg_path)
            results_directory.getResultsSummaryFilepaths()

            # Select everything if all_files
            if all_files:
                results_directory.openResultsSummaryFiles()
                summary_files = results_directory.returnResultsSummaryFiles()

            # State there is nothing if there is nothing
            elif results_directory.returnLengthFilepaths == 0:

                STATUS('Finished successfully.', True)
                sys.exit(0)
            
            # Else ask the user what they want to upload
            else:

                INFO('Looking in: ' + results_path)
                INFO('The following files were found:\n')
                results_directory.printSummary()
                print('')
                indices = getIndices(results_directory.returnLengthFilepaths())
                results_directory.openResultsSummaryFiles(*indices)
                summary_files = results_directory.returnResultsSummaryFiles()

        else:

            # Else if results_path points to a file, summary_files will contain only that file

            summary_files = [ResultsSummaryFile(results_path, ps_path, cfg_path)]

        # Iterate over all of our summary files
        for summary_file in summary_files:

            INFO('Looking in: ' + summary_file.returnFilepath())

            # Get our tests
            try:
                summary_file.getTests()
            except FileNotFoundError as path:
                WARNING('Filepath does not exist: {0} -- skipping'.format(path))
                continue

            # If all_tests, automatically select all tests
            if all_tests:
                indices = range(summary_file.returnLengthTests())

            # Else, print a summary table and ask the user to specify which tests
            else:

                tests = summary_file.returnTests()

                INFO('The following tests were found:\n')
                summary_file.printSummary()
                print('')

                if len(tests) >= 7:
                    for i, test in enumerate(tests):
                        if ((test['JSON']['runNumber'].split('-')[0] == tests[i+6]['JSON']['runNumber'].split('-')[0])
                            and ((int(tests[i+6]['JSON']['runNumber'].split('-')[1]) - int(test['JSON']['runNumber'].split('-')[1])) == 41)):
                            INFO('Run numbers {0} through {1} appear to be part of a FullTest, would you like to only upload those results?'.format(test['JSON']['runNumber'], tests[i+6]['JSON']['runNumber']))
                            INFO('Only the following files will be uploaded: <config>.det, <trim file>.trim, <mask file>.mask, and <post-trim response curve>.pdf.')
                            if getYesOrNo('Please enter \'y\' to confirm the FullTest or \'n\' to only upload specific results:'):
                                INFO('Only uploading results from the FullTest.')
                                indices = list(range(i, i+7))
                                fullTest = True
                                break
                            else:
                                indices = getIndices(summary_file.returnLengthTests())
                                break

                else:
                    indices = getIndices(summary_file.returnLengthTests())

            # For each selected test, finalize the JSON
            for length_index, i in enumerate(indices):

                # If finalizeJSON() raises a skip, the component cannot be identified and so cannot be uploaded
                # i.e., we want to just continue over that component (this would likely happen to every other component in the ResultsSummaryFile)
                try:
                    summary_file.finalizeJSON(session, i)
                except Skip:
                    continue

                # If get_confirm, print the JSON and ask the user 'y' or 'n'
                if get_confirm:
                    INFO('Printing JSON for run number: ' + summary_file.returnTests(i)['JSON']['runNumber'])
                    INFO('JSON:')
                    summary_file.printJSON(i)
                    if up_files:
                        if fullTest:
                            if length_index == 0:
                                del summary_file.tests[i]['files_to_upload']['strobe_delay_path']
                                INFO('The following file(s) will also be uploaded:')
                                try:
                                    print('    ' + summary_file.returnTests(i)['files_to_upload']['det_path'])
                                except KeyError:
                                    print('    <None found>')
                            elif length_index == 2:
                                INFO('The following file(s) will also be uploaded:')
                                try:
                                    print('    ' + summary_file.returnTests(i)['files_to_upload']['trim_path'])
                                    print('    ' + summary_file.returnTests(i)['files_to_upload']['mask_path'])
                                except KeyError:
                                    print('    <None found>')
                            elif length_index == 4:
                                INFO('The following file(s) will also be uploaded:')
                                try:
                                    print('    ' + summary_file.returnTests(i)['files_to_upload']['response_curve_path'])
                                except KeyError:
                                    print('    <None found>')
                        else:
                            INFO('The following file(s) will also be uploaded:')
                            if summary_file.returnTests(i)['files_to_upload'].keys() == []:
                                print('    <None found>')
                            else:
                                for file_key in summary_file.returnTests(i)['files_to_upload'].keys():
                                    print('    ' + summary_file.returnTests(i)['files_to_upload'][file_key])
                    if not getYesOrNo('Please enter \'y\' to confirm the upload or \'n\' to cancel:'):
                        INFO('Cancelled upload of run number: ' + summary_file.returnTests(i)['JSON']['runNumber'])
                        continue

                summary_file.uploadTests(session, i)
                if up_files:
                    summary_file.uploadFiles(session, i)
                INFO('Uploaded run number: ' + summary_file.returnTests(i)['JSON']['runNumber'])

        STATUS('Finished successfully.', True)
        sys.exit(0)

    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        STATUS('Finished with error.', False)
        sys.exit(1)

    except FileNotFoundError as e:
        ERROR('Path does not exist: {0}'.format(e))
        STATUS('Finished with error.', False)
        sys.exit(1)

if __name__ == '__main__':

    # Define our parser
    parser = argparse.ArgumentParser(description = 'Upload ITSDAQ test results to the ITk Production Database', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser._action_groups.pop()

    # Define our required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument(dest = 'results_path', type = str, help = 'path to the results file or directory')

    # Define our optional arguments
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-f', '--allFiles', dest = 'all_files', action = 'store_true', help = 'select all results files in the directory')
    optional.add_argument('-t', '--allTests', dest = 'all_tests', action = 'store_true', help = 'upload all tests in the selected results file(s)')  
    optional.add_argument('-c', '--getConfirm', dest = 'get_confirm', action = 'store_true', help = 'print the contents of each test selected for upload and ask for a confirmation')
    optional.add_argument('-P', '--psPath', dest = 'ps_path', type = str, help = 'path to the SCTVAR ps directory (i.e., .pdf file location for the tests)')
    optional.add_argument('-C', '--cfgPath', dest = 'cfg_path', type = str, help = 'path to the SCTVAR config directory (i.e., .det file location for the tests)')
    optional.add_argument('-u', '--upFiles', dest = 'up_files', action = 'store_true', help = 'upload the file(s) (e.g., .det, .trim, .mask, .pdf) associated with each test result')

    # Fetch our args
    args = parser.parse_args()

    # Run main()
    main(args)
