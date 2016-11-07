import socket
import multiprocessing as mp
import threading
import asyncore
import sys
import control_signals_pb2


class DataClient():
    def __init__(self, host, port, storage_queue, gui_data_queue):
        # initialize TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
        self.sock.connect((self.host, self.port))
        self.connected = True

    def close_data_port(self):
        print 'DataClient: close_control_port()'
        self.connected = False
        self.sock.close()

    def receive_data(self):
        self.sock.recv()
        # TODO: don't just drop data
