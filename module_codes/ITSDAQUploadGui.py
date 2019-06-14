#!/usr/bin/env python
# ITSDAQUploadGui.py -- a gui for uploading ITSDAQ test results to the ITk Production Database
# Created: 2019/02/28, Updated: 2019/03/22
# Written by Matthew Basso

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys, os
try:
    from PyQt5.QtWidgets import (QWidget, QMainWindow, QDesktopWidget, QLabel, QShortcut, QGridLayout, QPushButton, QLineEdit, QCheckBox, QSpinBox,
                                    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QStackedWidget, QTextEdit, QDialog)
    from PyQt5.QtGui import QIcon, QKeySequence, QColor, QFont
    from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
except ImportError:
    print('ERROR  : Python module \'PyQt5\' is not installed.')
    print('INFO   : To install, please type \'sudo apt-get install python-pyqt5\' for Python 2.')
    print('INFO   : For Python 3, type \'sudo apt-get install python3-pyqt5\'.')
    print('STATUS : Finished with error -- exitting!')
    sys.exit(1)
try:
    from requests.exceptions import RequestException
except ImportError:
    print('ERROR  : Python module \'requests\' is not installed.')
    print('INFO   : To install, please type \'sudo apt-get install python-requests\' for Python 2.')
    print('INFO   : For Python 3, type \'sudo apt-get install python3-requests\'.')
    print('STATUS : Finished with error -- exitting!')
    sys.exit(1)
from itk_pdb.ITkPDLoginGui import ITkPDLoginGui
from itk_pdb.ITSDAQTestClasses import ResultsFolder, ComponentNotFound
from itk_pdb.dbAccess import ExpiredToken
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)
from functools import wraps

