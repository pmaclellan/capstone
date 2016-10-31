import socket
import multiprocessing

class NetworkController():
    def __init__(self, storage_queue, gui_queue):
        print 'NetworkController __init__()'

        if type(storage_queue) is multiprocessing.queues.Queue:
            self.storage_queue = storage_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(storage_queue)))

        if type(gui_queue) is multiprocessing.queues.Queue:
            self.gui_queue = gui_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(gui_queue)))

        # create TCP sockets for communication with DaQuLa
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # sent_dict will hold request messages that have been sent over the
        # control_socket but have not yet been ACKed
        self.sent_dict = {}