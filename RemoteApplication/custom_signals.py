from PyQt4 import QtCore

class CustomSignal(QtCore.QObject):

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()
    new_data = QtCore.pyqtSignal(dict)