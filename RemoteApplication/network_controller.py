import socket
from multiprocessing import queues

class NetworkController():
    def __init__(self, storage_queue, gui_queue):
        print 'NetworkController __init__()'

        if isinstance(storage_queue, queues.SimpleQueue):
            self.storage_queue = storage_queue
        else:
            raise TypeError('storage_queue must be a SimpleQueue')

        if isinstance(gui_queue, queues.SimpleQueue):
            self.gui_queue = gui_queue
        else:
            raise TypeError('gui_queue must be a SimpleQueue')

        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)