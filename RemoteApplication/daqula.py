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
        self.addressLabel = QtGui.QLabel('Server IP:', self)
        # Editable text field used to define server IP address
        self.addressEdit = QtGui.QLineEdit()
        self.addressEdit.textChanged.connect(self.parent.daq.update_server_address)
        self.addressEdit.setText("localhost")

        self.connectBtn = QtGui.QPushButton('Connect')
        self.connectBtn.clicked.connect(self.parent.daq.connect_to_server)

        self.disconnectBtn = QtGui.QPushButton('Disconnect')
        self.disconnectBtn.clicked.connect(self.parent.daq.disconnect_from_server)

        self.quitBtn = QtGui.QPushButton('Quit')
        self.quitBtn.clicked.connect(QtCore.QCoreApplication.instance().quit)

        self.dc = MyDynamicMplCanvas(self, width=10, height=4, dpi=100)

        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)

        self.grid.addWidget(self.dc, 1, 0)
        self.grid.addWidget(self.addressLabel, 2, 0)
        self.grid.addWidget(self.addressEdit, 2, 1)
        self.grid.addWidget(self.connectBtn, 3, 0)
        self.grid.addWidget(self.disconnectBtn, 3, 1)
        self.grid.addWidget(self.quitBtn, 3, 2)
        
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