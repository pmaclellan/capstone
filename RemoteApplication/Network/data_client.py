import socket
import multiprocessing as mp
import threading


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

        self.recv_stop_event = threading.Event()
        self.receiver_thread = threading.Thread(target=self.receive_data, args=[self.recv_stop_event])
        self.sync_recovery_thread = threading.Thread(target=self.syncronize_stream, args=[self.recv_stop_event])

        self.host = host
        self.port = port
        self.connected = False

    def start_receiver_thread(self):
        self.receiver_thread.start()

    def stop_receiver_thread(self):
        self.recv_stop_event.set()

    def start_sync_recovery_thread(self):
        self.sync_recovery_thread.start()

    def connect_data_port(self):
        print 'DataClient: attempting connection'
        self.sock.connect((self.host, self.port))
        self.start_receiver_thread()
        self.connected = True

    def close_data_port(self):
        print 'DataClient: close_control_port()'
        self.connected = False
        self.stop_receiver_thread()
        self.sock.close()

    def receive_data(self, *args):
        stop_event = args[0]
        while not stop_event.is_set():
            byte = self.sock.recv(1)
            if byte != '':
                self.incoming_queue.put(byte.encode('hex'))

    def syncronize_stream(self, *args):
        print '\n\nsync thread started'
        stop_event = args[0]
        while not stop_event.is_set():
            if self.incoming_queue.empty():
                continue
            byte2 = self.incoming_queue.get_nowait()
            # TODO: odd number of bytes will break this, do something about that
            byte1 = self.incoming_queue.get_nowait()
            value = int(byte1.encode('hex') + byte2.encode('hex'), 16)
            print value

