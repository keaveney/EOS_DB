#!/usr/bin/env python
# uploadITSDAQTests.py -- an (updated!) interface for uploading tests from ITSDAQ results summary files to the ITk Production Database
# Created: 2019/01/17, Updated: 2019/03/22
# Written by Matthew Basso

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import argparse, os, sys, traceback
from itk_pdb.dbAccess import ITkPDSession
from itk_pdb.databaseUtilities import INFO, PROMPT, WARNING, ERROR, STATUS, Colours
from itk_pdb.ITSDAQTestClasses import ResultsFile, ResultsFolder, ComponentNotFound

# Fix the input (python3) versus raw_input (python2) issue
# See: https://stackoverflow.com/questions/954834/how-do-i-use-raw-input-in-python-3
try:
    input = raw_input
except NameError: 
    pass

# Define a function to get a list of indices from the user
# Note: a user can enter, e.g., 0 2-4 6 which would result in the list [0, 2, 3, 4, 6]
def getIndices(table_length):
    PROMPT('Enter a list of positive, space/comma-separated, integer indices from the table above, \'all\' to select all items, or \'none\' to select no items:')
    while True:
            response = input().strip()
            try:
                if response == '':
                    continue
                elif response == 'none':
                    INFO('No items were selected.')
                    return []
                elif response == 'all':
                    return list(range(table_length))
                else:
                    response_split = [item for sublist in response.split() for item in sublist.split(',') if item != '']
                    indices = [[int(index)] if '-' not in index else list(range(int(index.split('-')[0]), int(index.split('-')[1])+1)) for index in response_split]
                    indices = [index for sublist in indices for index in sublist if index < table_length and index >= 0]
                    return sorted(list(set(indices)))
            except ValueError:
                del response
                PROMPT('Invalid input. Please enter a list of positive, space/comma-separated integers, \'all\', or \'none\':')
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

