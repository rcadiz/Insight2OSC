#========================================================================================
#title           :Main.py
#description     :This is the main of the program.
#date            :10/11/2016
#version         :0.1
#usage           :python main.py
#python_version  :2.7
#========================================================================================

import sys
import atexit
from PyQt4 import QtGui, QtCore
from Window import GUI

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())