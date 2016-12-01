import sip
sip.setapi('QVariant',2)
from PyQt4 import uic
from PyQt4.QtCore import QThread, QTimer, QObject, pyqtSignal, QSettings
from PyQt4.QtGui import *
import pyqtgraph as pg
import numpy as np
from pyqtgraph.ptime import time
import os
import multiprocessing as mp
import threading
import Queue
import inspect
import logging
import time as realtime


class MainWindow(QMainWindow):
    def __init__(self, control_conn, data_queue, filepath_sender,
                 readings_to_be_plotted_event, filepath_available_event,
                 control_msg_from_gui_event, control_msg_from_nc_event):
        super(MainWindow, self).__init__()
 
        # bidirectional mp.Connection for sending control protobuf messages and receiving ACKs
        self.control_conn = control_conn
  
        # mp.Connection for receiving raw data stream for plotting
        self.data_queue = data_queue
  
        # mp.Connection for sending directory to store binary files in to StorageController
        self.filepath_sender = filepath_sender
  
        # mp.Event variable to wait on for new set of readings to be available to be plotted
        self.readings_to_be_plotted_event = readings_to_be_plotted_event
  
        # mp.Event variable to notify StorageController that it should update its filepath
        self.filepath_available_event = filepath_available_event
  
        # mp.Event variable for wait/notify on duplex control message connection GUI <--> NC
        self.control_msg_from_gui_event = control_msg_from_gui_event
        self.control_msg_from_nc_event = control_msg_from_nc_event

        self.stop_event = mp.Event()
  
        # UI event handlers will place messages into this queue to be sent by control_send_thread
        self.send_queue = Queue.Queue()
        self.msg_to_be_sent_event = threading.Event()
  
        self.sequence = 0
        self.sequence_lock = threading.Lock()

        # holds Unix timestamp sent from MicroZed that corresponds to the first sample time
        self.start_time = 0
 
        # sent_dict holds control messages that have been sent to NetworkController but not yet ACKed
        self.sent_dict = {}
        self.sent_dict_lock = threading.Lock()
  
        # worker threads for asynchronously sending and receiving start/stop messages to/from NC
        self.control_send_thread = threading.Thread(target=self.send_control_messages, args=[self.send_queue])
        self.control_send_thread.daemon = True
        self.control_recv_thread = QThread()
        # self.control_recv_thread.start()
        self.control_send_thread.start()

        # used to signal data thread to stop
        self.stop_event = threading.Event()

        self.ui = uic.loadUi('Gui/DAQuLA.ui')
        self.settings = QSettings('Gui/settings.ini', QSettings.IniFormat)
        self.handle_load_config()
        
        self.checkBoxes = CheckBoxes(self)
        self.checkBoxes.lockBoxes()
        self.daq = DaqPlot(self)
        self.ui.show()
        
        #Connect buttons to functions
        self.ui.connectButton.clicked.connect(self.handle_connect)
        self.ui.saveConfig.clicked.connect(self.handle_save_config)
        self.ui.loadConfig.clicked.connect(self.handle_load_config)
        self.ui.selectDirButton.clicked.connect(self.selectDir)
        
        self.directory = os.path.dirname(__file__)
        if not os.path.exists(self.directory + '/output'):
            os.makedirs(self.directory + '/output')
        self.ui.fileEdit.setText(self.directory + '/output')
       
        self.ui.serverIpEdit.setText('10.42.0.2')
        self.ui.serverPortEdit.setText('10001')       
        
    def handle_connect(self):        
        #get active channels
        numPlots = self.checkBoxes.numActive()
        if not numPlots:
            return
        
        self.daq.initPlot(numPlots)

        # TODO: input validation
        self.filepath_sender.send(str(self.ui.fileEdit.text()))
        self.filepath_available_event.set()

        # construct connect control message
        connect_msg = {}
        with self.sequence_lock:
            connect_msg['seq'] = self.sequence
            self.sequence += 1
        connect_msg['type'] = 'CONNECT'
        connect_msg['host'] = str(self.ui.serverIpEdit.text())
        connect_msg['port'] = int(self.ui.serverPortEdit.text())
        connect_msg['channels'] = self.checkBoxes.generateChannelBitMask()
        connect_msg['rate'] = int(self.ui.sampleRateEdit.text())

        self.enterWaitState()
        self.msg_recv_thread = MessageReceiverThread(self.control_conn, self.control_msg_from_nc_event)
        self.msg_recv_thread.responseReceived.connect(self.handle_connect_state)
        self.msg_recv_thread.start()
        # put connect message in queue to be sent to NetworkController and notify sender thread
        self.send_queue.put(connect_msg)
        self.msg_to_be_sent_event.set()
        # TODO: show a 'connecting...' spinner

    def handle_connect_state(self, response):
        if response['success'] == True:
            self.enterConnectedState()
        else:
            self.exitWaitState()
        self.showResultMessage(response)

    def handle_disconnect_state(self, response):
        if response['success'] == True:
            self.exitConnectedState()
        else:
            self.enterConnectedState()
        self.showResultMessage(response)

    def handle_disconnect(self):
        self.ui.connectButton.setText('Connect')
        self.daq.stopPlot()

        # construct disconnect control message
        disconnect_msg = {}
        with self.sequence_lock:
            disconnect_msg['seq'] = self.sequence
            self.sequence += 1
        disconnect_msg['type'] = 'DISCONNECT'

        self.enterWaitState()
        self.msg_recv_thread = MessageReceiverThread(self.control_conn, self.control_msg_from_nc_event)
        self.msg_recv_thread.responseReceived.connect(self.handle_disconnect_state)
        self.msg_recv_thread.start()

        # put disconnect message in queue to be sent to NetworkController and notify sender thread
        self.send_queue.put(disconnect_msg)
        self.msg_to_be_sent_event.set()
        # TODO: show a 'disconnecting...' spinner
      
    def enterWaitState(self):
        print 'wait state entered'
        self.checkBoxes.lockBoxes()
        self.ui.connectButton.setEnabled(False)
        self.ui.fileEdit.setEnabled(False)
        self.ui.selectDirButton.setEnabled(False)
        self.ui.sampleRateEdit.setEnabled(False)
        self.ui.loadConfig.setEnabled(False)
        self.ui.saveConfig.setEnabled(False)
        print 'UI updated'

    def exitWaitState(self):
        print 'wait state exited'
        self.checkBoxes.unlockBoxes()
        self.ui.connectButton.setEnabled(True)
        self.ui.fileEdit.setEnabled(True)
        self.ui.selectDirButton.setEnabled(True)
        self.ui.sampleRateEdit.setEnabled(True)
        self.ui.loadConfig.setEnabled(True)
        self.ui.saveConfig.setEnabled(True)
        print 'UI updated'

    def enterConnectedState(self):
        print 'connected state entered'
        self.checkBoxes.lockBoxes()
        self.ui.connectButton.clicked.disconnect()
        self.ui.connectButton.setText('Disconnect')
        self.ui.connectButton.clicked.connect(self.handle_disconnect)
        # TODO: make a disconnect button instead
        self.ui.connectButton.setEnabled(True)
        self.ui.fileEdit.setEnabled(False)
        self.ui.selectDirButton.setEnabled(False)
        self.ui.sampleRateEdit.setEnabled(False)
        self.ui.loadConfig.setEnabled(False)
        self.ui.saveConfig.setEnabled(True)
        print 'UI updated'

    def exitConnectedState(self):
        print 'connected state exited'
        self.checkBoxes.unlockBoxes()
        self.ui.connectButton.clicked.disconnect()
        self.ui.connectButton.clicked.connect(self.handle_connect)
        self.ui.connectButton.setEnabled(True)
        self.ui.fileEdit.setEnabled(True)
        self.ui.selectDirButton.setEnabled(True)
        self.ui.sampleRateEdit.setEnabled(True)
        self.ui.loadConfig.setEnabled(True)
        self.ui.saveConfig.setEnabled(True)
        print 'UI updated'

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
        if not os.path.isfile('Gui/settings.ini'):
            return
            
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
        while not self.stop_event.is_set():
            if not send_queue.empty():
                msg = send_queue.get()
                print 'sending control message %s' % msg
                self.control_conn.send(msg)
                self.control_msg_from_gui_event.set()
            else:
                while not self.stop_event.is_set():
                    if self.msg_to_be_sent_event.wait(1.0):
                        self.msg_to_be_sent_event.clear()
                        break
   
    def showResultMessage(self, message):
        msg = QMessageBox()
        if message['success']:
            msg.setIcon(QMessageBox.Information)
            msg.setText("Success!")
            msg.setWindowTitle("Success")
            msg.setInformativeText(message['message'])
            msg.exec_()
        else:
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Failure!")
            msg.setWindowTitle("Action Failed!")
            msg.setInformativeText(message['message'])
            msg.exec_()

