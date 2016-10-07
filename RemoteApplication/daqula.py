#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import socket
import threading
import Queue
import time
import random
from PyQt4 import QtGui, QtCore
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class CustomSignal(QtCore.QObject):

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()
    new_data = QtCore.pyqtSignal(float)


class DaqConnection:
    def __init__(self, parent):
        self.parentWindow = parent
        self.queue = Queue.Queue()
        self.sig = CustomSignal()
        self.sig.connected.connect(lambda: self.parentWindow.setStatusBarMessage('Connected'))
        self.sig.connected.connect(lambda: self.parentWindow.daqWidget.toggleConnectionButtons(self.connected))
        self.sig.disconnected.connect(lambda: self.parentWindow.setStatusBarMessage('Disconnected'))
        self.sig.disconnected.connect(lambda: self.parentWindow.daqWidget.toggleConnectionButtons(self.connected))
        self.sig.new_data.connect(self.parentWindow.forward_to_plot)
        self.connected = False
        self.server_address = ('localhost', 10001)

    def update_server_address(self, string):
        self.server_address = string, 10001

    def connect_to_server(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print('connecting to %s port %s' % self.server_address)
        try:
            self.sock.connect(self.server_address)
            self.connected = True
            self.sig.connected.emit()
            self.receiver_thread = threading.Thread(target=self.listen_for_data)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()
        except Exception, e:
            print("Something's wrong with %s. Exception type is %s" % (self.server_address, e))
            self.parentWindow.setStatusBarMessage("Unable to connect to server at %s:%s" % self.server_address)

    def disconnect_from_server(self):
        if self.sock is not None:
            self.sock.close()
            self.connected = False
            self.sig.disconnected.emit()

    # TCP Receiver thread
    def listen_for_data(self):
        while True:
            if self.sock:
                incoming_buffer = bytearray(b" " * 512) # create "empty" buffer to store incoming data
                self.sock.recv_into(incoming_buffer)
                i = 0
                tic = time.time()
                while i < len(incoming_buffer) and incoming_buffer[i] != b' ':
                    # convert each byte to binary strings and combine into one 16-bit string
                    binary = '{:08b}'.format(incoming_buffer[i + 1]) + '{:08b}'.format(incoming_buffer[i])
                    # convert 16-bit string to int
                    received = int(binary, base=2)
                    # add new value to queue to be processed by graph
                    self.queue.put(received)
                    if self.queue.qsize() % 1024 == 0:
                        avg_bit_time = (time.time() - tic) * 16
                        print("Bitrate: %.2f kbps" % (1 / avg_bit_time))
                        self.sig.new_data.emit(1 / avg_bit_time)
                    # increment by 2 bytes each time to account for uint16_t type
                    i += 2

    def yield_data_point(self):
        if not self.queue.empty():
          yield self.queue.get()
        else:
          print("No more data!")

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initClient()
        self.daqWidget = DaqWidget(self)
        self.setCentralWidget(self.daqWidget)
        self.initUI()
        
    def initClient(self):
        self.daq = DaqConnection(self)

    def initUI(self):               
        self.statusBar().showMessage('Not Connected')
        self.setGeometry(300, 300, 350, 300)
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
        timer.start(1000)
        self.queue = Queue.Queue()

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        # l = [random.randint(0, 10) for i in range(4)]
        l = []
        for i in range(10):
            if not self.queue.empty():
                l.append(self.queue.get())

        self.axes.plot(range(len(l)), l, 'r')
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

        self.dc = MyDynamicMplCanvas(self, width=5, height=4, dpi=100)

        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)

        self.grid.addWidget(self.dc, 1, 0)
        self.grid.addWidget(self.addressLabel, 2, 0)
        self.grid.addWidget(self.addressEdit, 2, 1)
        self.grid.addWidget(self.connectBtn, 3, 0)
        self.grid.addWidget(self.disconnectBtn, 3, 1)
        self.grid.addWidget(self.quitBtn, 3, 2)
        
        self.setLayout(self.grid)
        
        # self.setGeometry(300, 300, 350, 300)
        # self.setWindowTitle('Review')    
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