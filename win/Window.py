#========================================================================================
#title           :Window.py
#description     :The GUI of the program.
#author          :Constanza Levican Torres
#date            :10/11/2016
#version         :0.1
#usage           :Run by the main
#python_version  :2.7
#========================================================================================

import sys
import thread
import Insight
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal, pyqtSlot

class GUI(QtGui.QMainWindow):

    def __init__(self):
        super(GUI, self).__init__()

        self.statusBar = QtGui.QStatusBar()
        self.widget = QtGui.QWidget()
        self.setCentralWidget(self.widget)
        self.setStatusBar(self.statusBar)

        self.insight = Insight.Insight()
        self.insight.signalElectrodeStatus.connect(self.buttonChannelsSetColor)
        self.insight.signalSendText.connect(self.statusBar.showMessage)
        
        self.initUI()
        self.states_dict = {0: 'gray', 1: 'red', 2: 'orange', 3: 'green', 4: 'green'}
        self.numbers_dict = {3: 0, 7: 1, 9: 2, 12: 3, 16: 4}
        thread.start_new_thread(self.insight.start, (), {})

    def initUI(self):
        self.setGeometry(300, 300, 300, 200) # (x, y, ancho, alto)
        self.setWindowTitle('Insight2OSC')
        self.showLabels()
        self.show()

    def showLabels(self):
        grid = QtGui.QGridLayout()

        lb1 = QtGui.QLabel('Frontal Left', self)
        lb2 = QtGui.QLabel('Frontal Right', self)
        lb3 = QtGui.QLabel('Lateral Left', self)
        lb4 = QtGui.QLabel('Lateral Right', self)
        lb5 = QtGui.QLabel('Back', self)

        grid.addWidget(lb1, 1, 0)
        grid.addWidget(lb2, 2, 0)
        grid.addWidget(lb3, 3, 0)
        grid.addWidget(lb4, 4, 0)
        grid.addWidget(lb5, 5, 0)

        self.channelsButtons = []
        for j in range(1, 6):
            btn = QtGui.QPushButton()
            btn.setStyleSheet("background-color: gray")
            #btn.clicked.connect(self.buttonChannelClicked)
            self.channelsButtons.append(btn)
            grid.addWidget(btn, j, 1)

        form = QtGui.QFormLayout()

        lb1 = QtGui.QLabel('IP', self)
        self.le1 = QtGui.QLineEdit(self)
        self.le1.setText('127.0.0.1')
        form.addRow(lb1, self.le1)

        lb2 = QtGui.QLabel('Port', self)
        self.le2 = QtGui.QLineEdit(self)
        self.le2.setText('9001')
        form.addRow(lb2, self.le2)

        self.sendButton = QtGui.QPushButton('Send', self)
        self.sendButton.clicked.connect(self.ButtonSendClicked)

        form.addRow(self.sendButton)

        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(grid)
        hbox.addLayout(form)

        self.widget.setLayout(hbox)

    def buttonChannelsSetColor(self, i, j):
        # i: int. Numero del boton desde el Insight que se traduce en un boton de la GUI
        # j: int. Estado del boton (1-4) que se traduce a un color
        color = self.stateToColor(j)
        btn = self.numberToButton(i)
        btn.setStyleSheet("background-color: " + color)

    def restartChannelsColors(self):
        for i in range(5):
            self.channelsButtons[i].setStyleSheet("background-color: gray")

    def stateToColor(self, j):
        return self.states_dict[j]

    def numberToButton(self, i):
        return self.channelsButtons[self.numbers_dict[i]]

    def ButtonSendClicked(self):
        text_ip = self.le1.text()
        text_port = self.le2.text()
        self.restartChannelsColors()
        self.insight.connect_client(str(text_ip), int(str(text_port)))

    def buttonChannelClicked(self):
        pass


