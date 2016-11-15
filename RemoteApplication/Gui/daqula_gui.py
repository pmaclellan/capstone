import sys
import sip
sip.setapi('QVariant',2)
from PyQt4 import QtGui, uic, QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
import numpy as np
from pyqtgraph.ptime import time
import os
from datetime import datetime
import multiprocessing as mp
import threading
import Queue
import inspect


class MainWindow(QtGui.QMainWindow):
    def __init__(self, control_conn, data_receiver, filepath_sender,
                 readings_to_be_plotted_cond, filepath_available_cond,
                 control_msg_from_gui_cond, control_msg_from_nc_cond):
        super(MainWindow, self).__init__()
 
        # bidirectional mp.Connection for sending control protobuf messages and receiving ACKs
        self.control_conn = control_conn
  
        # mp.Connection for receiving raw data stream for plotting
        self.data_receiver = data_receiver
  
        # mp.Connection for sending directory to store binary files in to StorageController
        self.filepath_sender = filepath_sender
  
        # mp.Condition variable to wait on for new set of readings to be available to be plotted
        self.readings_to_be_plotted_cond = readings_to_be_plotted_cond
  
        # mp.Condition variable to notify StorageController that it should update its filepath
        self.filepath_available_cond = filepath_available_cond
  
        # mp.Condition variable for wait/notify on duplex control message connection GUI <--> NC
        self.control_msg_from_gui_cond = control_msg_from_gui_cond
        self.control_msg_from_nc_cond = control_msg_from_nc_cond
  
        # UI event handlers will place messages into this queue to be sent by control_send_thread
        self.send_queue = Queue.Queue()
        self.msg_to_be_sent_cond = threading.Condition()
  
        self.sequence = 0
        self.sequence_lock = threading.Lock()
  
        # sent_dict holds control messages that have been sent to NetworkController but not yet ACKed
        self.sent_dict = {}
        self.sent_dict_lock = threading.Lock()
  
        # worker threads for asynchronously sending and receiving start/stop messages to/from NC
        self.control_send_thread = threading.Thread(target=self.send_control_messages, args=[self.send_queue])
        self.control_send_thread.daemon = True
        self.control_recv_thread = threading.Thread(target=self.recv_control_messages)
        self.control_recv_thread.daemon = True
        self.control_send_thread.start()
        self.control_recv_thread.start()
        
        self.ui = uic.loadUi('Gui/DAQuLA.ui')
        self.settings = QSettings('Gui/settings.ini', QSettings.IniFormat)
        self.handle_load_config()
        
        self.checkBoxes = CheckBoxes(self)
        self.daq = DaqPlot(self)
        self.ui.show()
        
        #Connect buttons to functions
        self.ui.connectButton.clicked.connect(self.handle_connect)
        self.ui.saveConfig.clicked.connect(self.handle_save_config)
        self.ui.loadConfig.clicked.connect(self.handle_load_config)
        self.ui.selectDirButton.clicked.connect(self.selectDir)
        
        self.directory = os.path.dirname(__file__)
        if not os.path.exists(self.directory + "/Data"):
            os.makedirs(self.directory + "/Data")
        self.ui.fileEdit.setText(self.directory + "/Data")
        
        self.ui.serverIpEdit.setText("I am here")
        self.ui.serverPortEdit.setText("I am here")
        self.ui.sampleRateEdit.text()
        
        
    def handle_connect(self):        
        #get active channels
        numPlots = self.checkBoxes.numActive()
        if not numPlots:
            return
        
        self.daq.initPlot(numPlots)
        self.checkBoxes.lockBoxes()
        
        #send to Pete
        print self.checkBoxes.getActiveChannels()
        print self.ui.fileEdit.text()
        print self.ui.sampleRateEdit.text()

        # TODO: input validation
        self.filepath_sender.send(self.ui.fileEdit.text())
        with self.filepath_available_cond:
            self.filepath_available_cond.notify()

        # construct connect control message
        connect_msg = {}
        with self.sequence_lock:
            connect_msg['seq'] = self.sequence
            self.sequence += 1
        connect_msg['type'] = 'CONNECT'
        connect_msg['host'] = '10.42.0.2' # TODO: grab from UI field
        connect_msg['port'] = 10001 # TODO: grab from UI field
        connect_msg['channels'] = self.checkBoxes.generateChannelBitMask()
        connect_msg['rate'] = int(self.ui.sampleRateEdit.text())

        # put connect message in queue to be sent to NetworkController and notify sender thread
        self.send_queue.put(connect_msg)
        with self.msg_to_be_sent_cond:
            self.msg_to_be_sent_cond.notify()
        print "Connect Flag!"

        # TODO: show a 'connecting...' spinner

        # disable input until we get a reply message
        self.ui.connectButton.setEnabled(False)
        self.ui.fileEdit.setEnabled(False)
        self.ui.selectDirButton.setEnabled(False)
        self.ui.sampleRateEdit.setEnabled(False)
        self.ui.loadConfig.setEnabled(False)
        self.ui.saveConfig.setEnabled(False)
        
    def handle_disconnect(self):
        self.ui.connectButton.setText('Connect')
        self.daq.stopPlot()
        
        #send to Pete
        # construct disconnect control message
        disconnect_msg = {}
        with self.sequence_lock:
            disconnect_msg['seq'] = self.sequence
            self.sequence += 1
        disconnect_msg['type'] = 'DISCONNECT'

        # put disconnect message in queue to be sent to NetworkController and notify sender thread
        self.send_queue.put(disconnect_msg)
        with self.msg_to_be_sent_cond:
            self.msg_to_be_sent_cond.notify()
        print "Disconnect Flag!"

        # TODO: show a 'disconnecting...' spinner

        self.ui.connectButton.setEnabled(False)
        
    def handle_save_config(self):
        for name, obj in inspect.getmembers(self.ui):
            #if type(obj) is QComboBox:  # this works similar to isinstance, but missed some field... not sure why?
            if isinstance(obj, QComboBox):
                name   = obj.objectName()      # get combobox name
                index  = obj.currentIndex()    # get current index from combobox
                text   = obj.itemText(index)   # get the text for current index
                self.settings.setValue(name, text)   # save combobox selection to registry
                
            if isinstance(obj, QSpinBox):
                name = obj.objectName()
                value = obj.text()
                self.settings.setValue(name, value)
                
            if isinstance(obj, QLineEdit):
                name = obj.objectName()
                value = obj.text()
                self.settings.setValue(name, value)    # save ui values, so they can be restored next time
    
            if isinstance(obj, QCheckBox):
                name = obj.objectName()
                state = obj.checkState()
                self.settings.setValue(name, state)
    
    def handle_load_config(self):
        for name, obj in inspect.getmembers(self.ui):
            if isinstance(obj, QComboBox):
                index  = obj.currentIndex()    # get current region from combobox
                #text   = obj.itemText(index)   # get the text for new selected index
                name   = obj.objectName()
    
                value = unicode(self.settings.value(name))  
    
                if value == "":
                    continue
    
                index = obj.findText(value)   # get the corresponding index for specified string in combobox
    
                if index == -1:  # add to list if not found
                    obj.insertItems(0,[value])
                    index = obj.findText(value)
                    obj.setCurrentIndex(index)
                else:
                    obj.setCurrentIndex(index)   # preselect a combobox value by index    
    
            if isinstance(obj, QLineEdit):
                name = obj.objectName()
                value = unicode(self.settings.value(name))  # get stored value from registry
                obj.setText(value)  # restore lineEditFile
                
            if isinstance(obj, QSpinBox):
                name = obj.objectName()
                value = unicode(self.settings.value(name))
                obj.setValue(int(value))
    
            if isinstance(obj, QCheckBox):
                name = obj.objectName()
                value = self.settings.value(name)   # get stored value from registry
                if value != None:
                    obj.setCheckState(int(value))   # restore checkbox
    
    def selectDir(self):
        saveDir = QFileDialog.getExistingDirectory(directory = self.directory)
        if (saveDir):
            self.ui.fileEdit.setText(saveDir)

    # control_send_thread target
    def send_control_messages(self, *args):
        send_queue = args[0]
        while True:
            if not send_queue.empty():
                msg = send_queue.get()
                self.control_conn.send(msg)
                with self.control_msg_from_gui_cond:
                    self.control_msg_from_gui_cond.notify()
                with self.sent_dict_lock:
                    self.sent_dict[msg['seq']] = msg
            else:
                with self.msg_to_be_sent_cond:
                    self.msg_to_be_sent_cond.wait()

    def recv_control_messages(self):
        while True:
            if self.control_conn.poll():
                response = self.control_conn.recv()
                with self.sent_dict_lock:
                    if response['seq'] in self.sent_dict.keys():
                        self.sent_dict.pop(response['seq'])
                        print 'GUI: received reply from NC, %s' % response
                        # TODO: dear god please put this stuff into helper functions
                        if response['type'] == 'CONNECT':
                            if response['success'] == True:
                                self.ui.connectButton.setText('Disconnect')
                                self.ui.connectButton.clicked.disconnect()
                                self.ui.connectButton.clicked.connect(self.handle_disconnect)
                                self.ui.connectButton.setEnabled(True)
                                self.ui.fileEdit.setEnabled(False)
                                self.ui.selectDirButton.setEnabled(False)
                                self.ui.sampleRateEdit.setEnabled(False)
                                self.ui.loadConfig.setEnabled(False)
                                self.ui.saveConfig.setEnabled(False)
                                self.checkBoxes.lockBoxes()
                            else:
                                self.ui.connectButton.setText('Connect')
                                self.ui.connectButton.clicked.disconnect()
                                self.ui.connectButton.clicked.connect(self.handle_connect)
                                self.ui.connectButton.setEnabled(True)
                                self.ui.fileEdit.setEnabled(True)
                                self.ui.selectDirButton.setEnabled(True)
                                self.ui.sampleRateEdit.setEnabled(True)
                                self.ui.loadConfig.setEnabled(True)
                                self.ui.saveConfig.setEnabled(True)
                                self.checkBoxes.unlockBoxes()

                        elif response['type'] == 'DISCONNECT':
                            if response['success'] == True:
                                self.ui.connectButton.setText('Connect')
                                self.ui.connectButton.clicked.disconnect()
                                self.ui.connectButton.clicked.connect(self.handle_connect)
                                self.ui.connectButton.setEnabled(True)
                                self.ui.fileEdit.setEnabled(True)
                                self.ui.selectDirButton.setEnabled(True)
                                self.ui.sampleRateEdit.setEnabled(True)
                                self.ui.loadConfig.setEnabled(True)
                                self.ui.saveConfig.setEnabled(True)
                                self.checkBoxes.unlockBoxes()
                            else:
                                self.ui.connectButton.setText('Disconnect')
                                self.ui.connectButton.clicked.disconnect()
                                self.ui.connectButton.clicked.connect(self.handle_disconnect)
                                self.ui.connectButton.setEnabled(True)
                                self.ui.fileEdit.setEnabled(False)
                                self.ui.selectDirButton.setEnabled(False)
                                self.ui.sampleRateEdit.setEnabled(False)
                                self.ui.loadConfig.setEnabled(False)
                                self.ui.saveConfig.setEnabled(False)
                                self.checkBoxes.lockBoxes()
                        # self.showResultMessage(response)
                    else:
                        raise RuntimeWarning('unexpected message received from NetworkController')
            else:
                with self.control_msg_from_nc_cond:
                    self.control_msg_from_nc_cond.wait()

    # def showResultMessage(self, message):
    #     msg = QMessageBox()
    #     if message['success']:
    #         msg.setIcon(QMessageBox.Information)
    #         msg.setText("Success!")
    #         msg.setWindowTitle("Action Succeeded")
    #         msg.setInformativeText(message['message'])
    #     else:
    #         msg.setIcon(QMessageBox.Critical)
    #         msg.setText("Failure!")
    #         msg.setWindowTitle("Action Failed")
    #         msg.setInformativeText(message['message'])
    #
    #     msg.setStandardButtons(QMessageBox.Ok)

        