# Define a function to get a 'yes', 'no', or 'json' answer from the user
def getYesNoOrJson(prompt):
    PROMPT(prompt)
    while True:
        response = input().strip().lower()
        if response == '':
            continue
        elif response in ['n', 'no', '0']:
            return False, False
        elif response in ['y', 'yes', '1']:
            return True, True
        elif response in ['j', 'json', '2']:
            return True, False
        else:
            del response
            PROMPT('Invalid input. Please enter \'y\', \'n\', or \'j\':')
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

        (sctvar_folder_path, get_confirm, upload_files, ps_folder_path, config_folder_path, recursion_depth) = (
            args.sctvar_folder_path, args.get_confirm, args.upload_files, args.ps_folder_path, args.config_folder_path, args.recursion_depth)

        INFO('Launching ITkPDSession.')
        session = ITkPDSession()
        session.authenticate()

        results_folder = ResultsFolder(sctvar_folder_path, ps_folder_path, config_folder_path)

        INFO('Looking in: ' + str(results_folder))
        results_folder.getFiles(depth = recursion_depth)
        if results_folder.files == []:
            WARNING('No files found!')
        else:
            INFO('The following files were found:\n')
            results_folder.printSummaryOfFiles()
            print('')
            indices = getIndices(len(results_folder))
            results_folder.filterFiles(indices)

            for results_file in results_folder:
                full_test = False
                INFO('Looking in: ' + str(results_file))
                results_file.getTests()
                if results_file.tests == []:
                    WARNING('No tests found -- skipping.')
                else:
                    INFO('The following tests were found:')
                    try:
                        print('')
                        results_file.printSummaryOfTests()
                    except KeyError:
                        print('')
                        ERROR('KeyError encountered during ResultsFile.printSummaryOfTests() -- printing Traceback:\n')
                        print(traceback.format_exc())
                        WARNING('Error encountered in file -- skipping.')
                        continue
                    print('')
                    if results_file.full_test['state'] == True:
                        lower_index = results_file.full_test['lower_index']
                        upper_index = results_file.full_test['upper_index']
                        INFO('Indices %s through %s appear to be part of a FullTest, would you like to only upload those results?' % (lower_index, upper_index))
                        INFO('Only the following files will be uploaded: <config>.det, <trim file>.trim, <mask file>.mask, and <post-trim response curve>.pdf.')
                        if getYesOrNo('Please enter \'y\' to confirm the FullTest or \'n\' to only upload specific results:'):
                            INFO('Only uploading results from the FullTest.')
                            indices = list(range(lower_index, upper_index+1))
                            full_test = True
                        else:
                            indices = getIndices(len(results_file))
                    else:
                        indices = getIndices(len(results_file))

                    for i in indices:
                        try:
                            results_file.finalizeTest(test_number = i, ITkPDSession = session, upload_files = upload_files, ResultsFolder = results_folder,
                                                        depth = recursion_depth, full_test = full_test)
                            if get_confirm:
                                INFO('Printing JSON for run number \'' + results_file[i]['JSON']['runNumber'] + '\':\n')
                                results_file.printJSON(i)
                                print('')
                                if upload_files:
                                    files_to_upload = results_file[i]['files_to_upload']
                                    if files_to_upload == {}:
                                        pass
                                    else:
                                        INFO('The following files will also be uploaded to component code \'' + results_file[i]['JSON']['component'] + '\':\n')
                                        files_to_upload = results_file[i]['files_to_upload']
                                        for filetype in files_to_upload.keys():
                                            if files_to_upload[filetype] == None:
                                                print('    {0} = {1}{2}Not found!{3}'.format(filetype, Colours.BOLD, Colours.WHITE, Colours.ENDC))
                                            else:
                                                print('    ' + filetype + ' = ' + files_to_upload[filetype])
                                        print('')
                                        confirm_upload, upload_these_files = getYesNoOrJson('Please enter \'y\' to confirm the upload, \'n\' to cancel, or \'j\' to upload only the JSON:')
                                        if not confirm_upload:
                                            INFO(Colours.BOLD + Colours.RED + 'Cancelled' + Colours.ENDC + ' upload of run number \'' + results_file[i]['JSON']['runNumber'] + '\'.')
                                            continue
                                else:
                                    upload_these_files = False
                                    if not getYesOrNo('Please enter \'y\' to confirm the upload or \'n\' to cancel:'):
                                        INFO(Colours.BOLD + Colours.RED + 'Cancelled' + Colours.ENDC + ' upload of run number \'' + results_file[i]['JSON']['runNumber'] + '\'.')
                                        continue
                            results_file.uploadJSON(i, session)
                            if upload_these_files:
                                results_file.uploadFiles(i, session, upload_files)
                        except ComponentNotFound:
                            continue

        STATUS('Finished successfully.', True)
        sys.exit(0)

    except KeyboardInterrupt:
        print('')
        ERROR('Exectution terminated.')
        STATUS('Finished with error.', False)
        sys.exit(1)

if __name__ == '__main__':

    # Define our parser
    parser = argparse.ArgumentParser(description = 'Upload ITSDAQ test results/files to the ITk Production Database', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser._action_groups.pop()

    # Define our required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument(dest = 'sctvar_folder_path', type = str, default = os.getenv('SCTDAQ_VAR', None), help = 'path to the SCTVAR (or results) directory')

    # Define our optional arguments
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-c', '--getConfirm', dest = 'get_confirm', action = 'store_true', help = 'print the contents of each test/file selected for upload and ask for a confirmation')
    optional.add_argument('-u', '--uploadFiles', dest = 'upload_files', action = 'store_true', help = 'upload the file(s) (e.g., .det, .trim, .mask, .pdf) associated with each test result')
    optional.add_argument('-P', '--psPath', dest = 'ps_folder_path', type = str, help = 'path to the ps directory (or equivalent) if an SCTVAR directory structure is not present')
    optional.add_argument('-C', '--cfgPath', dest = 'config_folder_path', type = str, help = 'path to the config directory (or equivalent) if an SCTVAR directory structure is not present')
    optional.add_argument('-R', '--recursionDepth', dest = 'recursion_depth', type = int, default = 0, help = 'depth for searching for files in results, ps, and config')

    # Fetch our args
    args = parser.parse_args()

    # Run main()
    main(args)
