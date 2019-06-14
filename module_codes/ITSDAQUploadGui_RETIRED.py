#!/usr/bin/env python
# ITSDAQUploadGui_RETIRED.py
# Created: 2019/02/14, Updated: 2019/03/22
# Written by Matthew Basso

############################################################################################################################
################################################## RETIRED? BROKEN? BOTH? ##################################################
############################################################################################################################

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import sys, os
from PyQt5.QtWidgets import (QWidget, QMainWindow, QDesktopWidget, QLabel, QShortcut, QGridLayout, QPushButton, QLineEdit, QCheckBox, QSpinBox,
                                QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QStackedWidget, QTextEdit, QDialog)
from PyQt5.QtGui import QIcon, QKeySequence, QColor, QFont
from PyQt5.QtCore import Qt
from requests.exceptions import RequestException
from ITkPDLoginGui import ITkPDLoginGui
from itk_pdb.ITSDAQTestClasses import ResultsFolder, ComponentNotFound
from itk_pdb.dbAccess import ExpiredToken
from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

class ITSDAQUploadGui(QMainWindow):

    def __init__(self, ITkPDSession = None, parent = None):
 
        super(ITSDAQUploadGui, self).__init__(parent)
        self.parent = parent
        self.ITkPDSession = ITkPDSession
        self.title = 'ATLAS ITkPD ITSDAQ Test Upload'
        self.geometry = (0, 0, 1200, 720)
        self.__setDefaults()
        self.__initUI()

    def __setDefaults(self):
        self.sctvar_folder_path = None
        self.ps_folder_path     = None
        self.config_folder_path = None
        self.get_confirm        = True
        self.upload_files       = True
        self.recursion_depth    = 0
        self.file_regexes       = None
        self.upload_these_files = None
        self.ResultsFolder      = None
        self.ResultsFile        = None
        self.files_with_regex   = None
        self.file_index         = 0
        self.upload_status      = (True, True)
        self.files_to_upload    = []

    ############################################################################################################################################
    # Step 1 ###################################################################################################################################
    ############################################################################################################################################

    def __exploreForDirectory(self, caption, directory = '.'):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        directory_path = QFileDialog.getExistingDirectory(parent = self, caption = caption, directory = directory, options = options)
        return directory_path

    def __get__sctvar_folder_path(self):
        self.input__sctvar_folder_path.setText(self.__exploreForDirectory('Explore for /$(SCTDAQ_VAR)/') + '/')

    def __get__ps_folder_path(self):
        self.input__ps_folder_path.setText(self.__exploreForDirectory('Explore for /$(SCTDAQ_VAR)/ps/') + '/')

    def __get__config_folder_path(self):
        self.input__config_folder_path.setText(self.__exploreForDirectory('Explore for /$(SCTDAQ_VAR)/config/') + '/')

    def __getStep1Args(self):
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
        self.file_regexes       = [(r'' + regex) for sublist in self.input__file_regexes.text().split() for regex in sublist.split(',') if regex != '']
        self.__getAndPrepResultsFolder()
        self.__fillTableWithFiles()
        if len(self.ResultsFolder) != 0:
            self.confirm__file_indices.setEnabled(True)
            self.confirm__file_indices.setFocusPolicy(Qt.StrongFocus)

    def __getAndPrepResultsFolder(self):
        if self.ResultsFolder is None:
            self.ResultsFolder = ResultsFolder(sctvar_folder_path = self.sctvar_folder_path, ps_folder_path = self.ps_folder_path, config_folder_path = self.config_folder_path, enable_printing = False)
        else:
            self.ResultsFolder.reset(sctvar_folder_path = self.sctvar_folder_path, ps_folder_path = self.ps_folder_path, config_folder_path = self.config_folder_path, enable_printing = False)
        self.ResultsFolder.getFiles(depth = self.recursion_depth)
        self.ResultsFolder.filterFilesByRegex(regexes = self.file_regexes)

    ############################################################################################################################################
    # Step 2 ###################################################################################################################################
    ############################################################################################################################################

    def __fillTableWithFiles(self):
        self.table__files.setRowCount(len(self.ResultsFolder))
        for i, results_file in enumerate(self.ResultsFolder):
            filename = QTableWidgetItem(str(results_file))
            self.table__files.setItem(i, 0, filename)

    def __getIndicesFromLineEdit(self, QLineEdit_object, table_length):
        response = QLineEdit_object.text()
        if response == '':
            return []
        elif response == 'all':
            return list(range(table_length))
        else:
            response_split = [item for sublist in response.split() for item in sublist.split(',') if item != '']
            indices = [[int(index)-1] if '-' not in index else list(range(int(index.split('-')[0])-1, int(index.split('-')[1])-1)) for index in response_split]
            indices = [index for sublist in indices for index in sublist if index < table_length and index >= 0]
            return sorted(list(set(indices)))

    def __getIndicesFromTable(self, QTableWidget_object):
        indices = QTableWidget_object.selectionModel().selectedRows()
        indices = [index.row() for index in sorted(indices)]
        return indices

    def __getStep2Args(self):
        try:
            indices = set(self.__getIndicesFromLineEdit(self.input__file_indices, len(self.ResultsFolder)) + self.__getIndicesFromTable(self.table__files))
        except ValueError as e:
            QMessageBox.warning(self, 'Error', 'ValueError in QLineEdit index selection: %s -- please enter a list of positive, space/comma-separated integers or \"all\".' % e)
            return
        if len(indices) == 0:
            # https://stackoverflow.com/questions./1414781/prompt-on-exit-in-pyqt-application
            reply = QMessageBox.question(self, 'Message', 'No files selected -- do you want to quit?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                sys.exit(0)
            elif reply == QMessageBox.No:
                return
        self.files_with_regex = self.ResultsFolder.files
        self.ResultsFolder.filterFiles(indices)
        self.form__bottom.setCurrentWidget(self.form__step3)
        self.file_index = 0
        self.__getStep3Args()

    ############################################################################################################################################
    # Step 3 ###################################################################################################################################
    ############################################################################################################################################

    def __fillTableWithTestsAndDisplayCurrentFile(self):
        self.ResultsFile = self.ResultsFolder[self.file_index]
        self.ResultsFile.enable_printing = False
        self.lineEdit__current_file.setText(str(self.ResultsFile))
        self.ResultsFile.getTests()
        self.table__tests.setRowCount(len(self.ResultsFile))
        for i, test in enumerate(self.ResultsFile.tests):
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

    def __getConfirm(self, test_index):
        self.form__bottom.setCurrentWidget(self.form__step4)
        if self.upload_files:
            files_to_upload = self.ResultsFile[i]['files_to_upload']
        if files_to_upload == {}:
            pass
        else:
            for i, filetype in enumerate(files_to_upload.keys()):
                self.table__files_upload.setItem(i, 0, QTableWidgetItem(filetype))
                if files_to_upload[filetype] is None:
                    self.table__files_upload.setItem(i, 1, QTableWidgetItem('<NOT FOUND>'))
                else:
                    self.table__files_upload.setItem(i, 1, QTableWidgetItem(files_to_upload[filetype]))

    def __getStep3Args(self):
        self.recursion_depth    = int(self.input__recursion_depth_2.text())
        self.get_confirm        = self.input__get_confirm_2.isChecked()
        self.upload_files       = self.input__upload_files_2.isChecked()
        self.__fillTableWithTestsAndDisplayCurrentFile()
        try:
            indices = set(self.__getIndicesFromLineEdit(self.input__test_indices, len(self.ResultsFile)) + self.__getIndicesFromTable(self.table__tests))
        except ValueError as e:
            QMessageBox.warning(self, 'Error', 'ValueError in QLineEdit index selection: %s -- please enter a list of positive, space/comma-separated integers or \"all\".' % e)
            return
        for i in indices:
            try:
                print self.upload_files
                self.ResultsFile.finalizeTest(i, ITkPDSession = self.ITkPDSession, upload_files = self.upload_files, ResultsFolder = self.ResultsFolder, depth = self.recursion_depth, full_test = False)
                if self.get_confirm:
                    self.__getConfirm(i)
                    if self.upload_status == (False, False):
                        QMessageBox.information(self, 'Cancelled', 'Cancelled upload of run number %s for component %s (%s).' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
                        continue
                    if self.upload_status[0]:
                        self.ResultsFile.uploadJSON(i, ITkPDSession = self.ITkPDSession)
                    if self.upload_status[1]:
                        filetypes = [filetype for i, filetype in enumerate(self.ResultsFile[i]['files_to_upload'].keys()) if i in self.files_to_upload]
                        self.ResultsFile.uploadFiles(i, ITkPDSession = self.ITkPDSession, upload_files = self.upload_files, upload_these_files = True, filetypes = filetypes)
                    QMessageBox.information(self, 'Success', 'Run number %s for component %s (%s) uploaded successfully!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], self.ResultsFile[i]['JSON']['component']))
                    self.upload_status = (True, True)
                    self.files_to_upload = []
            except ComponentNotFound:
                QMessageBox.warning(self, 'Error', 'Run number %s for component with serial number \"%s\" could not be found in the ITkPD -- skipping!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER']))
                continue
            except RequestException as e:
                QMessageBox.warning(self, 'Error', 'Run number %s for component with serial number \"%s\" could not be finalized/uploaded due to requests exception: %s -- skipping!' % (self.ResultsFile[i]['JSON']['runNumber'], self.ResultsFile[i]['JSON']['properties']['SERIAL_NUMBER'], e))
                continue

    def __set__confirm_upload(self):
        self.upload_status = (True, True)
        self.files_to_upload = self.__getIndicesFromTable(self.table__files_upload)
        self.dialog__confirm.accept()

    def __set__only_json(self):
        self.upload_status = (True, False)
        self.dialog__confirm.accept()

    def __set__only_files(self):
        self.upload_status = (False, True)
        self.files_to_upload = self.__getIndicesFromTable(self.table__files_upload)
        self.dialog__confirm.accept()

    def __set__cancel_upload(self):
        self.upload_status = (False, False)
        self.dialog__confirm.accept()

    def __getConfirm(self, test_index):
        qtRectangle = self.dialog__confirm.frameGeometry()
        centerPoint = self.frameGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.dialog__confirm.move(qtRectangle.topLeft())
        self.dialog__confirm.setWindowTitle('Confirm Upload: Run Number %s' % self.ResultsFile[test_index]['JSON']['runNumber'])
        self.body__json.setText(pp.pformat(self.ResultsFile[test_index]['JSON']))
        if self.upload_files:
            self.button__only_json.setEnabled(True)
            self.button__only_json.setFocusPolicy(Qt.StrongFocus)
            self.button__only_files.setEnabled(True)
            self.button__only_files.setFocusPolicy(Qt.StrongFocus)
            files_to_upload = self.ResultsFile[test_index]['files_to_upload']
            if files_to_upload == {}:
                pass
            else:
                self.table__files_upload.setRowCount(len(files_to_upload.keys()))
                for i, filetype in enumerate(files_to_upload.keys()):
                    self.table__files_upload.setItem(i, 0, QTableWidgetItem(filetype))
                    if files_to_upload[filetype] is None:
                        self.table__files_upload.setItem(i, 1, QTableWidgetItem('<NOT FOUND>'))
                    else:
                        self.table__files_upload.setItem(i, 1, QTableWidgetItem(files_to_upload[filetype]))
        else:
            self.button__only_json.setEnabled(False)
            self.button__only_json.setFocusPolicy(Qt.NoFocus)
            self.button__only_files.setEnabled(False)
            self.button__only_files.setFocusPolicy(Qt.NoFocus)
        self.dialog__confirm.exec_()

    def __next(self):
        self.file_index += 1
        if self.file_index == len(self.ResultsFolder):
            reply = QMessageBox.question(self, 'Finished', 'All finished -- do you want to quit?', QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                sys.exit(0)
            elif reply == QMessageBox.No:
                self.__reset()
        else:
            self.table__tests.clearSelection()
            self.input__test_indices.setText('')
            self.__fillTableWithTestsAndDisplayCurrentFile()

    def __back(self):
        self.file_index -= 1
        if self.file_index < 0:
            self.ResultsFolder.files = self.files_with_regex
            self.form__bottom.setCurrentWidget(self.form__step12)
        else:
            self.input__test_indices.setText('')
            self.__fillTableWithTestsAndDisplayCurrentFile()

    def __reset(self):
        self.__setDefaults()
        self.input__sctvar_folder_path.setText('')
        self.input__ps_folder_path.setText('')
        self.input__config_folder_path.setText('')
        self.input__recursion_depth.setValue(self.recursion_depth)
        self.input__get_confirm.setChecked(self.get_confirm)
        self.input__upload_files.setChecked(self.upload_files)
        self.input__file_regexes.setText('')
        self.table__files.setRowCount(0)
        self.input__file_indices.setText('')
        self.confirm__file_indices.setEnabled(False)
        self.confirm__file_indices.setFocusPolicy(Qt.NoFocus)
        self.form__bottom.setCurrentWidget(self.form__step12)

    ############################################################################################################################################
    # -----------------------------------------------------------------------------------------------------------------------------------------#
    # RUN THE MAIN FUNCTION OF THE UI CLASS ---------------------------------------------------------------------------------------------------#
    # -----------------------------------------------------------------------------------------------------------------------------------------#
    ############################################################################################################################################

    # Super messy, could probably be organized better
    # But since I am learning how to build this as I go along, this is probably okay for a first attempt
    def __initUI(self):

        self.setWindowTitle(self.title)
        self.setGeometry(*self.geometry)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon('../media/ATLAS-Logo-Square-B&W-RGB.png'))

        #-------------------------------------------------------------------------------------------------------------------#
        #-------------------------------------------------------------------------------------------------------------------#
        #-------------------------------------------------------------------------------------------------------------------#
        # NOTE TO MATTHEW: USE ME TO SET GLOBAL STYLESHEETS IN THE FUTURE !!!                                               #
        # SEE: https://stackoverflow.com/questions/49140843/setting-background-of-qpushbutton-in-qmessagebox                #
        self.setStyleSheet('QMessageBox QPushButton { font-size: 12pt; color: black; }')
        self.setStyleSheet('QMessageBox { font-size: 12pt; color: black; }')
        #-------------------------------------------------------------------------------------------------------------------#
        #-------------------------------------------------------------------------------------------------------------------#
        #-------------------------------------------------------------------------------------------------------------------#

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        shortcut__close = QShortcut(QKeySequence('Ctrl+Q'), self)
        shortcut__close.activated.connect(lambda: sys.exit(0))

        form__main = QWidget(self)
        grid__main = QGridLayout(form__main)
        grid__main.setAlignment(Qt.AlignTop)
        self.setCentralWidget(form__main)

        ############################################################################################################################################
        # Top ######################################################################################################################################
        ############################################################################################################################################

        title = QLabel('ATLAS ITk Production Database -- ITSDAQ Test Upload GUI', self)
        title.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignLeft;')

        quit = QPushButton('Quit', self)
        quit.clicked.connect(lambda: sys.exit(0))
        quit.setAutoDefault(True)
        quit.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Quit the GUI'))
        quit.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        form__top = QWidget(self)
        grid__top = QGridLayout(form__top)
        grid__top.addWidget(title, 0, 0, 1, 7)
        grid__top.addWidget(quit, 0, 7, 1, 1)

        ############################################################################################################################################
        # Step 1 ###################################################################################################################################
        ############################################################################################################################################

        label__step1 = QLabel('Step #1: Inform the program of the location of ITSDAQ results files and then click \"Confirm\".')
        label__step1.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        label__sctvar_folder_path = QLabel('Enter the /$(SCTDAQ_VAR)/(results/) path:')
        label__sctvar_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        self.input__sctvar_folder_path = QLineEdit(self)
        self.input__sctvar_folder_path.setText(os.getenv('SCTDAQ_VAR', ''))
        self.input__sctvar_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        explore__sctvar_folder_path = QPushButton('Explore', self)
        explore__sctvar_folder_path.clicked.connect(self.__get__sctvar_folder_path)
        explore__sctvar_folder_path.setAutoDefault(True)
        explore__sctvar_folder_path.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Explore for /$(SCTDAQ_VAR)/'))
        explore__sctvar_folder_path.setStyleSheet('font-size: 12pt; color: black;')

        label__ps_folder_path = QLabel('(Optional) Enter the /$(SCTDAQ_VAR)/ps/ path:')
        label__ps_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        self.input__ps_folder_path = QLineEdit(self)
        self.input__ps_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        explore__ps_folder_path = QPushButton('Explore', self)
        explore__ps_folder_path.clicked.connect(self.__get__ps_folder_path)
        explore__ps_folder_path.setAutoDefault(True)
        explore__ps_folder_path.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Explore for /$(SCTDAQ_VAR)/ps/'))
        explore__ps_folder_path.setStyleSheet('font-size: 12pt; color: black;')

        label__config_folder_path = QLabel('(Optional) Enter the /$(SCTDAQ_VAR)/config/ path:')
        label__config_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        self.input__config_folder_path = QLineEdit(self)
        self.input__config_folder_path.setStyleSheet('font-size: 12pt; color: black;')
        explore__config_folder_path = QPushButton('Explore', self)
        explore__config_folder_path.clicked.connect(self.__get__config_folder_path)
        explore__config_folder_path.setAutoDefault(True)
        explore__config_folder_path.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Explore for /$(SCTDAQ_VAR)/config/'))
        explore__config_folder_path.setStyleSheet('font-size: 12pt; color: black;')

        label__recursion_depth = QLabel('Specify the search depth:')
        label__recursion_depth.setStyleSheet('font-size: 12pt; color: black;')
        self.input__recursion_depth = QSpinBox(self)
        self.input__recursion_depth.setValue(self.recursion_depth)
        self.input__recursion_depth.setStyleSheet('font-size: 12pt; color: black;')
        self.input__get_confirm = QCheckBox('Confirm each upload:', self)
        self.input__get_confirm.setChecked(self.get_confirm)
        self.input__get_confirm.setLayoutDirection(Qt.RightToLeft)
        self.input__get_confirm.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')
        self.input__upload_files = QCheckBox('Upload local files:', self)
        self.input__upload_files.setChecked(self.upload_files)
        self.input__upload_files.setLayoutDirection(Qt.RightToLeft)
        self.input__upload_files.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')

        label__file_regexes = QLabel('(Optional) Regex for filtering files:')
        label__file_regexes.setStyleSheet('font-size: 12pt; color: black;')
        self.input__file_regexes = QLineEdit(self)
        self.input__file_regexes.setStyleSheet('font-size: 12pt; color: black;')
        self.confirm__args = QPushButton('Confirm', self)
        self.confirm__args.clicked.connect(self.__getStep1Args)
        self.confirm__args.setAutoDefault(True)
        self.confirm__args.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Confirm search/upload options'))
        self.confirm__args.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        form__step1 = QWidget(self)
        grid__step1 = QGridLayout(form__step1)
        grid__step1.addWidget(label__step1,                     0, 0, 1, -1)
        grid__step1.addWidget(label__sctvar_folder_path,        1, 0, 1, 2)
        grid__step1.addWidget(self.input__sctvar_folder_path,   1, 2, 1, 5)
        grid__step1.addWidget(explore__sctvar_folder_path,      1, 7, 1, 1)
        grid__step1.addWidget(label__ps_folder_path,            2, 0, 1, 2)
        grid__step1.addWidget(self.input__ps_folder_path,       2, 2, 1, 5)
        grid__step1.addWidget(explore__ps_folder_path,          2, 7, 1, 1)
        grid__step1.addWidget(label__config_folder_path,        3, 0, 1, 2)
        grid__step1.addWidget(self.input__config_folder_path,   3, 2, 1, 5)
        grid__step1.addWidget(explore__config_folder_path,      3, 7, 1, 1)
        grid__step1.addWidget(label__recursion_depth,           4, 1, 1, 1)
        grid__step1.addWidget(self.input__recursion_depth,      4, 2, 1, 1)
        grid__step1.addWidget(self.input__get_confirm,          4, 3, 1, 2)
        grid__step1.addWidget(self.input__upload_files,         4, 5, 1, 2)
        grid__step1.addWidget(label__file_regexes,              5, 1, 1, 1)
        grid__step1.addWidget(self.input__file_regexes,         5, 2, 1, 5)
        grid__step1.addWidget(self.confirm__args,               5, 7, 1, 1)

        ############################################################################################################################################
        # Step 2 ###################################################################################################################################
        ############################################################################################################################################

        label__step2 = QLabel('Step #2: Select the results file(s) to be opened and scanned for tests and then click \"Confirm Files\".')
        label__step2.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        self.table__files = QTableWidget(self)
        self.table__files.setRowCount(0)
        self.table__files.setColumnCount(1)
        self.table__files.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files.setHorizontalHeaderLabels(['Filename'])
        self.table__files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table__files.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table__files.setStyleSheet('font-size: 12pt; color: black;')
        header = self.table__files.horizontalHeader()
        header.setStyleSheet('font: bold;')
        header.setDefaultAlignment(Qt.AlignHCenter)
        header.setSectionResizeMode(QHeaderView.Stretch)
        # header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # header.setStretchLastSection(True)
        header_vertical__files = self.table__files.verticalHeader()
        header_vertical__files.setSectionResizeMode(QHeaderView.Fixed)
        # header_vertical__tests.setDefaultSectionSize(24)

        # label__file_indices = QLabel('Manually select rows from the above table or enter a list of space/comma-separated indices below (hyphens denote ranges), \"all\" for all, or \"none\" for none:')
        label__file_indices = QLabel('Manually select rows from the above table or enter a list of space/comma-separated indices below (hyphens denote ranges) or \"all\" for all:')
        label__file_indices.setStyleSheet('font-size: 12pt; color: black;')

        self.input__file_indices = QLineEdit(self)
        self.input__file_indices.setStyleSheet('font-size: 12pt; color: black;')
        self.confirm__file_indices = QPushButton('Confirm Files', self)
        self.confirm__file_indices.clicked.connect(self.__getStep2Args)
        self.confirm__file_indices.setAutoDefault(True)
        self.confirm__file_indices.setEnabled(False)
        self.confirm__file_indices.setFocusPolicy(Qt.NoFocus)
        self.confirm__file_indices.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Confirm selected files'))
        self.confirm__file_indices.setStyleSheet('font-size: 12pt; font:bold; color: black;')

        form__step2 = QWidget(self)
        grid__step2 = QGridLayout(form__step2)
        grid__step2.addWidget(label__step2,                 0, 0, 1, -1)
        grid__step2.addWidget(self.table__files,            1, 0, 1, -1)
        grid__step2.addWidget(label__file_indices,          2, 0, 1, -1)
        grid__step2.addWidget(self.input__file_indices,     3, 0, 1, 7)
        grid__step2.addWidget(self.confirm__file_indices,   3, 7, 1, 1)

        ############################################################################################################################################
        # Step 3 ###################################################################################################################################
        ############################################################################################################################################

        label__step3 = QLabel('Step #3: Select the test(s) to be uploaded and then click \"Confirm\".')
        label__step3.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        label__reset_args = QLabel('(Optional) Reset search/upload arguments:')
        label__reset_args.setStyleSheet('font-size: 12pt; color: black;')

        # 2 := duplication of the above ones (else, the widgets don't reset to their original position when we use Reset)
        # A little hacky...
        label__recursion_depth_2 = QLabel('Specify the search depth:')
        label__recursion_depth_2.setStyleSheet('font-size: 12pt; color: black;')
        self.input__recursion_depth_2 = QSpinBox(self)
        self.input__recursion_depth_2.setValue(self.recursion_depth)
        self.input__recursion_depth_2.setStyleSheet('font-size: 12pt; color: black;')
        self.input__get_confirm_2 = QCheckBox('Confirm each upload:', self)
        self.input__get_confirm_2.setChecked(self.get_confirm)
        self.input__get_confirm_2.setLayoutDirection(Qt.RightToLeft)
        self.input__get_confirm_2.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')
        self.input__upload_files_2 = QCheckBox('Upload local files:', self)
        self.input__upload_files_2.setChecked(self.upload_files)
        self.input__upload_files_2.setLayoutDirection(Qt.RightToLeft)
        self.input__upload_files_2.setStyleSheet('font-size: 12pt; color: black; margin-left: 50%; margin-right: 50%;')

        label__current_file = QLabel('Currently looking in:')
        label__current_file.setStyleSheet('font-size: 12pt; color: black;')
        self.lineEdit__current_file = QLineEdit(self)
        self.lineEdit__current_file.setReadOnly(True)
        self.lineEdit__current_file.setStyleSheet('font-size: 12pt; color: black;')

        self.table__tests = QTableWidget(self)
        self.table__tests.setRowCount(0)
        self.table__tests.setColumnCount(6)
        self.table__tests.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__tests.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__tests.setHorizontalHeaderLabels(['Serial Number', 'Test type', 'Date-Time', 'Run Number', 'Passed', 'Problems'])
        self.table__tests.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table__tests.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table__tests.setStyleSheet('font-size: 12pt; color: black;')
        header__tests = self.table__tests.horizontalHeader()
        header__tests.setStyleSheet('font: bold;')
        header__tests.setDefaultAlignment(Qt.AlignHCenter)
        header__tests.setSectionResizeMode(QHeaderView.Stretch)
        header_vertical__tests = self.table__tests.verticalHeader()
        header_vertical__tests.setSectionResizeMode(QHeaderView.Fixed)

        self.input__test_indices = QLineEdit(self)
        self.input__test_indices.setStyleSheet('font-size: 12pt; color: black;')
        label__test_indices = QLabel('Manually select rows from the above table or enter a list of space/comma-separated indices below (hyphens denote ranges) or \"all\" for all:')
        label__test_indices.setStyleSheet('font-size: 12pt; color: black;')
        button__confirm_tests = QPushButton('Confirm Tests', self)
        button__confirm_tests.clicked.connect(self.__getStep3Args)
        button__confirm_tests.setAutoDefault(True)
        button__confirm_tests.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Confirm selected tests'))
        button__confirm_tests.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        # DOES TAB GO TO NEXT BEFORE BACK B/C IT IS DEFINED FIRST?
        button__next = QPushButton('Next', self)
        button__next.clicked.connect(self.__next)
        button__next.setAutoDefault(True)
        button__next.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Move to the next file'))
        button__next.setStyleSheet('font-size: 12pt; color: black;')
        button__back = QPushButton('Previous', self)
        button__back.clicked.connect(self.__back)
        button__back.setAutoDefault(True)
        button__back.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Move to the previous file'))
        button__back.setStyleSheet('font-size: 12pt; color: black;')
        button__reset = QPushButton('Reset', self)
        button__reset.clicked.connect(self.__reset)
        button__reset.setAutoDefault(True)
        button__reset.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Go back to Steps 1+2'))
        button__reset.setStyleSheet('font-size: 12pt; color: black;')

        self.form__step3 = QWidget(self)
        grid__step3 = QGridLayout(self.form__step3)
        grid__step3.addWidget(label__step3,                     0, 0, 1, -1)
        grid__step3.addWidget(label__reset_args,                1, 0, 1, -1)
        grid__step3.addWidget(label__recursion_depth_2,         2, 1, 1, 1)
        grid__step3.addWidget(self.input__recursion_depth_2,    2, 2, 1, 1)
        grid__step3.addWidget(self.input__get_confirm_2,        2, 3, 1, 2)
        grid__step3.addWidget(self.input__upload_files_2,       2, 5, 1, 2)
        grid__step3.addWidget(label__current_file,              3, 0, 1, 1)
        grid__step3.addWidget(self.lineEdit__current_file,      3, 1, 1, -1)
        grid__step3.addWidget(self.table__tests,                4, 0, 1, -1)
        grid__step3.addWidget(label__test_indices,              5, 0, 1, -1)
        grid__step3.addWidget(self.input__test_indices,         6, 0, 1, 6)
        grid__step3.addWidget(button__confirm_tests,            6, 6, 1, 1)
        grid__step3.addWidget(button__back,                     7, 4, 1, 1)
        grid__step3.addWidget(button__next,                     7, 5, 1, 1)
        grid__step3.addWidget(button__reset,                    7, 6, 1, 1)

        ############################################################################################################################################
        # Upload File Dialog #######################################################################################################################
        ############################################################################################################################################

        self.dialog__confirm = QDialog(self)
        self.dialog__confirm.setGeometry(0, 0, 1000, 500)
        self.dialog__confirm.setFixedSize(self.dialog__confirm.size())
        shortcut__close2 = QShortcut(QKeySequence('Ctrl+Q'), self.dialog__confirm)
        shortcut__close2.activated.connect(lambda: sys.exit(0))

        label__step4 = QLabel('(Step #4): Confirm the JSON and files to be uploaded.')
        label__step4.setStyleSheet('font-size: 14pt; font: bold; color: black;')

        label__confirm_json = QLabel('The following JSON will be uploaded:')
        label__confirm_json.setStyleSheet('font-size: 12pt; color: black;')

        self.body__json = QTextEdit(self)
        self.body__json.setReadOnly(True)
        self.body__json.setStyleSheet('font-size: 12pt; color: black;')

        label__confirm_files = QLabel('The following files will be uploaded:')
        label__confirm_files.setStyleSheet('font-size: 12pt; color: black;')

        self.table__files_upload = QTableWidget(self)
        self.table__files_upload.setRowCount(0)
        self.table__files_upload.setColumnCount(2)
        self.table__files_upload.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files_upload.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table__files_upload.setHorizontalHeaderLabels(['Filetype', 'Filename'])
        self.table__files_upload.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table__files_upload.setSelectionBehavior(QAbstractItemView.SelectRows)
        header__files_upload = self.table__files_upload.horizontalHeader()
        header__files_upload.setStyleSheet('font: bold;')
        header__files_upload.setDefaultAlignment(Qt.AlignHCenter)
        header__files_upload.setSectionResizeMode(QHeaderView.ResizeToContents)
        header__files_upload.setStretchLastSection(True)
        header_vertical__files_upload = self.table__files_upload.verticalHeader()
        header_vertical__files_upload.setSectionResizeMode(QHeaderView.Fixed)

        button__upload = QPushButton('Upload All', self)
        button__upload.clicked.connect(self.__set__confirm_upload)
        button__upload.setAutoDefault(True)
        button__upload.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Upload JSON + files'))
        button__upload.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        self.button__only_json = QPushButton('Upload Only JSON', self)
        self.button__only_json.clicked.connect(self.__set__only_json)
        self.button__only_json.setAutoDefault(True)
        self.button__only_json.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Upload only JSON'))
        self.button__only_json.setStyleSheet('font-size: 12pt; color: black;')
        self.button__only_files = QPushButton('Upload Only Files', self)
        self.button__only_files.clicked.connect(self.__set__only_files)
        self.button__only_files.setAutoDefault(True)
        self.button__only_files.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Upload only files'))
        self.button__only_files.setStyleSheet('font-size: 12pt; color: black;')
        button__cancel = QPushButton('Cancel Upload', self)
        button__cancel.clicked.connect(self.__set__cancel_upload)
        button__cancel.setAutoDefault(True)
        button__cancel.setToolTip('<span style=\"background-color:black;color:white;font:normal;font-size:12pt\">{0}</span>'.format('Cancel this upload'))
        button__cancel.setStyleSheet('font-size: 12pt; font: bold; color: black;')

        grid__confirm = QGridLayout(self.dialog__confirm)
        grid__confirm.addWidget(label__step4,                     0, 0, 1, 6)
        grid__confirm.addWidget(label__confirm_json,              1, 0, 1, -1)
        grid__confirm.addWidget(self.body__json,                  2, 0, 1, -1)
        grid__confirm.addWidget(label__confirm_files,             3, 0, 1, -1)
        grid__confirm.addWidget(self.table__files_upload,         4, 0, 1, -1)
        grid__confirm.addWidget(button__upload,                   5, 1, 1, 1)
        grid__confirm.addWidget(self.button__only_json,           5, 2, 1, 1)
        grid__confirm.addWidget(self.button__only_files,          5, 3, 1, 1)
        grid__confirm.addWidget(button__cancel,                   5, 4, 1, 1)

        ############################################################################################################################################
        # Configure widget arrangement #############################################################################################################
        ############################################################################################################################################

        grid__main.addWidget(form__top, 0, 0)
        self.form__bottom = QStackedWidget(self)
        grid__main.addWidget(self.form__bottom, 1, 0)
        
        self.form__step12 = QWidget(self)
        grid__step12 = QGridLayout(self.form__step12)
        grid__step12.addWidget(form__step1, 0, 0)
        grid__step12.addWidget(form__step2, 1, 0)

        self.form__bottom.addWidget(self.form__step12)
        self.form__bottom.addWidget(self.form__step3)
        self.form__bottom.setCurrentWidget(self.form__step12)

        ############################################################################################################################################
        #------------------------------------------------------------------------------------------------------------------------------------------#
        # LOGIN INTO THE GUI ----------------------------------------------------------------------------------------------------------------------#
        #------------------------------------------------------------------------------------------------------------------------------------------#
        ############################################################################################################################################
        # Gui is opened through a self.parent.open() call in ITkPDLoginGui, following authentication
        try:
            ITkPDLoginGui(self.ITkPDSession, self)
        except ExpiredToken as e:
            QMessageBox.warning(self, 'Expired Token', 'ITkPD token has expired: expired at %s, current time is %s -- exitting.' % (e.expired_at, e.current_time))
            sys,exit(1)
        except RequestException as e:
            QMessageBox.warning(self, 'Error', 'Unhandled requests exception raised: %s -- exitting.' % e, QMessageBox.Ok)
            sys.exit(1)
        # self.show()

if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication
        from itk_pdb.dbAccess import ITkPDSession

        session = ITkPDSession()

        app = QApplication(sys.argv)
        exe = ITSDAQUploadGui(session)
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