#     def showdialog(self):
#         msg = QMessageBox()
#         msg.setIcon(QMessageBox.Information)
#         
#         msg.setText(os.path.basename(str(self.ui.fileEdit.text())) + " already exists!")
#         msg.setInformativeText("Are you sure you want to overwrite this file?")
#         msg.setWindowTitle("Warning!")
#         msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
#         msg.buttonClicked.connect(self.msgbtn)
#         msg.exec_()
#     
#     def msgbtn(self, i):
#         if (i.text() == "&No"):
#             fileUpdated = self.selectFile()
#             if not fileUpdated:
#                 self.cancel = True
        
class DaqPlot:
    def __init__(self, parent):
        self.parent = parent
        self.parent.ui.daqPlot.setLabel('bottom', 'Index', units='B')
        
    def initPlot(self, numPlots):
        self.nPlots = numPlots
        self.nSamples = 500
        self.curves = []
        for i in range(self.nPlots):
            c = pg.PlotCurveItem(pen=(i,self.nPlots*1.3))
            self.parent.ui.daqPlot.addItem(c)
            c.setPos(0,i*6)
            self.curves.append(c)
        self.parent.ui.daqPlot.setYRange(0, self.nPlots*6)
        self.parent.ui.daqPlot.setXRange(0, self.nSamples)
        self.parent.ui.daqPlot.resize(600,900)
        self.x = np.linspace(-8*np.pi, 8*np.pi, 500)
        self.data = np.sin(self.x)
        #self.data = np.random.normal(size=(self.nPlots*23,self.nSamples))
        self.ptr = 0
        self.lastTime = time()
        self.fps = None
        self.count = 0
        if self.fps is None:
            self.fps = 1.0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0)
        
    def stopPlot(self):
        for i in range(self.nPlots):
            self.curves[i].clear()
        self.timer.stop()
