from Gui.daqula_gui import MainWindow, DaqPlot, CheckBoxes
from Network.network_controller import NetworkController
from Storage.storage_controller import StorageController

import multiprocessing as mp
from PyQt4 import QtGui
import sys

class DaqulaApplication(mp.Process):
    def __init__(self, argv):
        super(DaqulaApplication, self).__init__()
        self.argv = argv

    def run(self):
        self.gui_app = QtGui.QApplication(self.argv)

        # Create Connection channels to link various submodules
        self.storage_receiver, self.storage_sender = mp.Pipe(duplex=False)
        self.gui_control_conn, self.nc_control_conn = mp.Pipe(duplex=True)
        self.gui_data_receiver, self.gui_data_sender = mp.Pipe(duplex=False)

        # Create Condition variables
        self.reading_to_be_stored_cond = mp.Condition()
        self.readings_to_be_plotted_cond = mp.Condition()

        self.gui = MainWindow(control_conn=self.gui_control_conn,
                              data_receiver=self.gui_data_receiver)

        self.nc = NetworkController(storage_sender=self.storage_sender,
                                    gui_control_conn=self.nc_control_conn,
                                    gui_data_sender=self.gui_data_sender,
                                    reading_to_be_stored_cond=self.reading_to_be_stored_cond,
                                    readings_to_be_plotted_cond=self.readings_to_be_plotted_cond)

        self.sc = StorageController(storage_receiver=self.storage_receiver,
                                    reading_to_be_stored_cond=self.reading_to_be_stored_cond)

        self.nc.start()

        sys.exit(self.gui_app.exec_())

if __name__ == "__main__":
    app = DaqulaApplication(sys.argv)
    app.start()