import socket
import multiprocessing
import threading
import asyncore
import sys
import control_signals_pb2

class ControlClient(asyncore.dispatcher):
    def __init__(self, host, port, outgoing_queue, incoming_queue):
        asyncore.dispatcher.__init__(self)

        # initialize TCP socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        # holds messages that have not been sent yet
        self.outgoing_queue = outgoing_queue

        # holds serialized messages that have been received but not processed
        self.incoming_queue = incoming_queue

        # holds messages that have been sent over the
        # control_socket but have not yet been ACKed
        self.sent_dict = {}

        # sequence numbers are assigned to outgoing messages to correlate ACKs
        self.sequence = 0

        self.host = host
        self.port = port
        self.connected = False

    def connect_control_port(self):
        print 'attempting connection'
        self.connect((self.host, self.port))
        self.connected = True

    def handle_connect(self):
        print 'handle_connect() entered'

    def handle_close(self):
        self.connected = False
        self.close()

    def handle_read(self):
        # read 16 bit length header
        length = self.recv(2)
        print 'received length header: %s' % length

        # read the message content
        msg = self.recv(length)
        print 'received message: %s' % msg

        # TODO: put onto incoming_queue and have another thread handle the parsing

        # construct a container protobuf and parse into from serialized message
        ackWrapper = control_signals_pb2.RequestWrapper()
        ackWrapper.ParseFromString(msg)

        seq = ackWrapper.seq

        if seq in self.sent_dict.keys():
            acked_request = self.sent_dict.pop(seq)
            print 'ACKed request popped %s' % acked_request
            # TODO: process ACK and notify necessary parties

    def readable(self):
        return True

    def writable(self):
        # we want to write whenever there are messages to be sent
        is_writable = not self.outgoing_queue.empty()
        print 'writable() -> %s' % is_writable
        return is_writable

    def handle_write(self):
        # grab request to be sent from the queue
        request_wrapper = self.outgoing_queue.get_nowait()
        print 'retrieved msg type: %s from queue' % type(request_wrapper)


        serialized = request_wrapper.SerializeToString()

        print 'sending message length over control socket'
        self.send(str(sys.getsizeof(serialized)))
        # TODO: sent as a uint16

        print 'sending Request message over control socket'
        sent = self.send(serialized)
        print 'sent message bytes: %d' % sent

        print 'adding request %d to sent_dict' % request_wrapper.sequence
        self.sent_dict[request_wrapper.sequence] = request_wrapper
        self.sequence += 1


class NetworkController():
    def __init__(self, storage_queue, gui_queue):

        if type(storage_queue) is multiprocessing.queues.Queue:
            self.storage_queue = storage_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(storage_queue)))

        if type(gui_queue) is multiprocessing.queues.Queue:
            self.gui_queue = gui_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(gui_queue)))

        self.outgoing_queue = multiprocessing.Queue()
        self.received_queue = multiprocessing.Queue()

        # create TCP sockets for communication with DaQuLa
        self.control_client = ControlClient('localhost', 10001,
                                            self.outgoing_queue,
                                            self.received_queue)
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # receives request protobuf messages triggered by GUI events
        self.gui_receiver_thread = threading.Thread(target=self.recv_from_gui)
        self.gui_receiver_thread.daemon = True
        self.gui_receiver_thread.start()

        # handle asyncore blocking loop in a separate thread
        # NOTE: lambda needed so loop() doesn't get called right away and block
        self.loop_thread = threading.Thread(target=lambda: asyncore.loop(1.0))

    def connect_control_port(self):
        print 'connect_control_port() entered'
        if self.control_client is not None and not self.control_client.connected:
            self.control_client.connect_control_port()
            self.loop_thread.start()

    def recv_from_gui(self):
        while True:
            if not self.gui_queue.empty() and self.control_client.connected:
                requestWrapper = control_signals_pb2.RequestWrapper()

                serialized = self.gui_queue.get_nowait()

                requestWrapper.ParseFromString(serialized)
                print 'received wrapper %s' % requestWrapper

                # just pass along to control client without modifying
                self.outgoing_queue.put(requestWrapper)

            elif not self.gui_queue.empty() and not self.control_client.connected:
                self.gui_queue.get_nowait()
                print 'NOT CONNECTED: dropped message'

                # TODO: notify GUI that connection to server has not been established
                # TODO: -> requests cannot be sent at this time