def tip_decorate(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        args = list(args)
        args[1] = '<span style = \"background-color: black; color: white; font: normal; font-size: 12pt\">' + args[1] + '</span>'
        func(*args, **kwargs)
    return func_wrapper

QPushButton.setToolTip = tip_decorate(QPushButton.setToolTip)

#########################################
# ++++++++++++++ GLOBALS ++++++++++++++ #
#########################################
_DEBUG                 = False
_DEBUG_DEPTH           = 0
#########################################
# +++++++++++++++++++++++++++++++++++++ #
#########################################

def DEBUG(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if _DEBUG:
            global _DEBUG_DEPTH
            print(_DEBUG_DEPTH * ' ' + 'DEBUG : entering: %s.%s' % (args[0].__class__.__name__, func.__name__))
            _DEBUG_DEPTH += 1
            return_value = func(*args, **kwargs)
            _DEBUG_DEPTH -= 1
            print(_DEBUG_DEPTH * ' ' + 'DEBUG :  exiting: %s.%s' % (args[0].__class__.__name__, func.__name__))
            return return_value
        else:
            return func(*args, **kwargs)
    return func_wrapper

''' It would be really nice if I had a Globals class that the individual widgets could pass around so I don't need to manage passing around
    member variables utilized by all classes, mais c'est la vie '''

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## HEADER WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ITSDAQUploadGui__Header(QWidget):

    @DEBUG
    def __init__(self, parent = None):
        super(ITSDAQUploadGui__Header, self).__init__(parent)
        self.parent = parent
        self.layout = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __quit(self):
        sys.exit(0)

    @DEBUG
    def __initUI(self):

        title = QLabel('ATLAS ITk Production Database -- ITSDAQ Test Upload GUI', self)
        title.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignLeft;')
        quit = QPushButton('Quit', self)
        quit.clicked.connect(lambda: self.__quit())
        quit.setAutoDefault(True)
        quit.setToolTip('Quit the GUI')
        quit.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        self.layout.addWidget(title,    0, 0, 1, 7)
        self.layout.addWidget(quit,     0, 7, 1, 1)

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## STEP 1 WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ITSDAQUploadGui__Step1(QWidget):

    @DEBUG
    def __init__(self, parent = None):
        super(ITSDAQUploadGui__Step1, self).__init__(parent)
        self.parent     = parent
        self.layout     = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __setDefaults(self):
        self.sctvar_folder_path = ''
        self.ps_folder_path     = ''
        self.config_folder_path = ''
        self.get_confirm        = True
        self.upload_files       = True
        self.recursion_depth    = 0
        self.regexes            = ''
        self.ResultsFolder      = None

    @DEBUG
    def __exploreForDirectory(self, caption = 'Explore', directory = '.'):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        path = QFileDialog.getExistingDirectory(parent = self, caption = caption, directory = directory, options = options)
        return path

    @DEBUG
    def __setDirectory(self, member_QLineEdit, caption = 'Explore', directory = '.'):
        if member_QLineEdit.text() == '':
            pass
        else:
            directory = member_QLineEdit.text()
        path = self.__exploreForDirectory(caption, directory)
        if path == '':
            pass
        else:
            member_QLineEdit.setText(path + '/')

    @DEBUG
    def __getResultsFolder(self):
        # Have to convert '' to None for instantiating ResultsFolder
        if self.ps_folder_path == '':
            ps_folder_path = None
        else:
            ps_folder_path = self.ps_folder_path
        if self.config_folder_path == '':
            config_folder_path = None
        else:
            config_folder_path = self.config_folder_path
        if self.ResultsFolder is None:
            self.ResultsFolder = ResultsFolder(self.sctvar_folder_path, ps_folder_path, config_folder_path, enable_printing = False)
        else:
            self.ResultsFolder.reset(self.sctvar_folder_path, ps_folder_path, config_folder_path, enable_printing = False)
        self.ResultsFolder.getFiles(depth = self.recursion_depth)
        self.ResultsFolder.filterFilesByRegex(regexes = self.regexes)

    @DEBUG
    def __confirm(self):
        if self.input__sctvar_folder_path.text() == '':
            QMessageBox.warning(self, 'Error', '/$(SCTDAQ_VAR)/ is not specified (None)')
            return
        if os.path.exists(self.input__sctvar_folder_path.text()):
            self.sctvar_folder_path = self.input__sctvar_folder_path.text()
        else:
            QMessageBox.warning(self, 'Error', '/$(SCTDAQ_VAR)/ path does not exist: %s' % self.input__sctvar_folder_path.text())
            return
        if self.input__ps_folder_path.text() != '':
            if os.path.exists(self.input__ps_folder_path.text()):
                self.ps_folder_path = self.input__ps_folder_path.text()
            else:
                QMessageBox.warning(self, 'Error', '/$(SCTDAQ_VAR)/ps/ path does not exist: %s' % self.input__ps_folder_path.text())
                return
        if self.input__config_folder_path.text() != '':
            if os.path.exists(self.input__config_folder_path.text()):
                self.config_folder_path = self.input__config_folder_path.text()
            else:
                QMessageBox.warning(self, 'Error', '/$(SCTDAQ_VAR)/config/ path does not exist: %s' % self.input__config_folder_path.text())
                return
        self.recursion_depth    = int(self.input__recursion_depth.text())
        self.get_confirm        = self.input__get_confirm.isChecked()
        self.upload_files       = self.input__upload_files.isChecked()
        self.regexes            = [(r'' + regex) for sublist in self.input__regexes.text().split() for regex in sublist.split(',') if regex != '']
        self.__getResultsFolder()
        self.signal_done.emit()

    @DEBUG
    def __initUI(self):
    
        title = QLabel('Step #1: Inform the program of the location of ITSDAQ results files and then click \"Confirm\".')
        title.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        label__sctvar_folder_path = QLabel('Enter the /$(SCTDAQ_VAR)/(results/) path:')
        label__sctvar_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        self.input__sctvar_folder_path = QLineEdit(self)
        self.input__sctvar_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        explore__sctvar_folder_path = QPushButton('Explore', self)
        explore__sctvar_folder_path.clicked.connect(lambda: self.__setDirectory(self.input__sctvar_folder_path, 'Explore for /$(SCTDAQ_VAR)/'))
        explore__sctvar_folder_path.setAutoDefault(True)
        explore__sctvar_folder_path.setToolTip('Explore for /$(SCTDAQ_VAR)/')
        explore__sctvar_folder_path.setStyleSheet('font-size: 12pt; color: black;')

        label__ps_folder_path = QLabel('(Optional) Enter the /$(SCTDAQ_VAR)/ps/ path:')
        label__ps_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        self.input__ps_folder_path = QLineEdit(self)
        self.input__ps_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        explore__ps_folder_path = QPushButton('Explore', self)
        explore__ps_folder_path.clicked.connect(lambda: self.__setDirectory(self.input__ps_folder_path, 'Explore for /$(SCTDAQ_VAR)/ps/'))
        explore__ps_folder_path.setAutoDefault(True)
        explore__ps_folder_path.setToolTip('Explore for /$(SCTDAQ_VAR)/ps/')
        explore__ps_folder_path.setStyleSheet('font-size: 12pt; color: black;')

        label__config_folder_path = QLabel('(Optional) Enter the /$(SCTDAQ_VAR)/config/ path:')
        label__config_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        self.input__config_folder_path = QLineEdit(self)
        self.input__config_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        explore__config_folder_path = QPushButton('Explore', self)
        explore__config_folder_path.clicked.connect(lambda: self.__setDirectory(self.input__config_folder_path, 'Explore for /$(SCTDAQ_VAR)/config/'))
        explore__config_folder_path.setAutoDefault(True)
        explore__config_folder_path.setToolTip('Explore for /$(SCTDAQ_VAR)/config/')
        explore__config_folder_path.setStyleSheet('font-size: 12pt; color: black;')

        label__recursion_depth = QLabel('Specify the search depth:')
        label__recursion_depth.setStyleSheet('font-size: 12pt; color: black;')
        self.input__recursion_depth = QSpinBox(self)
        self.input__recursion_depth.setStyleSheet('font-size: 12pt; color: black;')
        self.input__get_confirm = QCheckBox('Confirm each upload:', self)
        self.input__get_confirm.setLayoutDirection(Qt.RightToLeft)
        self.input__get_confirm.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')
        self.input__upload_files = QCheckBox('Upload local files:', self)
        self.input__upload_files.setLayoutDirection(Qt.RightToLeft)
        self.input__upload_files.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')

        label__regexes = QLabel('(Optional) Regex for filtering files:')
        label__regexes.setStyleSheet('font-size: 12pt; color: black;')
        self.input__regexes = QLineEdit(self)
        self.input__regexes.setStyleSheet('font-size: 12pt; color: black;')
        self.confirm = QPushButton('Confirm', self)
        self.confirm.clicked.connect(lambda: self.__confirm())
        self.confirm.setAutoDefault(True)
        self.confirm.setToolTip('Confirm search/upload options')
        self.confirm.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        self.layout.addWidget(title,                            0, 0, 1, -1)
        self.layout.addWidget(label__sctvar_folder_path,        1, 0, 1, 2)
        self.layout.addWidget(self.input__sctvar_folder_path,   1, 2, 1, 5)
        self.layout.addWidget(explore__sctvar_folder_path,      1, 7, 1, 1)
        self.layout.addWidget(label__ps_folder_path,            2, 0, 1, 2)
        self.layout.addWidget(self.input__ps_folder_path,       2, 2, 1, 5)
        self.layout.addWidget(explore__ps_folder_path,          2, 7, 1, 1)
        self.layout.addWidget(label__config_folder_path,        3, 0, 1, 2)
        self.layout.addWidget(self.input__config_folder_path,   3, 2, 1, 5)
        self.layout.addWidget(explore__config_folder_path,      3, 7, 1, 1)
        self.layout.addWidget(label__recursion_depth,           4, 1, 1, 1)
        self.layout.addWidget(self.input__recursion_depth,      4, 2, 1, 1)
        self.layout.addWidget(self.input__get_confirm,          4, 3, 1, 2)
        self.layout.addWidget(self.input__upload_files,         4, 5, 1, 2)
        self.layout.addWidget(label__regexes,                   5, 1, 1, 1)
        self.layout.addWidget(self.input__regexes,              5, 2, 1, 5)
        self.layout.addWidget(self.confirm,                     5, 7, 1, 1)

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

    # In theory, I have written these member variables as all public, but it is nice to differentiate those which should be able to be accessed

    @DEBUG
    def get__get_confirm(self):
        return self.get_confirm

    @DEBUG
    def get__upload_files(self):
        return self.upload_files

    @DEBUG
    def get__recursion_depth(self):
        return self.recursion_depth

    @DEBUG
    def get__ResultsFolder(self):
        return self.ResultsFolder

    @DEBUG
    def set__get_confirm(self, get_confirm):
        self.get_confirm = get_confirm

    @DEBUG
    def set__upload_files(self, upload_files):
        self.upload_files = upload_files

    @DEBUG
    def set__recursion_depth(self, recursion_depth):
        self.recursion_depth = recursion_depth

    @DEBUG
    def set__ResultsFolder(self, ResultsFolder):
        self.ResultsFolder = ResultsFolder

    @DEBUG
    def initialize(self):
        self.input__sctvar_folder_path.setText(self.sctvar_folder_path)
        self.input__ps_folder_path.setText(self.ps_folder_path)
        self.input__config_folder_path.setText(self.config_folder_path)
        self.input__recursion_depth.setValue(self.recursion_depth)
        self.input__get_confirm.setChecked(self.get_confirm)
        self.input__upload_files.setChecked(self.upload_files)
        self.input__regexes.setText(self.regexes)

    @DEBUG
    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## STEP 2 WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ITSDAQUploadGui__Step2(QWidget):

    @DEBUG
    def __init__(self, parent = None):
        super(ITSDAQUploadGui__Step2, self).__init__(parent)
        self.parent     = parent
        self.layout     = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __setDefaults(self):
        self.ResultsFolder      = None
        self.unfiltered_files   = []

    @DEBUG
    def __getIndicesFromQLineEdit(self, member_QLineEdit, table_length):
        response = member_QLineEdit.text()
        if response == '':
            return []
        elif response == 'all':
            return list(range(table_length))
        else:
            response_split = [item for sublist in response.split() for item in sublist.split(',') if item != '']
            indices = [[int(index)-1] if '-' not in index else list(range(int(index.split('-')[0])-1, int(index.split('-')[1])-1)) for index in response_split]
            indices = [index for sublist in indices for index in sublist if index < table_length and index >= 0]
            return sorted(list(set(indices)))

    @DEBUG
    def __getIndicesFromQTableWidget(self, member_QTableWidget):
        indices = member_QTableWidget.selectionModel().selectedRows()
        indices = [index.row() for index in sorted(indices)]
        return indices

    @DEBUG
    def __fillTable(self):
        self.table__files.setRowCount(len(self.ResultsFolder))
        for i, results_file in enumerate(self.ResultsFolder):
            filename = QTableWidgetItem(str(results_file))
            self.table__files.setItem(i, 0, filename)

    @DEBUG
    def __confirm(self):
        try:
            indices = list(set(self.__getIndicesFromQLineEdit(self.input__files, len(self.ResultsFolder)) + self.__getIndicesFromQTableWidget(self.table__files)))
        except ValueError as e:
            QMessageBox.warning(self, 'Error', 'ValueError in QLineEdit index selection: %s -- please enter a list of positive, space/comma-separated integers or \"all\".' % e)
            return
        if len(indices) == 0:
            reply = QMessageBox.question(self, 'Message', 'No files selected -- do you want to quit?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                sys.exit(0)
            elif reply == QMessageBox.No:
                return
        self.unfiltered_files = self.ResultsFolder.files
        self.ResultsFolder.filterFiles(indices)
        self.signal_done.emit()

    @DEBUG
    def __initUI(self):

        title = QLabel('Step #2: Select the results file(s) to be opened and scanned for tests and then click \"Confirm Files\".')
        title.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        self.table__files = QTableWidget(self)
        self.table__files.setColumnCount(1)
        self.table__files.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files.setHorizontalHeaderLabels(['Filename'])
        self.table__files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table__files.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table__files.setStyleSheet('font-size: 12pt; color: black;')
        header_horizonal__files = self.table__files.horizontalHeader()
        header_horizonal__files.setStyleSheet('font: bold;')
        header_horizonal__files.setDefaultAlignment(Qt.AlignHCenter)
        header_horizonal__files.setSectionResizeMode(QHeaderView.Stretch)
        header_vertical__files = self.table__files.verticalHeader()
        header_vertical__files.setSectionResizeMode(QHeaderView.Fixed)

        label__files = QLabel('Manually select rows from the above table (hold CTRL to deselect) or enter a list of space/comma-separated indices below (hyphens denote ranges) or \"all\" for all:')
        label__files.setStyleSheet('font-size: 12pt; color: black;')

        self.input__files = QLineEdit(self)
        self.input__files.setStyleSheet('font-size: 12pt; color: black;')
        self.confirm = QPushButton('Confirm Files', self)
        self.confirm.clicked.connect(lambda: self.__confirm())
        self.confirm.setAutoDefault(True)
        self.confirm.setToolTip('Confirm selected files')
        self.confirm.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        reset = QPushButton('Reset', self)
        reset.clicked.connect(lambda: self.signal_reset.emit())
        reset.setAutoDefault(True)
        reset.setToolTip('Reset all inputs')
        reset.setStyleSheet('font-size: 12pt;color: black;')

        self.layout.addWidget(title,                0, 0, 1, -1)
        self.layout.addWidget(self.table__files,    1, 0, 1, -1)
        self.layout.addWidget(label__files,         2, 0, 1, -1)
        self.layout.addWidget(self.input__files,    3, 0, 1, 6)
        self.layout.addWidget(self.confirm,         3, 6, 1, 1)
        self.layout.addWidget(reset,                3, 7, 1, 1)

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done     = pyqtSignal()
    signal_reset    = pyqtSignal()

    @DEBUG
    def get__ResultsFolder(self):
        return self.ResultsFolder

    # NOTE: in setting ResultsFolder, it is assumed files have already been discovered and filtered within it
    @DEBUG
    def set__ResultsFolder(self, ResultsFolder):
        self.ResultsFolder = ResultsFolder
        self.unfiltered_files = self.ResultsFolder.files

    @DEBUG
    def resetResultsFolder(self):
        if self.ResultsFolder is not None:
            self.ResultsFolder.files = self.unfiltered_files
        else:
            pass

    @DEBUG
    def initialize(self):
        self.table__files.clearSelection()
        if self.ResultsFolder is not None and len(self.ResultsFolder) > 0:
            self.__fillTable()
            self.confirm.setEnabled(True)
            self.confirm.setFocusPolicy(Qt.StrongFocus)
        else:
            self.table__files.setRowCount(0)
            self.confirm.setEnabled(False)
            self.confirm.setFocusPolicy(Qt.NoFocus)

    @DEBUG
    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## STEP 3 WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ITSDAQUploadGui__Step3(QWidget):

    @DEBUG
    def __init__(self, parent = None, ITkPDSession = None):
        super(ITSDAQUploadGui__Step3, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.layout = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __setDefaults(self):
        self.recursion_depth    = 0
        self.get_confirm        = True
        self.upload_files       = True
        self.ResultsFolder      = None
        self.file_index         = 0
        self.ResultsFile        = None
        self.upload_indices     = []

    @DEBUG
    def __getIndicesFromQLineEdit(self, member_QLineEdit, table_length):
        response = member_QLineEdit.text()
        if response == '':
            return []
        elif response == 'all':
            return list(range(table_length))
        else:
            response_split = [item for sublist in response.split() for item in sublist.split(',') if item != '']
            indices = [[int(index)-1] if '-' not in index else list(range(int(index.split('-')[0])-1, int(index.split('-')[1])-1)) for index in response_split]
            indices = [index for sublist in indices for index in sublist if index < table_length and index >= 0]
            return sorted(list(set(indices)))

    @DEBUG
    def __getIndicesFromQTableWidget(self, member_QTableWidget):
        indices = member_QTableWidget.selectionModel().selectedRows()
        indices = [index.row() for index in sorted(indices)]
        return indices

    @DEBUG
    def __fillTable(self):
        self.table__tests.setRowCount(len(self.ResultsFile))
        for i, test in enumerate(self.ResultsFile):
            self.table__tests.setItem(i, 0, QTableWidgetItem(test['JSON']['properties']['SERIAL_NUMBER']))
            self.table__tests.setItem(i, 1, QTableWidgetItem(test['JSON']['testType']))
            self.table__tests.setItem(i, 2, QTableWidgetItem(test['JSON']['date'] + '-' + test['JSON']['properties']['TIME']))
            self.table__tests.setItem(i, 3, QTableWidgetItem(test['JSON']['runNumber']))
            font = QFont()
            font.setBold(True)
            passed = QTableWidgetItem('YES' if test['JSON']['passed'] else 'NO')
            passed.setFont(font)
            if test['JSON']['passed']:
                passed.setBackground(QColor('green'))
            else:
                passed.setBackground(QColor('red'))
            self.table__tests.setItem(i, 4, passed)
            problems = QTableWidgetItem('YES' if test['JSON']['problems'] else 'NO')
            problems.setFont(font)
            if not test['JSON']['problems']:
                problems.setBackground(QColor('green'))
            else:
                problems.setBackground(QColor('red'))
            self.table__tests.setItem(i, 5, problems)

    @DEBUG
    def __upload(self, i):
        self.ResultsFile.finalizeTest(i, ITkPDSession = self.ITkPDSession, upload_files = self.upload_files, ResultsFolder = self.ResultsFolder, depth = self.recursion_depth, full_test = False)
        status_json = self.ResultsFolder.uploadJSON(i, ITkPDSession = self.ITkPDSession)
        status_files = self.ResultsFolder.uploadFiles(i, ITkPDSession = self.ITkPDSession, upload_files = self.upload_files)
        if status_json and status_files:
            QMessageBox.information(self, 'Success', 'Run number %s for component %s (%s) uploaded successfully!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        elif status_json:
            QMessageBox.warning(self, 'Partial Success', 'JSON for run number %s for component %s (%s) uploaded successfully, issues encountered when uploading one or more files.' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        elif self.upload_files and status_files:
            QMessageBox.warning(self, 'Partial Success', 'Files for run number %s for component %s (%s) uploaded successfully, issues encountered when uploading JSON.' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        else:
            QMessageBox.warning(self, 'Failure', 'Failed to upload run number %s for component %s (%s).' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))

    @DEBUG
    def __confirm(self):
        self.recursion_depth    = int(self.input__recursion_depth.text())
        self.get_confirm        = self.input__get_confirm.isChecked()
        self.upload_files       = self.input__upload_files.isChecked()
        try:
            self.upload_indices = list(set(self.__getIndicesFromQLineEdit(self.input__tests, len(self.ResultsFile)) + self.__getIndicesFromQTableWidget(self.table__tests)))
        except ValueError as e:
            QMessageBox.warning(self, 'Error', 'ValueError in QLineEdit index selection: %s -- please enter a list of positive, space/comma-separated integers or \"all\".' % e)
            return
        if len(self.upload_indices) == 0:
            reply = QMessageBox.question(self, 'Message', 'No tests selected -- do you want to go to the next file?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.__next()
                return
            elif reply == QMessageBox.No:
                return
        if self.get_confirm:
            self.signal_next2Step4.emit()
        else:
            for i in self.upload_indices:
                try:
                    self.__upload(i)
                except ComponentNotFound:
                    QMessageBox.warning(self, 'Error', 'Run number %s for component with serial number \"%s\" could not be found in the ITkPD -- skipping!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER']))
                    continue
                except RequestException as e:
                    QMessageBox.warning(self, 'Error', 'Run number %s for component with serial number \"%s\" could not be finalized/uploaded due to requests exception: %s -- skipping!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], e))
                    continue

    @DEBUG
    def __next(self):
        self.recursion_depth    = int(self.input__recursion_depth.text())
        self.get_confirm        = self.input__get_confirm.isChecked()
        self.upload_files       = self.input__upload_files.isChecked()
        self.file_index += 1
        if self.file_index == len(self.ResultsFolder):
            reply = QMessageBox.question(self, 'Finished', 'All finished -- do you want to quit?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.signal_done.emit()
            elif reply == QMessageBox.No:
                self.file_index -= 1
                return
        else:
            self.initialize()

    @DEBUG
    def __back(self):
        self.recursion_depth    = int(self.input__recursion_depth.text())
        self.get_confirm        = self.input__get_confirm.isChecked()
        self.upload_files       = self.input__upload_files.isChecked()
        self.file_index -= 1
        if self.file_index < 0:
            self.signal_back2Step12.emit()
        else:
            self.initialize()

    @DEBUG
    def __reset(self):
        self.signal_reset.emit()

    @DEBUG
    def __initUI(self):

        title = QLabel('Step #3: Select the test(s) to be uploaded and then click \"Confirm\".')
        title.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        label__reset_args = QLabel('(Optional) Reset search/upload arguments:')
        label__reset_args.setStyleSheet('font-size: 12pt; color: black;')

        label__recursion_depth = QLabel('Specify the search depth:')
        label__recursion_depth.setStyleSheet('font-size: 12pt; color: black;')
        self.input__recursion_depth = QSpinBox(self)
        self.input__recursion_depth.setStyleSheet('font-size: 12pt; color: black;')
        self.input__get_confirm = QCheckBox('Confirm each upload:', self)
        self.input__get_confirm.setLayoutDirection(Qt.RightToLeft)
        self.input__get_confirm.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')
        self.input__upload_files = QCheckBox('Upload local files:', self)
        self.input__upload_files.setLayoutDirection(Qt.RightToLeft)
        self.input__upload_files.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')

        label__current_file = QLabel('Currently looking in:')
        label__current_file.setStyleSheet('font-size: 12pt; color: black;')
        self.current_file = QLineEdit(self)
        self.current_file.setReadOnly(True)
        self.current_file.setStyleSheet('font-size: 12pt; color: black;')

        self.table__tests = QTableWidget(self)
        self.table__tests.setRowCount(0)
        self.table__tests.setColumnCount(6)
        self.table__tests.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__tests.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__tests.setHorizontalHeaderLabels(['Serial Number', 'Test type', 'Date-Time', 'Run Number', 'Passed', 'Problems'])
        self.table__tests.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table__tests.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table__tests.setStyleSheet('font-size: 12pt; color: black;')
        header_horizontal__tests = self.table__tests.horizontalHeader()
        header_horizontal__tests.setStyleSheet('font: bold;')
        header_horizontal__tests.setDefaultAlignment(Qt.AlignHCenter)
        header_horizontal__tests.setSectionResizeMode(QHeaderView.Stretch)
        header_vertical__tests = self.table__tests.verticalHeader()
        header_vertical__tests.setSectionResizeMode(QHeaderView.Fixed)

        label__tests = QLabel('Manually select rows from the above table (hold CTRL to deselect) or enter a list of space/comma-separated indices below (hyphens denote ranges) or \"all\" for all:')
        label__tests.setStyleSheet('font-size: 12pt; color: black;')
        self.input__tests = QLineEdit(self)
        self.input__tests.setStyleSheet('font-size: 12pt; color: black;')
        self.confirm = QPushButton('Confirm Tests', self)
        self.confirm.clicked.connect(lambda: self.__confirm())
        self.confirm.setAutoDefault(True)
        self.confirm.setToolTip('Confirm selected tests')
        self.confirm.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        next = QPushButton('Next', self)
        next.clicked.connect(lambda: self.__next())
        next.setAutoDefault(True)
        next.setToolTip('Move to the next file')
        next.setStyleSheet('font-size: 12pt; color: black;')
        back = QPushButton('Previous', self)
        back.clicked.connect(lambda: self.__back())
        back.setAutoDefault(True)
        back.setToolTip('Move to the previous file')
        back.setStyleSheet('font-size: 12pt; color: black;')
        reset = QPushButton('Reset', self)
        reset.clicked.connect(lambda: self.__reset())
        reset.setAutoDefault(True)
        reset.setToolTip('Reset all inputs and go back to Steps 1 + 2')
        reset.setStyleSheet('font-size: 12pt; color: black;')

        self.layout.addWidget(title,                            0, 0, 1, -1)
        self.layout.addWidget(label__reset_args,                1, 0, 1, -1)
        self.layout.addWidget(label__recursion_depth,           2, 1, 1, 1)
        self.layout.addWidget(self.input__recursion_depth,      2, 2, 1, 1)
        self.layout.addWidget(self.input__get_confirm,          2, 3, 1, 2)
        self.layout.addWidget(self.input__upload_files,         2, 5, 1, 2)
        self.layout.addWidget(label__current_file,              3, 0, 1, 1)
        self.layout.addWidget(self.current_file,                3, 1, 1, -1)
        self.layout.addWidget(self.table__tests,                4, 0, 1, -1)
        self.layout.addWidget(label__tests,                     5, 0, 1, -1)
        self.layout.addWidget(self.input__tests,                6, 0, 1, 6)
        self.layout.addWidget(self.confirm,                     6, 6, 1, 1)
        self.layout.addWidget(back,                             7, 4, 1, 1)
        self.layout.addWidget(next,                             7, 5, 1, 1)
        self.layout.addWidget(reset,                            7, 6, 1, 1)

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done         = pyqtSignal()
    signal_back2Step12  = pyqtSignal()
    signal_next2Step4   = pyqtSignal()
    signal_reset        = pyqtSignal()

    @DEBUG
    def get__get_confirm(self):
        return self.get_confirm

    @DEBUG
    def get__upload_files(self):
        return self.upload_files

    @DEBUG
    def get__recursion_depth(self):
        return self.recursion_depth

    @DEBUG
    def get__ResultsFolder(self):
        return self.ResultsFolder

    @DEBUG
    def get__ResultsFile(self):
        return self.ResultsFile

    @DEBUG
    def get__upload_indices(self):
        return self.upload_indices

    @DEBUG
    def set__get_confirm(self, get_confirm):
        self.get_confirm = get_confirm

    @DEBUG
    def set__upload_files(self, upload_files):
        self.upload_files = upload_files

    @DEBUG
    def set__recursion_depth(self, recursion_depth):
        self.recursion_depth = recursion_depth

    @DEBUG
    def set__ResultsFolder(self, ResultsFolder):
        self.ResultsFolder = ResultsFolder

    @DEBUG
    def set__ResultsFile(self, ResultsFile):
        self.ResultsFile = ResultsFile

    @DEBUG
    def set__upload_indices(self, upload_indices):
        self.upload_indices = upload_indices

    @DEBUG
    def initialize(self):
        self.input__recursion_depth.setValue(self.recursion_depth)
        self.input__get_confirm.setChecked(self.get_confirm)
        self.input__upload_files.setChecked(self.upload_files)
        if self.ResultsFolder is not None and len(self.ResultsFolder) > 0:
            self.ResultsFile = self.ResultsFolder[self.file_index]
            self.ResultsFile.getTests(debug = False)
            self.current_file.setText(str(self.ResultsFile))
            self.table__tests.clearSelection()
            if len(self.ResultsFile) > 0:
                self.__fillTable()
                self.confirm.setEnabled(True)
                self.confirm.setFocusPolicy(Qt.StrongFocus)
            else:
                self.table__tests.setRowCount(0)
                self.confirm.setEnabled(False)
                self.confirm.setFocusPolicy(Qt.NoFocus)
        else:
            self.table__tests.setRowCount(0)
            self.confirm.setEnabled(False)
            self.confirm.setFocusPolicy(Qt.NoFocus)

    @DEBUG
    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## STEP 4 WIDGET -------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ITSDAQUploadGui__Step4(QWidget):

    @DEBUG
    def __init__(self, parent = None, ITkPDSession = None):
        super(ITSDAQUploadGui__Step4, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.layout = QGridLayout(self)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __setDefaults(self):
        self.recursion_depth    = 0
        self.upload_files       = True
        self.ResultsFolder      = None
        self.ResultsFile        = None
        self.test_index         = 0
        self.upload_indices     = []

    @DEBUG
    def __fillTable(self):
        i = self.upload_indices[self.test_index]
        files_to_upload = self.ResultsFile[i]['files_to_upload_FULL']
        self.table__files.setRowCount(len(files_to_upload.keys()))
        for j, filetype in enumerate(files_to_upload.keys()):
            if filetype == 'det_filename':
                label = '.det Config Filename'
            elif filetype == 'strobe_delay_filename':
                label = '.pdf Strobe Delay Filename'
            elif filetype == 'three_point_gain_filename':
                label = '.pdf 3PG Filename'
            elif filetype == 'response_curve_filename':
                label = '.pdf Response Curve Filename'
            elif filetype == 'trim_filename':
                label = '.trim Trim Range Filename'
            elif filetype == 'mask_filename':
                label = '.mask Trim Range Filename'
            elif filetype == 'no_filename':
                label = '.pdf Noise Occupancy Filename'
            else:
                label = filetype
            self.table__files.setItem(j, 0, QTableWidgetItem(label))
            if files_to_upload[filetype] is not None:
                self.table__files.setItem(j, 1, QTableWidgetItem(files_to_upload[filetype]))   
            else:
                font = QFont()
                font.setBold(True)
                not_found = QTableWidgetItem('NOT FOUND')
                not_found.setFont(font)
                not_found.setBackground(QColor('red'))
                self.table__files.setItem(j, 1, not_found)

    @DEBUG
    def __getIndicesFromQTableWidget(self, member_QTableWidget):
        indices = member_QTableWidget.selectionModel().selectedRows()
        indices = [index.row() for index in sorted(indices)]
        return indices

    @DEBUG
    def __upload(self, upload_json = True, upload_these_files = True):
        i = self.upload_indices[self.test_index]
        file_indices = self.__getIndicesFromQTableWidget(self.table__files)
        if file_indices == []:
            filestypes_to_upload = self.ResultsFile[i]['files_to_upload_FULL'].keys()
        else:
            filestypes_to_upload = [filetype for j, filetype in enumerate(self.ResultsFile[i]['files_to_upload_FULL'].keys()) if j in file_indices]
        try:
            if upload_json:
                status_json = self.ResultsFile.uploadJSON(i, ITkPDSession = self.ITkPDSession)
            else:
                status_json = True
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'JSON for run number %s for component %s (%s) could not be uploaded due to requests exception: %s -- please try again or cancel the upload.' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component'], e))
            status_json = False
            return
        try:
            if upload_these_files:
                status_files = self.ResultsFile.uploadFiles(i, ITkPDSession = self.ITkPDSession, upload_files = self.upload_files, filetypes = filestypes_to_upload)
            else:
                status_files = True
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'One or more files for run number %s for component %s (%s) could not be uploaded due to requests exception: %s -- please try again or cancel the upload.' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component'], e))
            status_json = False
            return
        if status_json and status_files:
            QMessageBox.information(self, 'Success', 'Run number %s for component %s (%s) uploaded successfully!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        elif upload_json and status_json:
            QMessageBox.warning(self, 'Partial Success', 'JSON for run number %s for component %s (%s) uploaded successfully, issues encountered when uploading one or more files.' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        elif upload_these_files and status_files:
            QMessageBox.warning(self, 'Partial Success', 'Files for run number %s for component %s (%s) uploaded successfully, issues encountered when uploading JSON.' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        else:
            QMessageBox.warning(self, 'Failure', 'Failed to upload run number %s for component %s (%s).' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
        self.__next()

    @DEBUG
    def __cancel(self):
        self.__next()

    @DEBUG
    def __cancelAll(self):
        self.signal_done.emit()

    @DEBUG
    def __next(self):
        self.test_index += 1
        if self.test_index == len(self.upload_indices):
            self.signal_done.emit()
        else:
            self.initialize()

    @DEBUG
    def __initUI(self):

        title = QLabel('(Step #4): Confirm the JSON and files to be uploaded.')
        title.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        label__json = QLabel('The following JSON will be uploaded:')
        label__json.setStyleSheet('font-size: 12pt; color: black;')

        self.json = QTextEdit(self)
        self.json.setReadOnly(True)
        self.json.setStyleSheet('font-size: 12pt; color: black;')

        label__files = QLabel('The following files will be uploaded:')
        label__files.setStyleSheet('font-size: 12pt; color: black;')

        self.table__files = QTableWidget(self)
        self.table__files.setRowCount(0)
        self.table__files.setColumnCount(2)
        self.table__files.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files.setHorizontalHeaderLabels(['Filetype', 'Filename'])
        self.table__files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table__files.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table__files.setStyleSheet('font-size: 12pt; color: black;')
        header_horizontal__files = self.table__files.horizontalHeader()
        header_horizontal__files.setStyleSheet('font: bold;')
        header_horizontal__files.setDefaultAlignment(Qt.AlignHCenter)
        header_horizontal__files.setSectionResizeMode(QHeaderView.ResizeToContents)
        header_horizontal__files.setStretchLastSection(True)
        header_vertical__files = self.table__files.verticalHeader()
        header_vertical__files.setSectionResizeMode(QHeaderView.Fixed)

        label__selection = QLabel('Select rows from the above table (hold CTRL to deselect) to only upload those files (all are assumed otherwise -- \"NOT FOUND\" files will be skipped).')
        label__selection.setStyleSheet('font-size: 12pt; color: black;')

        self.upload = QPushButton('Upload JSON + Files', self)
        self.upload.clicked.connect(lambda: self.__upload(True, True))
        self.upload.setAutoDefault(True)
        self.upload.setToolTip('Upload JSON (+ selected files)')
        self.upload.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        self.only_json = QPushButton('Upload Only JSON', self)
        self.only_json.clicked.connect(lambda: self.__upload(True, False))
        self.only_json.setAutoDefault(True)
        self.only_json.setToolTip('Upload only JSON')
        self.only_json.setStyleSheet('font-size: 12pt; color: black;')
        self.only_files = QPushButton('Upload Only Files', self)
        self.only_files.clicked.connect(lambda: self.__upload(False, True))
        self.only_files.setAutoDefault(True)
        self.only_files.setToolTip('Upload only selected files')
        self.only_files.setStyleSheet('font-size: 12pt; color: black;')
        cancel = QPushButton('Cancel Upload', self)
        cancel.clicked.connect(lambda: self.__cancel())
        cancel.setAutoDefault(True)
        cancel.setToolTip('Cancel this upload')
        cancel.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        cancel_all = QPushButton('Cancel All', self)
        cancel_all.clicked.connect(lambda: self.__cancelAll())
        cancel_all.setAutoDefault(True)
        cancel_all.setToolTip('Cancel all uploads')
        cancel_all.setStyleSheet('font-size: 12pt; color: black;')

        self.layout.addWidget(title,              0, 0, 1, 7)
        self.layout.addWidget(label__json,        1, 0, 1, -1)
        self.layout.addWidget(self.json,          2, 0, 1, -1)
        self.layout.addWidget(label__files,       3, 0, 1, -1)
        self.layout.addWidget(self.table__files,  4, 0, 1, -1)
        self.layout.addWidget(label__selection,   5, 0, 1, -1)
        self.layout.addWidget(self.upload,        6, 0, 1, 1)
        self.layout.addWidget(self.only_json,     6, 1, 1, 1)
        self.layout.addWidget(self.only_files,    6, 2, 1, 1)
        self.layout.addWidget(cancel,             6, 5, 1, 1)
        self.layout.addWidget(cancel_all,         6, 6, 1, 1)

        self.reset()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

    @DEBUG
    def get__upload_files(self):
        return self.upload_files

    @DEBUG
    def get__recursion_depth(self):
        return self.recursion_depth

    @DEBUG
    def get__ResultsFolder(self):
        return self.ResultsFolder

    @DEBUG
    def get__ResultsFile(self):
        return self.ResultsFile

    @DEBUG
    def get__upload_indices(self):
        return self.upload_indices

    @DEBUG
    def set__upload_files(self, upload_files):
        self.upload_files = upload_files

    @DEBUG
    def set__recursion_depth(self, recursion_depth):
        self.recursion_depth = recursion_depth

    @DEBUG
    def set__ResultsFolder(self, ResultsFolder):
        self.ResultsFolder = ResultsFolder

    @DEBUG
    def set__upload_indices(self, upload_indices):
        self.upload_indices = upload_indices

    # NOTE: in setting ResultsFile, it is assumed files have already been discovered and filtered within it
    @DEBUG
    def set__ResultsFile(self, ResultsFile):
        self.ResultsFile = ResultsFile

    @DEBUG
    def initialize(self):
        self.upload.setAutoDefault(True)
        if self.ResultsFile is not None:
            i = self.upload_indices[self.test_index]
            self.upload.setEnabled(True)
            self.upload.setFocusPolicy(Qt.StrongFocus)
            if self.upload_files:
                self.only_json.setEnabled(True)
                self.only_json.setFocusPolicy(Qt.StrongFocus)
                self.only_files.setEnabled(True)
                self.only_files.setFocusPolicy(Qt.StrongFocus)
            else:
                self.only_json.setEnabled(False)
                self.only_json.setFocusPolicy(Qt.NoFocus)
                self.only_files.setEnabled(False)
                self.only_files.setFocusPolicy(Qt.NoFocus)
            try:
                self.ResultsFile.finalizeTest(i, ITkPDSession = self.ITkPDSession, upload_files = self.upload_files, ResultsFolder = self.ResultsFolder, depth = self.recursion_depth, full_test = False)
            except ComponentNotFound:
                QMessageBox.warning(self, 'Error', 'Run number %s for component with serial number \"%s\" could not be found in the ITkPD -- cannot be uploaded!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER']))
                self.upload.setEnabled(False)
                self.upload.setFocusPolicy(Qt.NoFocus)
                self.only_json.setEnabled(False)
                self.only_json.setFocusPolicy(Qt.NoFocus)
                self.only_files.setEnabled(False)
                self.only_files.setFocusPolicy(Qt.NoFocus)
            except RequestException as e:
                QMessageBox.warning(self, 'Error', 'Run number %s for component with serial number \"%s\" could not be finalized due to requests exception: %s -- cannot be uploaded!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], e))
                self.upload.setEnabled(False)
                self.upload.setFocusPolicy(Qt.NoFocus)
                self.only_json.setEnabled(False)
                self.only_json.setFocusPolicy(Qt.NoFocus)
                self.only_files.setEnabled(False)
                self.only_files.setFocusPolicy(Qt.NoFocus)
            self.json.setText(pp.pformat(self.ResultsFile[i]['JSON']))
            self.table__files.clearSelection()
            if self.upload_files:
                self.__fillTable()
            else:
                self.table__files.setRowCount(0)

    @DEBUG
    def reset(self):
        self.__setDefaults()
        self.initialize()

##############################################################################################################################################
##############################################################################################################################################
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
## MAIN WIDGET ---------------------------------------------------------------------------------------------------------------------------- ##
## ---------------------------------------------------------------------------------------------------------------------------------------- ##
##############################################################################################################################################
##############################################################################################################################################

class ITSDAQUploadGui(QMainWindow):

    @DEBUG
    def __init__(self, parent = None, ITkPDSession = None):
        super(ITSDAQUploadGui, self).__init__(parent)
        self.parent         = parent
        self.ITkPDSession   = ITkPDSession
        self.title          = 'ATLAS ITkPD ITSDAQ Test Upload'
        self.geometry       = (0, 0, 1200, 720)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    @DEBUG
    def __step1Done(self):
        self.step2.set__ResultsFolder(self.step1.get__ResultsFolder())
        self.step2.initialize()

    @DEBUG
    def __step2Done(self):
        self.step3.reset()
        self.step3.set__recursion_depth(self.step1.get__recursion_depth())
        self.step3.set__get_confirm(self.step1.get__get_confirm())
        self.step3.set__upload_files(self.step1.get__upload_files())
        self.step3.set__ResultsFolder(self.step2.get__ResultsFolder())
        self.step3.initialize()
        self.body.setCurrentWidget(self.step3)

    @DEBUG
    def __step3Done(self):
        sys.exit(0)

    @DEBUG
    def __step4Done(self):
        self.body.setCurrentWidget(self.step3)

    @DEBUG
    def __reset(self):
        self.step1.reset()
        self.step2.reset()
        self.step3.reset()
        self.step4.reset()
        self.body.setCurrentWidget(self.step12)

    @DEBUG
    def __back2Step12(self):
        self.step2.resetResultsFolder()
        self.body.setCurrentWidget(self.step12)

    @DEBUG
    def __next2Step4(self):
        self.step4.reset()
        self.step4.set__recursion_depth(self.step3.get__recursion_depth())
        self.step4.set__upload_files(self.step3.get__upload_files())
        self.step4.set__ResultsFolder(self.step3.get__ResultsFolder())
        self.step4.set__ResultsFile(self.step3.get__ResultsFile())
        self.step4.set__upload_indices(self.step3.get__upload_indices())
        self.step4.initialize()
        self.body.setCurrentWidget(self.step4)

    @DEBUG
    def __tieTogetherSignals(self):
        self.step1.signal_done.connect(lambda: self.__step1Done())
        self.step2.signal_done.connect(lambda: self.__step2Done())
        self.step3.signal_done.connect(lambda: self.__step3Done())
        self.step4.signal_done.connect(lambda: self.__step4Done())
        self.step2.signal_reset.connect(lambda: self.__reset())
        self.step3.signal_reset.connect(lambda: self.__reset())
        self.step3.signal_back2Step12.connect(lambda: self.__back2Step12())
        self.step3.signal_next2Step4.connect(lambda: self.__next2Step4())

    ##################################################################
    ############################## MAIN ##############################
    ##################################################################

    @DEBUG
    def __initUI(self):

        ###########################################################
        ### Set size/position of the main window -------------- ###
        ###########################################################

        self.setWindowTitle(self.title)
        self.setGeometry(*self.geometry)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon('../media/ATLAS-Logo-Square-B&W-RGB.png'))

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        close = QShortcut(QKeySequence('Ctrl+Q'), self)
        close.activated.connect(lambda: sys.exit(0))

        self.setStyleSheet('QMessageBox QPushButton { font-size: 12pt; color: black; }')
        self.setStyleSheet('QMessageBox { font-size: 12pt; color: black; }')

        ###########################################################
        ### Instatiate individual pieces ---------------------- ###
        ###########################################################

        self.header = ITSDAQUploadGui__Header(self)
        self.step1  = ITSDAQUploadGui__Step1(self)
        self.step2  = ITSDAQUploadGui__Step2(self)
        self.step3  = ITSDAQUploadGui__Step3(self, self.ITkPDSession)
        self.step4  = ITSDAQUploadGui__Step4(self, self.ITkPDSession)

        ###########################################################
        ### Position individual widgets ----------------------- ###
        ###########################################################

        self.main = QWidget(self)
        self.layout = QGridLayout(self.main)
        self.layout.setAlignment(Qt.AlignTop)
        self.setCentralWidget(self.main)

        self.step12 = QWidget(self)
        self.layout__step12 = QGridLayout(self.step12)
        self.layout__step12.addWidget(self.step1,   0, 0)
        self.layout__step12.addWidget(self.step2,   1, 0)

        self.body = QStackedWidget(self)
        self.body.addWidget(self.step12)
        self.body.addWidget(self.step3)
        self.body.addWidget(self.step4)

        self.layout.addWidget(self.header,          0, 0)
        self.layout.addWidget(self.body,            1, 0)
        
        ###########################################################
        ### Connect all of our signals and run ---------------- ###
        ###########################################################

        self.__tieTogetherSignals()

        self.body.setCurrentWidget(self.step12)

        try:
            ITkPDLoginGui(self.ITkPDSession, self)
        except ExpiredToken as e:
            QMessageBox.warning(self, 'Expired Token', 'ITkPD token has expired: expired at %s, current time is %s -- exitting.' % (e.expired_at, e.current_time))
            sys,exit(1)
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting.' % e, QMessageBox.Ok)
            sys.exit(1)

if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication
        from itk_pdb.dbAccess import ITkPDSession

        session = ITkPDSession()

        app = QApplication(sys.argv)
        exe = ITSDAQUploadGui(None, session)
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
