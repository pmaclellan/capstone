#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import Queue
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import daq_connection


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initClient()
        self.daqWidget = DaqWidget(self)
        self.setCentralWidget(self.daqWidget)
        self.initUI()
        
    def initClient(self):
        self.daq = daq_connection.DaqConnection(self)

    def initUI(self):               
        self.statusBar().showMessage('Not Connected')
        self.setGeometry(300, 300, 900, 600)
        self.setWindowTitle('Daqula')
        self.show()

    def setStatusBarMessage(self, message):
        self.statusBar().showMessage(message)

    def forward_to_plot(self, datum):
        self.daqWidget.dc.add_to_queue(datum)

    def updateActiveChannels(self, state):
        print(state)

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(10000)
        self.queue = Queue.Queue()

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        to_plot = {}
        for i in range(10):
            if not self.queue.empty():
                readings = self.queue.get()
                for channel in readings.keys():
                    if (to_plot.has_key(channel)):
                        to_plot[channel].append(readings[channel])
                    else:
                        to_plot[channel] = [readings[channel]]

        for channel in to_plot.keys():
            self.axes.plot(range(len(to_plot[channel])), to_plot[channel])
        self.draw()

    def add_to_queue(self, datum):
        self.queue.put(datum)

class DaqWidget(QtGui.QWidget):
    
    def __init__(self, parent):
        super(DaqWidget, self).__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        ########## Channel Checkboxes ##########
        self.channelsLabel = QtGui.QLabel('Active ADC Channels', self)

        self.channel_0_0 = QtGui.QCheckBox('0.0', self)
        self.channel_0_0.toggle()
        self.channel_0_0.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_1 = QtGui.QCheckBox('0.1', self)
        self.channel_0_1.toggle()
        self.channel_0_1.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_2 = QtGui.QCheckBox('0.2', self)
        self.channel_0_2.toggle()
        self.channel_0_2.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_3 = QtGui.QCheckBox('0.3', self)
        self.channel_0_3.toggle()
        self.channel_0_3.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_4 = QtGui.QCheckBox('0.4', self)
        self.channel_0_4.toggle()
        self.channel_0_4.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_5 = QtGui.QCheckBox('0.5', self)
        self.channel_0_5.toggle()
        self.channel_0_5.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_6 = QtGui.QCheckBox('0.6', self)
        self.channel_0_6.toggle()
        self.channel_0_6.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_0_7 = QtGui.QCheckBox('0.7', self)
        self.channel_0_7.toggle()
        self.channel_0_7.stateChanged.connect(self.parent.updateActiveChannels)

        self.channel_1_0 = QtGui.QCheckBox('1.0', self)
        self.channel_1_0.toggle()
        self.channel_1_0.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_1 = QtGui.QCheckBox('1.1', self)
        self.channel_1_1.toggle()
        self.channel_1_1.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_2 = QtGui.QCheckBox('1.2', self)
        self.channel_1_2.toggle()
        self.channel_1_2.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_3 = QtGui.QCheckBox('1.3', self)
        self.channel_1_3.toggle()
        self.channel_1_3.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_4 = QtGui.QCheckBox('1.4', self)
        self.channel_1_4.toggle()
        self.channel_1_4.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_5 = QtGui.QCheckBox('1.5', self)
        self.channel_1_5.toggle()
        self.channel_1_5.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_6 = QtGui.QCheckBox('1.6', self)
        self.channel_1_6.toggle()
        self.channel_1_6.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_1_7 = QtGui.QCheckBox('1.7', self)
        self.channel_1_7.toggle()
        self.channel_1_7.stateChanged.connect(self.parent.updateActiveChannels)

        self.channel_2_0 = QtGui.QCheckBox('2.0', self)
        self.channel_2_0.toggle()
        self.channel_2_0.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_1 = QtGui.QCheckBox('2.1', self)
        self.channel_2_1.toggle()
        self.channel_2_1.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_2 = QtGui.QCheckBox('2.2', self)
        self.channel_2_2.toggle()
        self.channel_2_2.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_3 = QtGui.QCheckBox('2.3', self)
        self.channel_2_3.toggle()
        self.channel_2_3.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_4 = QtGui.QCheckBox('2.4', self)
        self.channel_2_4.toggle()
        self.channel_2_4.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_5 = QtGui.QCheckBox('2.5', self)
        self.channel_2_5.toggle()
        self.channel_2_5.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_6 = QtGui.QCheckBox('2.6', self)
        self.channel_2_6.toggle()
        self.channel_2_6.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_2_7 = QtGui.QCheckBox('2.7', self)
        self.channel_2_7.toggle()
        self.channel_2_7.stateChanged.connect(self.parent.updateActiveChannels)

        self.channel_3_0 = QtGui.QCheckBox('3.0', self)
        self.channel_3_0.toggle()
        self.channel_3_0.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_1 = QtGui.QCheckBox('3.1', self)
        self.channel_3_1.toggle()
        self.channel_3_1.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_2 = QtGui.QCheckBox('3.2', self)
        self.channel_3_2.toggle()
        self.channel_3_2.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_3 = QtGui.QCheckBox('3.3', self)
        self.channel_3_3.toggle()
        self.channel_3_3.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_4 = QtGui.QCheckBox('3.4', self)
        self.channel_3_4.toggle()
        self.channel_3_4.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_5 = QtGui.QCheckBox('3.5', self)
        self.channel_3_5.toggle()
        self.channel_3_5.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_6 = QtGui.QCheckBox('3.6', self)
        self.channel_3_6.toggle()
        self.channel_3_6.stateChanged.connect(self.parent.updateActiveChannels)
        self.channel_3_7 = QtGui.QCheckBox('3.7', self)
        self.channel_3_7.toggle()
        self.channel_3_7.stateChanged.connect(self.parent.updateActiveChannels)

        ########## Server Connection Controls ##########

        # Editable text field used to define server IP address
        self.addressLabel = QtGui.QLabel('Server IP:', self)
        self.addressEdit = QtGui.QLineEdit()
        self.addressEdit.textChanged.connect(self.parent.daq.update_server_address)
        self.addressEdit.setText("192.168.211.18X")

        self.connectBtn = QtGui.QPushButton('Connect')
        self.connectBtn.clicked.connect(self.parent.daq.connect_to_server)

        self.disconnectBtn = QtGui.QPushButton('Disconnect')
        self.disconnectBtn.clicked.connect(self.parent.daq.disconnect_from_server)

        self.quitBtn = QtGui.QPushButton('Quit')
        self.quitBtn.clicked.connect(QtCore.QCoreApplication.instance().quit)

        self.dc = MyDynamicMplCanvas(self, width=10, height=4, dpi=100)

        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)

        self.grid.addWidget(self.dc, 0, 0, 8, 3)

        self.grid.addWidget(self.channelsLabel, 0, 4)

        self.grid.addWidget(self.channel_0_0, 1, 4)
        self.grid.addWidget(self.channel_0_1, 2, 4)
        self.grid.addWidget(self.channel_0_2, 3, 4)
        self.grid.addWidget(self.channel_0_3, 4, 4)
        self.grid.addWidget(self.channel_0_4, 5, 4)
        self.grid.addWidget(self.channel_0_5, 6, 4)
        self.grid.addWidget(self.channel_0_6, 7, 4)
        self.grid.addWidget(self.channel_0_7, 8, 4)

        self.grid.addWidget(self.channel_1_0, 1, 5)
        self.grid.addWidget(self.channel_1_1, 2, 5)
        self.grid.addWidget(self.channel_1_2, 3, 5)
        self.grid.addWidget(self.channel_1_3, 4, 5)
        self.grid.addWidget(self.channel_1_4, 5, 5)
        self.grid.addWidget(self.channel_1_5, 6, 5)
        self.grid.addWidget(self.channel_1_6, 7, 5)
        self.grid.addWidget(self.channel_1_7, 8, 5)

        self.grid.addWidget(self.channel_2_0, 1, 6)
        self.grid.addWidget(self.channel_2_1, 2, 6)
        self.grid.addWidget(self.channel_2_2, 3, 6)
        self.grid.addWidget(self.channel_2_3, 4, 6)
        self.grid.addWidget(self.channel_2_4, 5, 6)
        self.grid.addWidget(self.channel_2_5, 6, 6)
        self.grid.addWidget(self.channel_2_6, 7, 6)
        self.grid.addWidget(self.channel_2_7, 8, 6)

        self.grid.addWidget(self.channel_3_0, 1, 7)
        self.grid.addWidget(self.channel_3_1, 2, 7)
        self.grid.addWidget(self.channel_3_2, 3, 7)
        self.grid.addWidget(self.channel_3_3, 4, 7)
        self.grid.addWidget(self.channel_3_4, 5, 7)
        self.grid.addWidget(self.channel_3_5, 6, 7)
        self.grid.addWidget(self.channel_3_6, 7, 7)
        self.grid.addWidget(self.channel_3_7, 8, 7)

        self.grid.addWidget(self.addressLabel, 9, 0)
        self.grid.addWidget(self.addressEdit, 9, 1)
        self.grid.addWidget(self.connectBtn, 10, 0)
        self.grid.addWidget(self.disconnectBtn, 10, 1)
        self.grid.addWidget(self.quitBtn, 10, 2)
        
        self.setLayout(self.grid)

        self.show()

    def toggleConnectionButtons(self, connected):
        self.connectBtn.setEnabled(not connected)
        self.disconnectBtn.setEnabled(connected)
     

def main():
    
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()