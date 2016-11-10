import sys
from PyQt4 import QtGui, uic, QtCore, QtGui
from PyQt4.QtCore import QObject, pyqtSlot
from PyQt4.QtGui import QFileDialog, QMessageBox
import pyqtgraph as pg
import Queue
import numpy as np
from pyqtgraph.ptime import time
import os
from datetime import datetime

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.ui = uic.loadUi("DAQuLA.ui")
        self.checkBoxes = CheckBoxes(self)
        self.daq = DaqPlot(self)
        self.ui.show()
        self.ui.connectButton.clicked.connect(self.connect)
        
        self.directory = os.path.dirname(__file__)
        self.fileTimestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        if not os.path.exists(self.directory + "\Data"):
            os.makedirs(self.directory + "\Data")
        self.ui.selectFileButton.clicked.connect(self.selectFile)
        self.ui.fileEdit.setText(self.directory + "\Data\\" + self.fileTimestamp + ".h5")
#        self.cancel = False #used for stopping plotting process
        #self.ui.fileEdit.setText(QFileDialog.getSaveFileName(directory = self.directory + "\Data", filter = "*.h5"))

        
    def connect(self):
        #if selected file doesn't exist yet, make it
        if not os.path.isfile(self.ui.fileEdit.text()):
            open( str(self.ui.fileEdit.text()), 'a').close()
        
        #get active channels
        numPlots = self.checkBoxes.numActive()
        if not numPlots:
            return
        
        self.daq.initPlot(numPlots)
        self.checkBoxes.lockBoxes()
        
        #send to Pete
        print self.checkBoxes.getActiveChannels()
        print self.ui.fileEdit.text()
        print self.ui.sampleRate.text()
        print "Connect Flag!"
        
        
        self.ui.connectButton.setText('Disconnect')
        self.ui.connectButton.clicked.disconnect()
        self.ui.connectButton.clicked.connect(self.disconnect)
        self.ui.fileEdit.setEnabled(False)
        self.ui.selectFileButton.setEnabled(False)
        self.ui.sampleRate.setEnabled(False)
        
    def disconnect(self):
        self.ui.connectButton.setText('Connect')
        self.daq.stopPlot()
        
        #send to Pete
        print "Disconnect Flag!"
        
        self.ui.connectButton.clicked.disconnect()
        self.ui.connectButton.clicked.connect(self.connect)
        self.checkBoxes.unlockBoxes()
        self.ui.fileEdit.setEnabled(True)
        self.ui.selectFileButton.setEnabled(True)
        self.ui.sampleRate.setEnabled(True)
    
    def selectFile(self):
        saveFile = QFileDialog.getSaveFileName(directory = self.directory + "\Data", filter = "*.h5")
        if (saveFile):
            self.ui.fileEdit.setText(saveFile)
            open( str(self.ui.fileEdit.text()), 'a').close()
        
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

## Always start by initializing Qt (only once per application)
app = QtGui.QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec_())
"""

from pyqtgraph.Qt import QtGui, QtCore, uic
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)


#win = QtGui.QWidget()
#win.setWindowTitle('pyqtgraph example: ScatterPlotSpeedTest')
ui = uic.loadUi("ScatterPlotSpeedTestTemplate.ui")
ui.setWindowTitle('pyqtgraph example: ScatterPlotSpeedTest')
#ui.setupUi(win)
ui.show()

p = ui.plot
p.setRange(xRange=[-500, 500], yRange=[-500, 500])

data = np.random.normal(size=(50,500), scale=100)
sizeArray = (np.random.random(500) * 20.).astype(int)
ptr = 0
lastTime = time()
fps = None
def update():
    global curve, data, ptr, p, lastTime, fps
    p.clear()
    if ui.randCheck.isChecked():
        size = sizeArray
    else:
        size = ui.sizeSpin.value()
    curve = pg.ScatterPlotItem(x=data[ptr%50], y=data[(ptr+1)%50], 
                               pen='w', brush='b', size=size, 
                               pxMode=ui.pixelModeCheck.isChecked())
    p.addItem(curve)
    ptr += 1
    now = time()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0/dt
    else:
        s = np.clip(dt*3., 0, 1)
        fps = fps * (1-s) + (1.0/dt) * s
    p.setTitle('%0.2f fps' % fps)
    p.repaint()
    #app.processEvents()  ## force complete redraw for every plot
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
    


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
"""