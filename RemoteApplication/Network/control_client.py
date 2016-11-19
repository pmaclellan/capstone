import control_signals_pb2

import socket
import multiprocessing as mp
import numpy as np
import asyncore
import sys
import logging

class ControlClient(asyncore.dispatcher):
    def __init__(self, control_protobuf_conn, ack_msg_from_cc_event, connected_event, disconnected_event):
        asyncore.dispatcher.__init__(self)

        # initialize TCP socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        # receives control messages from NetworkController to be sent over TCP control connection
        # sends ACK messages back to NetworkController
        self.control_protobuf_conn = control_protobuf_conn

        # threading.Condition variable to notify NetworkController when an ACK has been sent back up
        self.ack_msg_from_cc_event = ack_msg_from_cc_event

        # threading.Event variable for notifying NetworkController that we have connected to server (async)
        self.connected_event = connected_event
        self.disconnected_event = disconnected_event

        # holds serialized messages that have been received but not processed
        self.incoming_queue = mp.Queue()

        # holds messages that have been sent over the
        # control_socket but have not yet been ACKed
        self.sent_dict = {}

        self.connected = False

    def connect_control_port(self, host, port):
        logging.info('ControlClient: attempting connection to %s:%d', host, port)
        self.connect((host, port))
        self.connected = True

    def close_control_port(self):
        logging.debug('ControlClient: close_control_port() entered')
        self.connected = False
        self.handle_close()

    def handle_connect(self):
        logging.debug('ControlClient: handle_connect() entered')

    def handle_close(self):
        logging.debug('ControlClient: handle_close() entered')
        self.connected = False
        self.close()
        self.disconnected_event.set()
        return False

    def handle_read(self):
        # read 16 bit length header	
        size = bytearray(2)
        # TODO: wrap in try/except and handle Connection Refused socket.error
        self.recv_into(size)
        length = (size[1] << 8) + size[0]
        print length
        logging.debug('ControlClient: received length header: %s', length)

        # read the message content
        msg = self.recv(length)
        logging.debug('ControlClient: received message: %s', msg)

        # TODO: (probably not necessary) put onto incoming_queue and have another thread handle the parsing

        # construct a container protobuf and parse into from serialized message
        ackWrapper = control_signals_pb2.RequestWrapper()
        ackWrapper.ParseFromString(msg)

        sequence = ackWrapper.sequence

        if sequence in self.sent_dict.keys():
            serialized_acked_request = self.sent_dict.pop(sequence)
            logging.debug('ControlClient: ACKed request popped %s', serialized_acked_request)
            self.control_protobuf_conn.send(msg)
            self.ack_msg_from_cc_event.set()

    def readable(self):
        return True

    def writable(self):
        # we want to write whenever there are messages to be sent
        is_writable = self.control_protobuf_conn.poll()
        return is_writable

    def handle_write(self):
        # notify NetworkController that we are connected
        self.connected_event.set()

        # grab request to be sent from the incoming connection
        serialized_req_wrap = self.control_protobuf_conn.recv()
        logging.debug('ControlClient: handle_write() retrieved msg from outgoing queue')

        # parse the request for storage in sent_dict
        request_wrapper = control_signals_pb2.RequestWrapper()
        request_wrapper.ParseFromString(serialized_req_wrap)

        length = np.uint16(len(serialized_req_wrap))
        logging.debug('ControlClient: sending message length %d over control socket', length)
        self.send(length)

        logging.debug('ControlClient: sending Request message over control socket')
        sent = self.send(serialized_req_wrap)
        logging.debug('ControlClient: sent message bytes: %d', sent)

        logging.debug('ControlClient: adding request %d to sent_dict', request_wrapper.sequence)
        if request_wrapper.sequence not in self.sent_dict.keys():
            self.sent_dict[request_wrapper.sequence] = serialized_req_wrap
        else:
            raise RuntimeWarning('ControlClient: requestWrapper with sequence %d already in sent_dict' %
                                 request_wrapper.sequence)
