import multiprocessing as mp
import numpy as np
import threading
import asyncore
import bisect
import control_signals_pb2
from control_client import ControlClient
from data_client import DataClient


class NetworkController():
    def __init__(self, storage_queue, from_gui_queue, to_gui_queue, gui_data_queue):

        if type(storage_queue) is mp.queues.Queue:
            self.storage_queue = storage_queue
        else:
            raise TypeError('arg 1 must be a multiprocessing.Queue, found \n%s' % str(type(storage_queue)))

        if type(from_gui_queue) is mp.queues.Queue:
            self.from_gui_queue = from_gui_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(from_gui_queue)))

        if type(to_gui_queue) is mp.queues.Queue:
            self.to_gui_queue = to_gui_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(to_gui_queue)))

        if type(gui_data_queue) is mp.queues.Queue:
            self.gui_data_queue = gui_data_queue
        else:
            raise TypeError('arg 3 must be a multiprocessing.Queue, found \n%s' % str(type(gui_data_queue)))

        # shared with control client, holds request messages to be sent
        self.outgoing_queue = mp.Queue()

        # control client will write ACK'd requests here
        self.ack_queue = mp.Queue()

        # default to all channels being active
        # NOTE: this needs to match up with the default state of the channel checboxes on GUI
        self.active_channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7',
                                '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
                                '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                                '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7']

        self.channel_mask = self.generateChannelBitMask()

        # create TCP sockets for communication with DaQuLa
        self.control_client = ControlClient('localhost', 10001,
                                            self.outgoing_queue,
                                            self.ack_queue)
        self.data_client = DataClient('localhost', 10002,
                                      self.gui_data_queue,
                                      self.storage_queue)

        # receives request protobuf messages triggered by GUI events
        self.gui_receiver_thread = threading.Thread(target=self.recv_from_gui)
        self.gui_receiver_thread.daemon = True
        self.gui_receiver_thread.start()

        # listens for ACK messages being passed back from control client
        self.ack_listener_thread = threading.Thread(target=self.read_ack_messages)
        self.ack_listener_thread.start()

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

    def connect_data_port(self):
        print 'connect_data_port() entered'
        if self.data_client is not None and not self.data_client.connected:
            # inform data client which channels it should expect before connecting
            self.data_client.update_active_channels(self.active_channels)
            self.data_client.connect_data_port()

    def close_control_port(self):
        if self.data_client.connected:
            self.data_client.close_data_port()
        self.control_client.close_control_port()
        self.loop_thread.join()

    def close_data_port(self):
        self.control_client.close_data_port()

    def processChannelUpdate(self, sender, checked):
        if checked:
            if sender.text() not in self.active_channels:
                bisect.insort(self.active_channels, str(sender.text()))
        else:
            if sender.text() in self.active_channels:
                self.active_channels.remove(sender.text())

        print(self.active_channels)
        self.channel_mask = self.generateChannelBitMask()
        self.data_client.update_active_channels(self.active_channels)
        print(self.channel_mask)

    def generateChannelBitMask(self):
        bit_mask = np.uint32(0)
        offset = 0
        for i in range(4):
            for j in range(8):
                if (str(i) + '.' + str(j)) in self.active_channels:
                    # bit_mask |= 0x01 << offset
                    bit_mask = np.bitwise_or(bit_mask, np.left_shift(np.uint32(1), offset))
                else:
                    # bit_mask &= ~(0x01 << offset)
                    bit_mask = np.bitwise_and(bit_mask, np.bitwise_not(np.left_shift(np.uint32(1), offset)))
                offset += 1
        return bit_mask

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

    def read_ack_messages(self):
        while True:
            if not self.ack_queue.empty():
                acked = self.ack_queue.get_nowait()
                ack_wrapper = control_signals_pb2.RequestWrapper()
                ack_wrapper.ParseFromString(acked)
                print 'NetworkController: received ACK message %s' % ack_wrapper

                if ack_wrapper.HasField('start') and not self.data_client.connected:
                    print 'NetworkController: received start ACK, starting data client'
                    try:
                        self.data_client.connect_data_port()
                        self.to_gui_queue.put(acked)
                    except Exception, e:
                        print('ERROR: could not connect data client, exception is %s' % e)

                elif self.data_client.connected:
                    # passthrough
                    self.to_gui_queue.put(acked)


