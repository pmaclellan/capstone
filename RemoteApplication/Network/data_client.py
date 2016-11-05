import socket
import multiprocessing as mp
import threading
import asyncore
import sys
import control_signals_pb2


class DataClient(asyncore.dispatcher):
    def __init__(self, host, port, storage_queue, gui_data_queue):
        asyncore.dispatcher.__init__(self)

        # initialize TCP socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        # buffer between NetworkController and StorageController
        self.storage_queue = storage_queue

        # buffer between NetworkController and GUI
        self.gui_queue = gui_data_queue

        # buffer for incoming data stream from socket
        self.incoming_queue = mp.Queue()

        # buffer between stream processing threads
        self.pipeline_queue = mp.Queue()

        self.host = host
        self.port = port
        self.connected = False

    def connect_data_port(self):
        print 'DataClient: attempting connection'
        self.connect((self.host, self.port))
        self.connected = True

    def close_data_port(self):
        print 'DataClient: close_control_port()'
        self.connected = False
        self.close()

    def handle_connect(self):
        print 'DataClient: handle_connect() entered'

    def handle_close(self):
        self.connected = False
        self.close()

    def handle_read(self):
        print 'baz'

    def readable(self):
        return True

    def writable(self):
        return False
