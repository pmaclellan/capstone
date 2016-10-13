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
    # def listen_for_data(self):
    #     while True:
    #         if self.sock:
    #             incoming_buffer = bytearray(b" " * 512) # create "empty" buffer to store incoming data
    #             self.sock.recv_into(incoming_buffer)
    #             i = 0
    #             tic = time.time()
    #             while i < len(incoming_buffer) and incoming_buffer[i] != b' ':
    #                 # convert each byte to binary strings and combine into one 16-bit string
    #                 binary = '{:08b}'.format(incoming_buffer[i + 1]) + '{:08b}'.format(incoming_buffer[i])
    #                 # convert 16-bit string to int
    #                 received = int(binary, base=2)
    #                 # add new value to queue to be processed by graph
    #                 self.queue.put(received)
    #                 if self.queue.qsize() % 1024 == 0:
    #                     avg_bit_time = (time.time() - tic) * 16
    #                     print("Bitrate: %.2f kbps" % (1 / avg_bit_time))
    #                     self.sig.new_data.emit(1 / avg_bit_time)
    #                 # increment by 2 bytes each time to account for uint16_t type
    #                 i += 2
    #
    #                 # TCP Receiver thread

    def listen_for_data(self):
        synchronized = False
        temp_buffer = []
        temp_byte = '00000000'
        readings = {}
        #TODO: read active channels upon connecting to server
        active_channels = ['0.0', '0.1', '0.2', '0.3',
                           '1.0', '1.1', '1.2', '1.3',
                           '2.0', '2.1', '2.2', '2.3',
                           '3.0', '3.1', '3.2', '3.3',
                           '4.0', '4.1', '4.2', '4.3',
                           '5.0', '5.1', '5.2', '5.3',
                           '6.0', '6.1', '6.2', '6.3',
                           '7.0', '7.1', '7.2', '7.3']
        block_offset = 0 # which reading we are currently expecting: 0 -> (n-1) **NOTE: DEAD and TS not counted
        n = 32 # number of channels, will be sent as a parameter
        while True:
            if self.sock:
                incoming_buffer = bytearray(b" " * 512)  # create "empty" buffer to store incoming data
                self.sock.recv_into(incoming_buffer)
                i = 0
                while i+1 < len(incoming_buffer) and incoming_buffer[i+1] != b' ':
                    # convert each byte to binary strings
                    byte1 = '{:08b}'.format(incoming_buffer[i + 1])
                    byte2 = '{:08b}'.format(incoming_buffer[i])
                    binary = byte1 + byte2
                    value = int(binary, base=2)
                    if not synchronized:
                        if byte1 == '11011110': # 0xDE
                            if byte2 == '10101101': # 0xAD
                                # we found a DEAD, let's see if it aligns with a previous DEAD
                                if len(temp_buffer) >= (n + 2) and temp_buffer[-1 * (n + 2)] == 57005: # 0xDEAD
                                    synchronized = True
                                    # flush the buffer to only include the new DEAD
                                    temp_buffer = [value]
                                    temp_buffer.append(0) # TODO: placeholder for timestamp
                                    # reset readings just to be sure
                                    readings = {}
                                    i += 4 #just skip over the timestamp bytes for now
                                    continue
                                else:
                                    # not in sync yet, store in buffer
                                    temp_buffer.append(value)
                                    i += 2
                                    continue
                            else:
                                # no DEAD here, move along
                                temp_buffer.append(value)
                        elif byte2 == '11011110': # 0xDE
                            # carry = True
                            if temp_byte == '10101101': # 0xAD where temp_byte is the byte1 from the prev iteration
                                # we found a DEAD, but we're misaligned by one byte
                                # reconstruct binary string with the DEAD together
                                binary = byte2 + temp_byte
                                value = int(binary, base=2)
                                temp_buffer.append(value)
                                i += 1 # only move ahead by one byte to realign ourselves
                                # We can't be sure we're back in sync yet, need to wait until the next DEAD
                                continue
                            else:
                                temp_buffer.append(value)
                                i += 2
                                continue
                        else:
                            # we've got nothing, throw it in the buffer and better luck next time
                            temp_buffer.append(value)
                            i += 2
                            # but wait, let's save byte1 in case we're off by one...
                            temp_byte = byte1
                            continue

                    elif synchronized:
                        if value == 57005: # 0xDEAD
                            if len(temp_buffer) >= (n + 2) and temp_buffer[-1 * (n + 2)]:
                                # all good, still synced up
                                temp_buffer = [value] # flush the buffer
                                temp_buffer.append(0) # TODO: placeholder for timestamp
                                block_offset = 0
                                i += 4 #skip the timestamp bytes for now
                                continue
                            else:
                                # well fuck, we're either out of sync or happened to read a DEAD
                                synchronized = False
                                temp_buffer.append(value)
                                i += 2
                                continue
                        else:
                            readings[active_channels[block_offset]] = value
                            i += 2
                            block_offset += 1
                            if block_offset >= n:
                                write_to_queue(readings) # TODO: define new queue that holds dictionaries
                                readings = {} # clear readings before starting next block
                            continue

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