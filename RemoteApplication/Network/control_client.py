import socket
import multiprocessing as mp
import threading
import asyncore
import sys
import control_signals_pb2

class ControlClient(asyncore.dispatcher):
    def __init__(self, host, port, outgoing_queue, ack_queue):
        asyncore.dispatcher.__init__(self)

        # initialize TCP socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        # holds messages that have not been sent yet
        self.outgoing_queue = outgoing_queue

        # used to pass ACKs up to network controller
        self.ack_queue = ack_queue

        # holds serialized messages that have been received but not processed
        self.incoming_queue = mp.Queue()

        # holds messages that have been sent over the
        # control_socket but have not yet been ACKed
        self.sent_dict = {}

        self.host = host
        self.port = port
        self.connected = False

    def connect_control_port(self):
        print 'ControlClient: attempting connection'
        self.connect((self.host, self.port))
        self.connected = True

    def close_control_port(self):
        print 'ControlClient: close_control_port()'
        self.connected = False
        self.close()

    def handle_connect(self):
        print 'ControlClient: handle_connect() entered'

    def handle_close(self):
        self.connected = False
        self.close()

    def handle_read(self):
        # read 16 bit length header
        length = self.recv(2)
        print 'ControlClient: received length header: %s' % length

        # read the message content
        msg = self.recv(int(length))
        print 'ControlClient: received message: %s' % msg

        # TODO: put onto incoming_queue and have another thread handle the parsing

        # construct a container protobuf and parse into from serialized message
        ackWrapper = control_signals_pb2.RequestWrapper()
        ackWrapper.ParseFromString(msg)

        sequence = ackWrapper.sequence

        if sequence in self.sent_dict.keys():
            serialized_acked_request = self.sent_dict.pop(sequence)
            print 'ControlClient: ACKed request popped %s' % serialized_acked_request
            self.ack_queue.put(serialized_acked_request)

    def readable(self):
        return True

    def writable(self):
        # we want to write whenever there are messages to be sent
        is_writable = not self.outgoing_queue.empty()
        return is_writable

    def handle_write(self):
        # grab request to be sent from the queue
        serialized_req_wrap = self.outgoing_queue.get_nowait()
        print 'ControlClient: handle_write() retrieved msg from outgoing queue'

        # parse the request for storage in sent_dict
        request_wrapper = control_signals_pb2.RequestWrapper()
        request_wrapper.ParseFromString(serialized_req_wrap)

        print 'ControlClient: sending message length over control socket'
        self.send(str(sys.getsizeof(serialized_req_wrap)))
        # TODO: sent as a uint16

        print 'ControlClient: sending Request message over control socket'
        sent = self.send(serialized_req_wrap)
        print 'ControlClient: sent message bytes: %d' % sent

        print 'ControlClient: adding request %d to sent_dict' % request_wrapper.sequence
        self.sent_dict[request_wrapper.sequence] = serialized_req_wrap