class MessageReceiverThread(QThread):

    responseReceived = pyqtSignal(dict, name='responseReceived')

    def __init__(self, control_conn, control_msg_from_nc_event):
        QThread.__init__(self)
        self.control_conn = control_conn
        self.control_msg_from_nc_event = control_msg_from_nc_event

    def run(self):
        while True:
            if self.control_conn.poll():
                response = self.control_conn.recv()
                # response = {'foo' : 123}
                logging.debug('GUI: received reply from NC, %s', response)
                self.responseReceived.emit(response)
                break
            else:
                self.control_msg_from_nc_event.wait()
                self.control_msg_from_nc_event.clear()

class DaqPlot:
    def __init__(self, parent):
        self.parent = parent
        self.parent.ui.daqPlot.setLabel('bottom', 'Index', units='B')
        
    def initPlot(self, numPlots):
        self.dataToPlot = [[]for i in range(numPlots)]
        self.nPlots = numPlots
        self.nSamples = 150
        self.curves = []
        for i in range(numPlots):
            # c = pg.PlotCurveItem(pen=(i,numPlots*1.3))
            c = pg.PlotCurveItem(pen='g')
            self.parent.ui.daqPlot.addItem(c)
            c.setPos(0,i*10)
            self.curves.append(c)
        self.parent.ui.daqPlot.setYRange(-5, 10*numPlots-5)
        self.parent.ui.daqPlot.setXRange(0, self.nSamples)
        self.parent.ui.daqPlot.resize(600,900)
        self.ptr = 0
        self.lastTime = time()
        self.fps = None
        self.count = 0
        if self.fps is None:
            self.fps = 1.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0)
        
    def stopPlot(self):
        for i in range(self.nPlots):
            self.curves[i].clear()
        self.timer.stop()
#    def activeChannels(self):
#        self.parent.ui
        
    def update(self):
        if not self.parent.data_queue.empty():
            reading = [self.parent.data_queue.get()]
            [[self.dataToPlot[(j-16)/2].append((float(reading[i][j] + (reading[i][j+1] << 8))/6553.6)-5) for i in range(0,len(reading))] for j in range(16,len(reading[0]),2)]
            
            if len(self.dataToPlot[0]) >= self.nSamples:
                self.count += 1
                for i in range(self.nPlots):
                    self.curves[i].setData(self.dataToPlot[i])
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
                self.dataToPlot = [[] for i in range(self.nPlots)]

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
