import socket
import multiprocessing
import threading
import asyncore
import sys
import control_signals_pb2

class ControlClient(asyncore.dispatcher):
    def __init__(self, host, port, outgoing_queue, sent_dict, incoming_queue):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.outgoing_queue = outgoing_queue
        self.sent_dict = sent_dict
        self.incoming_queue = incoming_queue
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
        length = self.recv(2)
        print 'received length header: %s' % length
        msg = self.recv(length)
        print 'received message: %s' % msg
        ack = control_signals_pb2.RequestWrapper()
        ack.ParseFromString(msg)
        seq = ack.seq
        if seq in self.sent_dict.keys():
            acked_request = self.sent_dict.pop(seq)
            # TODO: process ACK and notify necessary parties

    def readable(self):
        return True

    def writable(self):
        is_writable = not self.outgoing_queue.empty()
        print 'writable() -> %s' % is_writable
        return is_writable

    def handle_write(self):
        # grab request to be sent from the queue
        request = self.outgoing_queue.get_nowait()
        print 'retrieved msg type: %s from queue' % type(request)

        # wrap request in generic request message
        wrapped_request = control_signals_pb2.RequestWrapper()
        wrapped_request.sequence = self.sequence
        if request is control_signals_pb2._STARTREQUEST:
            wrapped_request.start = request
        elif request is control_signals_pb2._STOPREQUEST:
            wrapped_request.stop = request
        elif request is control_signals_pb2._SAMPLERATEREQUEST:
            wrapped_request.rate = request
        elif request is control_signals_pb2._SENSITIVITYREQUEST:
            wrapped_request.sens = request

        serialized = wrapped_request.SerializeToString()
        print 'sending message length over control socket'
        self.send(str(sys.getsizeof(serialized)))
        print 'sending Request message over control socket'
        sent = self.send(serialized)
        print 'sent message bytes: %d' % sent
        self.sent_dict[self.sequence] = request
        self.sequence += 1
        print 'next SEQ num: %d' % self.sequence


class NetworkController():
    def __init__(self, storage_queue, gui_queue):
        print 'NetworkController __init__()'

        if type(storage_queue) is multiprocessing.queues.Queue:
            self.storage_queue = storage_queue
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(storage_queue)))

        if type(gui_queue) is multiprocessing.queues.Queue:
            self.gui_queue = gui_queue
            print 'NC-side: gui_queue received is empty: %s' % gui_queue.empty()
            print 'NC-side: self.gui_queue is empty: %s' % self.gui_queue.empty()
        else:
            raise TypeError('arg 2 must be a multiprocessing.Queue, found \n%s' % str(type(gui_queue)))

        # sent_dict will hold request messages that have been sent over the
        # control_socket but have not yet been ACKed
        self.sent_dict = {}

        self.outgoing_queue = multiprocessing.Queue()
        self.received_queue = multiprocessing.Queue()

        # create TCP sockets for communication with DaQuLa
        self.control_client = ControlClient('localhost', 10001,
                                            self.outgoing_queue,
                                            self.sent_dict,
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
        expected_requests = (control_signals_pb2.StartRequest,
                             control_signals_pb2.StopRequest,
                             control_signals_pb2.SampleRateRequest,
                             control_signals_pb2.SensitivityRequest)
        while True:
            if not self.gui_queue.empty() and self.control_client.connected:
                print 'client connected: %s' % self.control_client.connected
                request = self.gui_queue.get_nowait()
                if type(request) not in expected_requests:
                    raise TypeError('unexpected object in queue from gui, Type: %s' % type(request))
                else:
                    print 'putting object in outgoing_queue'
                    self.outgoing_queue.put(request)
