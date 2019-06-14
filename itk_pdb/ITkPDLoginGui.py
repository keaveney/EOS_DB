#!/usr/bin/env python
# ITkPDLoginGui.py -- class for logging into the ITk Production Database
# Created: 2019/02/13, Updated: 2019/03/18
# Written by Matthew Basso

import sys
from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox, QDesktopWidget, QShortcut
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import pyqtSignal
from requests.exceptions import RequestException

class ITkPDLoginGui(QDialog):

    def __init__(self, ITkPDSession = None, parent = None, show_immediately = True):

        super(ITkPDLoginGui, self).__init__(parent)
        self.ITkPDSession = ITkPDSession
        self.parent = parent
        self.show_immediately = show_immediately
        self.title = 'ATLAS ITkPD Login'
        self.geometry = (0, 0, 480, 240)
        self.__initUI()

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PRIVATE MEMBER FUNCTIONS --------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    def __initUI(self):

        self.setWindowTitle(self.title)
        self.setGeometry(*self.geometry)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon('../media/ATLAS-Logo-Square-B&W-RGB.png'))

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        shortcut__close = QShortcut(QKeySequence('Ctrl+Q'), self)
        shortcut__close.activated.connect(lambda: sys.exit(0))

        title = QLabel('ATLAS ITk Production Database Login', self)
        title.setStyleSheet('font-size: 18pt; font: bold; color: black; qproperty-alignment: AlignCenter;')

        title__accessCode1 = QLabel('Access Code 1:', self)
        title__accessCode1.setStyleSheet('font-size: 12pt; color: black;')
        self.line__accessCode1 = QLineEdit(self)
        self.line__accessCode1.setEchoMode(QLineEdit.Password)

        title__accessCode2 = QLabel('Access Code 2:', self)
        title__accessCode2.setStyleSheet('font-size: 12pt; color: black;')
        self.line__accessCode2 = QLineEdit(self)
        self.line__accessCode2.setEchoMode(QLineEdit.Password)

        login = QPushButton('Login', self)
        login.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        login.clicked.connect(lambda: self.__login())
        quit = QPushButton('Quit', self)
        quit.setStyleSheet('font-size: 12pt; font: bold; color: black;')
        quit.clicked.connect(lambda: sys.exit(0))

        buttons = QWidget(self)
        layout__buttons = QGridLayout(buttons)
        layout__buttons.addWidget(login,            0, 0, 1, 1)
        layout__buttons.addWidget(quit,             0, 1, 1, 1)

        layout = QGridLayout(self)
        layout.addWidget(title,                     0, 0, 1, -1)
        layout.addWidget(title__accessCode1,        1, 0, 1, 1)
        layout.addWidget(self.line__accessCode1,    1, 1, 1, 1)
        layout.addWidget(title__accessCode2,        2, 0, 1, 1)
        layout.addWidget(self.line__accessCode2,    2, 1, 1, 1)
        layout.addWidget(buttons,                   3, 0, 1, -1)

        if self.show_immediately:
            self.show()

    # Add support for checking if tokens are expired or not (?)
    # Keys: "expires_at", "issued_at", "expires_in"
    def __login(self):
        if self.ITkPDSession is not None:
            # NOTE: this is hacky for now, doesn't actually check if the token is still good
            if 'Authorization' in self.ITkPDSession.headers.keys():
                QMessageBox.information(self, 'Success', 'Token already available!')
                self.signal_done.emit()
                self.close()
                if self.parent is not None:
                    self.parent.show()
            else:
                try:
                    self.ITkPDSession.enable_printing = False
                    accessCode1 = self.line__accessCode1.text()
                    accessCode2 = self.line__accessCode2.text()
                    if accessCode1 == '' or accessCode2 == '':
                        QMessageBox.warning(self, 'Warning', 'Access code(s) left blank')
                    else: 
                        self.ITkPDSession.authenticate(accessCode1, accessCode2)
                        QMessageBox.information(self, 'Success', 'Authentication successful!')
                        self.signal_done.emit()
                        self.close()
                        if self.parent is not None:
                            self.parent.show()
                except RequestException as e:
                    QMessageBox.warning(self, 'Error', 'requests exception raised: %s' % e)
        else:
            QMessageBox.warning(self, 'Error', 'No ITkPDSession available')

    ############################################################################################################################################
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    # PUBLIC MEMBER FUNCTIONS ---------------------------------------------------------------------------------------------------------------- #
    # ---------------------------------------------------------------------------------------------------------------------------------------- #
    ############################################################################################################################################

    signal_done = pyqtSignal()

if __name__ == '__main__':

    try:

        from PyQt5.QtWidgets import QApplication
        from itk_pdb.dbAccess import ITkPDSession

        session = ITkPDSession()

        app = QApplication(sys.argv)
        exe = ITkPDLoginGui(session)
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        sys.exit(1)
