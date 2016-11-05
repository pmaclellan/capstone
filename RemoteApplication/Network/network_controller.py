import socket
import multiprocessing as mp
import threading
import asyncore
import sys
import control_signals_pb2
from control_client import ControlClient
from data_client import DataClient


class NetworkController():
    def __init__(self, storage_queue, from_gui_queue, gui_data_queue):

        if type(storage_queue) is mp.queues.Queue:
            self.storage_queue = storage_queue
        else:
            raise TypeError('arg 1 must be a multiprocessing.Queue, found \n%s' % str(type(storage_queue)))

        if type(from_gui_queue) is mp.queues.Queue:
            self.from_gui_queue = from_gui_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(gui_queue)))

        if type(gui_data_queue) is mp.queues.Queue:
            self.gui_data_queue = gui_data_queue
        else:
            raise TypeError('arg 3 must be a multiprocessing.Queue, found \n%s' % str(type(gui_data_queue)))

        self.outgoing_queue = mp.Queue()
        self.received_queue = mp.Queue()

        # create TCP sockets for communication with DaQuLa
        self.control_client = ControlClient('localhost', 10001,
                                            self.outgoing_queue,
                                            self.received_queue)
        self.data_client = DataClient('localhost', 10002,
                                      self.gui_data_queue,
                                      self.storage_queue)

        # receives request protobuf messages triggered by GUI events
        self.gui_receiver_thread = threading.Thread(target=self.recv_from_gui)
        self.gui_receiver_thread.daemon = True
        self.gui_receiver_thread.start()

        # handle asyncore blocking loop in a separate thread
        # NOTE: lambda needed so loop() doesn't get called right away and block
        # 1.0 sets the polling frequency (default=30.0)
        # use_poll=True is a workaround to avoid "bad file descriptor" upon closing
        # for python 2.7.X according to GitHub Issue...but it still gives the error
        self.loop_thread = threading.Thread(target=lambda: asyncore.loop(1.0, use_poll=True))

    def connect_control_port(self):
        print 'connect_control_port() entered'
        if self.control_client is not None and not self.control_client.connected:
            self.control_client.connect_control_port()
            self.loop_thread.start()

    def close_control_port(self):
        self.control_client.close_control_port()
        self.loop_thread.join()

    def recv_from_gui(self):
        while True:
            if not self.from_gui_queue.empty() and self.control_client.connected:
                requestWrapper = control_signals_pb2.RequestWrapper()

                serialized = self.from_gui_queue.get_nowait()

                requestWrapper.ParseFromString(serialized)
                print 'received wrapper %s' % requestWrapper

                # just pass along to control client without modifying
                self.outgoing_queue.put(serialized)

            elif not self.from_gui_queue.empty() and not self.control_client.connected:
                self.from_gui_queue.get_nowait()
                print 'NOT CONNECTED: dropped message'

                # TODO: notify GUI that connection to server has not been established
                # TODO: -> requests cannot be sent at this time