#    def activeChannels(self):
#        self.parent.ui
        
    def update(self):
        self.count += 1
        #print "---------", count
        for i in range(self.nPlots):
            #self.curves[i].setData(self.data[(self.ptr+i)%self.data.shape[0]])
            self.curves[i].setData(0.25*np.sin(180*np.pi*self.x)*self.fps)

        #print "   setData done."
        self.ptr += self.nPlots
        now = time()
        self.x = np.linspace(self.lastTime, now, 500)
        dt = now - self.lastTime
        self.lastTime = now
        if self.fps is None:
            self.fps = 1.0/dt
        else:
            s = np.clip(dt*3., 0, 1)
            self.fps = self.fps * (1-s) + (1.0/dt) * s
        self.parent.ui.daqPlot.setTitle('%0.2f fps' % self.fps)

class CheckBoxes:
    def __init__(self, parent):
        self.parent = parent
        self.cb00 = parent.ui.cb_ch_0_0
        self.cb01 = parent.ui.cb_ch_0_1
        self.cb02 = parent.ui.cb_ch_0_2
        self.cb03 = parent.ui.cb_ch_0_3
        self.cb04 = parent.ui.cb_ch_0_4
        self.cb05 = parent.ui.cb_ch_0_5
        self.cb06 = parent.ui.cb_ch_0_6
        self.cb07 = parent.ui.cb_ch_0_7
        self.cb10 = parent.ui.cb_ch_1_0
        self.cb11 = parent.ui.cb_ch_1_1
        self.cb12 = parent.ui.cb_ch_1_2
        self.cb13 = parent.ui.cb_ch_1_3
        self.cb14 = parent.ui.cb_ch_1_4
        self.cb15 = parent.ui.cb_ch_1_5
        self.cb16 = parent.ui.cb_ch_1_6
        self.cb17 = parent.ui.cb_ch_1_7
        self.cb20 = parent.ui.cb_ch_2_0
        self.cb21 = parent.ui.cb_ch_2_1
        self.cb22 = parent.ui.cb_ch_2_2
        self.cb23 = parent.ui.cb_ch_2_3
        self.cb24 = parent.ui.cb_ch_2_4
        self.cb25 = parent.ui.cb_ch_2_5
        self.cb26 = parent.ui.cb_ch_2_6
        self.cb27 = parent.ui.cb_ch_2_7
        self.cb30 = parent.ui.cb_ch_3_0
        self.cb31 = parent.ui.cb_ch_3_1
        self.cb32 = parent.ui.cb_ch_3_2
        self.cb33 = parent.ui.cb_ch_3_3
        self.cb34 = parent.ui.cb_ch_3_4
        self.cb35 = parent.ui.cb_ch_3_5
        self.cb36 = parent.ui.cb_ch_3_6
        self.cb37 = parent.ui.cb_ch_3_7
        self.enableAll = self.parent.ui.enableAll
        self.disableAll = self.parent.ui.disableAll
        
        self.enableAll.clicked.connect(self.checkAllBoxes)
        self.disableAll.clicked.connect(self.uncheckAllBoxes)
        
        self.boxes = [self.cb00, self.cb01, self.cb02, self.cb03, self.cb04, self.cb05, self.cb06, self.cb07, self.cb10, self.cb11, self.cb12, self.cb13, self.cb14, self.cb15, self.cb16, self.cb17, self.cb20, self.cb21, self.cb22, self.cb23, self.cb24, self.cb25, self.cb26, self.cb27, self.cb30, self.cb31, self.cb32, self.cb33, self.cb34, self.cb35, self.cb36, self.cb37]
        self.channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7']
        self.activeChannels = self.getActiveChannels()
    
    def checkAllBoxes(self):
        for i in range(len(self.boxes)):
            self.boxes[i].setCheckState(2)
            
    def uncheckAllBoxes(self):
        for i in range(len(self.boxes)):
            self.boxes[i].setCheckState(0)
    
    def getActiveChannels(self):
        active = []
        for i in range(len(self.boxes)):
            if self.boxes[i].isChecked():
                active.append(self.channels[i])
        return active

    def generateChannelBitMask(self):
        active = self.getActiveChannels()

        bit_mask = np.uint32(0)
        offset = 0
        for i in range(4):
            for j in range(8):
                if (str(i) + '.' + str(j)) in active:
                    # bit_mask |= 0x01 << offset
                    bit_mask = np.bitwise_or(bit_mask, np.left_shift(np.uint32(1), offset))
                else:
                    # bit_mask &= ~(0x01 << offset)
                    bit_mask = np.bitwise_and(bit_mask, np.bitwise_not(np.left_shift(np.uint32(1), offset)))
                offset += 1
        return bit_mask
            
    def lockBoxes(self):
        self.enableAll.setEnabled(False)
        self.disableAll.setEnabled(False)
        
        for i in range(len(self.boxes)):
            self.boxes[i].setEnabled(False)
            
    def unlockBoxes(self):
        self.enableAll.setEnabled(True)
        self.disableAll.setEnabled(True)
        
        for i in range(len(self.boxes)):
            self.boxes[i].setEnabled(True)
    
    def numActive(self):
        count = 0
        for i in range(len(self.boxes)):
            if self.boxes[i].isChecked():
                count = count + 1
        return count
    
    def checked(self):
        if self.cb00.checkState() == 0:
            #self.parent.daq.nPlots = self.parent.daq.nPlots - 1
            self.parent.ui.daqPlot.removeItem(self.parent.daq.curves[2])
        if self.cb00.checkState() == 2:
            #self.parent.daq.nPlots = self.parent.daq.nPlots + 1
            self.parent.ui.daqPlot.addItem(self.parent.daq.curves[2])


# if __name__ == "__main__":
#     ## Always start by initializing Qt (only once per application)
#     app = QtGui.QApplication(sys.argv)
#     window = MainWindow()
#     sys.exit(app.exec_())
