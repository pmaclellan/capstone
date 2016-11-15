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

        # IPC Connection channels to link various submodules
        # NC.DC -> SC
        self.storage_receiver, self.storage_sender = mp.Pipe(duplex=False)
        # GUI <--> NC
        self.gui_control_conn, self.nc_control_conn = mp.Pipe(duplex=True)
        # NC -> GUI
        self.gui_data_receiver, self.gui_data_sender = mp.Pipe(duplex=False)
        # GUI -> SC
        self.filepath_receiver, self.filepath_sender = mp.Pipe(duplex=False)
        # NC -> SC
        self.file_header_receiver, self.file_header_sender = mp.Pipe(duplex=False)

        # Create Condition variables
        self.readings_to_be_plotted_cond = mp.Condition()
        self.filepath_available_cond = mp.Condition()
        self.file_header_available_cond = mp.Condition()
        self.control_msg_from_gui_cond = mp.Condition()
        self.control_msg_from_nc_cond = mp.Condition()

        # Create Event variables for things that need timeout functionality
        self.reading_to_be_stored_event = mp.Event()

        self.gui = MainWindow(control_conn=self.gui_control_conn,
                              data_receiver=self.gui_data_receiver,
                              filepath_sender=self.filepath_sender,
                              readings_to_be_plotted_cond=self.readings_to_be_plotted_cond,
                              filepath_available_cond=self.filepath_available_cond,
                              control_msg_from_gui_cond=self.control_msg_from_gui_cond,
                              control_msg_from_nc_cond=self.control_msg_from_nc_cond)

        self.nc = NetworkController(storage_sender=self.storage_sender,
                                    gui_control_conn=self.nc_control_conn,
                                    gui_data_sender=self.gui_data_sender,
                                    file_header_sender=self.file_header_sender,
                                    file_header_available_cond=self.file_header_available_cond,
                                    reading_to_be_stored_event=self.reading_to_be_stored_event,
                                    readings_to_be_plotted_cond=self.readings_to_be_plotted_cond,
                                    control_msg_from_gui_cond=self.control_msg_from_gui_cond,
                                    control_msg_from_nc_cond=self.control_msg_from_nc_cond)

        self.sc = StorageController(storage_receiver=self.storage_receiver,
                                    filepath_receiver=self.filepath_receiver,
                                    file_header_receiver=self.file_header_receiver,
                                    reading_to_be_stored_event=self.reading_to_be_stored_event,
                                    filepath_available_cond=self.filepath_available_cond,
                                    file_header_available_cond=self.file_header_available_cond)

        self.nc.start()
        self.sc.start()

        sys.exit(self.gui_app.exec_())

if __name__ == "__main__":
    app = DaqulaApplication(sys.argv)
    app.start()