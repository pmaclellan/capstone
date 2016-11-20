from Gui.daqula_gui import MainWindow, DaqPlot, CheckBoxes
from Network.network_controller import NetworkController
from Storage.storage_controller import StorageController

import multiprocessing as mp
from PyQt4 import QtGui
import sys
import logging
import signal


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
        # self.gui_data_receiver, self.gui_data_sender = mp.Pipe(duplex=False)
        self.gui_data_queue = mp.Queue()
        # GUI -> SC
        self.filepath_receiver, self.filepath_sender = mp.Pipe(duplex=False)
        # NC -> SC
        self.file_header_receiver, self.file_header_sender = mp.Pipe(duplex=False)

        # Create Event variables
        self.readings_to_be_plotted_event = mp.Event()
        self.filepath_available_event = mp.Event()
        self.file_header_available_event = mp.Event()
        self.control_msg_from_gui_event = mp.Event()
        self.control_msg_from_nc_event = mp.Event()

        # Create Event variables for things that need timeout functionality
        self.reading_to_be_stored_event = mp.Event()

        self.gui = MainWindow(control_conn=self.gui_control_conn,
                              data_queue=self.gui_data_queue,
                              filepath_sender=self.filepath_sender,
                              readings_to_be_plotted_event=self.readings_to_be_plotted_event,
                              filepath_available_event=self.filepath_available_event,
                              control_msg_from_gui_event=self.control_msg_from_gui_event,
                              control_msg_from_nc_event=self.control_msg_from_nc_event)

        self.nc = NetworkController(storage_sender=self.storage_sender,
                                    gui_control_conn=self.nc_control_conn,
                                    gui_data_queue=self.gui_data_queue,
                                    file_header_sender=self.file_header_sender,
                                    file_header_available_event=self.file_header_available_event,
                                    reading_to_be_stored_event=self.reading_to_be_stored_event,
                                    readings_to_be_plotted_event=self.readings_to_be_plotted_event,
                                    control_msg_from_gui_event=self.control_msg_from_gui_event,
                                    control_msg_from_nc_event=self.control_msg_from_nc_event)

        self.sc = StorageController(storage_receiver=self.storage_receiver,
                                    filepath_receiver=self.filepath_receiver,
                                    file_header_receiver=self.file_header_receiver,
                                    reading_to_be_stored_event=self.reading_to_be_stored_event,
                                    filepath_available_event=self.filepath_available_event,
                                    file_header_available_event=self.file_header_available_event)

        # Set signal handling of SIGINT to ignore mode. This will be inherited by NC and SC
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.nc.start()
        logging.info('NetworkController started')
        self.sc.start()
        logging.info('StorageController started')

        # set signal handler to properly shut down on SIGINT
        signal.signal(signal.SIGINT, self.signal_handler)

        self.gui_app.exec_()
        self.nc.stop_event.set()
        self.sc.stop_event.set()
        self.nc.join()
        logging.debug('Main: NetworkController joined')
        self.sc.join()
        logging.debug('Main: StorageController joined')

        sys.exit()

    def signal_handler(self, signal, frame):
        print 'DaqulaApplication: entered signal_handler()'
        self.gui_app.closeAllWindows()
        self.nc.stop_event.set()
        self.sc.stop_event.set()
