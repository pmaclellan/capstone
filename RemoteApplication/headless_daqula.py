from Network.network_controller import NetworkController
from Storage.storage_controller import StorageController

import multiprocessing as mp
import threading
import sys
import logging
import signal
import time


class HeadlessDaqula(mp.Process):
    def __init__(self, output_dir, rate, host, port):
        super(HeadlessDaqula, self).__init__()
        self.output_dir = output_dir
        self.sample_rate = rate
        self.host = host
        self.control_port = port

    def run(self):
        print mp.current_process().pid
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
        self.stop_event = mp.Event()

        # Create Event variables for things that need timeout functionality
        self.reading_to_be_stored_event = mp.Event()

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

        self.control_receiver_thread = threading.Thread(target=self.recv_control_message)
        self.control_receiver_thread.daemon = True
        self.control_receiver_thread.start()

        # Set signal handling of SIGINT to ignore mode. This will be inherited by NC and SC
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.nc.start()
        logging.info('NetworkController started')
        self.sc.start()
        logging.info('StorageController started')

        # set signal handler to properly shut down on SIGINT
        signal.signal(signal.SIGINT, self.signal_handler)

        print 'Attempting to connect to DAQ at %s:%d' % (self.host, self.control_port)
        self.send_start_message()

        self.control_receiver_thread.join()
        self.nc.join()
        logging.debug('Main: NetworkController joined')
        self.sc.join()
        logging.debug('Main: StorageController joined')

        sys.exit()

    def signal_handler(self, signal, frame):
        print 'HeadlessDaqula: Entered signal handler'
        self.trigger_stop()

    def trigger_stop(self):
        self.stop_event.set()
        self.nc.stop_event.set()
        self.sc.stop_event.set()

    def send_start_message(self):
        self.filepath_sender.send(self.output_dir)
        self.filepath_available_event.set()

        # construct connect control message
        connect_msg = {}
        connect_msg['seq'] = 0
        connect_msg['type'] = 'CONNECT'
        connect_msg['host'] = self.host
        connect_msg['port'] = self.control_port
        connect_msg['channels'] = 0xffffffff
        connect_msg['rate'] = self.sample_rate

        # pretend to send it from "GUI" to NetworkController
        self.gui_control_conn.send(connect_msg)
        self.control_msg_from_gui_event.set()

    def recv_control_message(self):
        while not self.stop_event.is_set():
            if self.gui_control_conn.poll():
                response = self.gui_control_conn.recv()
                if response['type'] == 'CONNECT':
                    if response['success'] == True:
                        print response['message']
                        break
                    else:
                        print response['message']
                        self.trigger_stop()
                        break
                else:
                    raise RuntimeWarning('unexpected message received from NetworkController')
            else:
                while not self.stop_event.is_set():
                    if self.control_msg_from_nc_event.wait(1.0):
                        self.control_msg_from_nc_event.clear()
                        break
