from network_controller import NetworkController

import pytest
import multiprocessing as mp
import control_signals_pb2
import time
import socket
import sys

stg_queue = mp.Queue()
from_gui_queue = mp.Queue()
to_gui_queue = mp.Queue()
gui_data_queue = mp.Queue()

def setup():
    global stg_queue
    global from_gui_queue
    global to_gui_queue
    global gui_data_queue

    stg_queue = mp.Queue()
    from_gui_queue = mp.Queue()
    to_gui_queue = mp.Queue()
    gui_data_queue = mp.Queue()
    nc = NetworkController(stg_queue, from_gui_queue, to_gui_queue, gui_data_queue)
    return nc

def recv_request_wrapper(control_conn):
    # synchronously read in the msg length header
    length = ''
    while length == '':
        length = control_conn.recv(2)
        print length
    print 'ControlServer: received length header: %s' % length

    # read in the message content
    msg = control_conn.recv(int(length))

    # construct a reply container and parse from the received message
    requestWrapper = control_signals_pb2.RequestWrapper()
    requestWrapper.ParseFromString(msg)
    print 'ControlServer: received request message:\n%s' % requestWrapper

    return requestWrapper

class TestDataConnection:
    def test_creation(self):
        nc = setup()
        assert nc.data_client is not None

    def test_connection(self):
        print 'Starting Data:test_connection()'
        nc = setup()

        # construct the initial start streaming request
        startRequest = control_signals_pb2.StartRequest()
        startRequest.port = 10002
        startRequest.channels = 0xFFFFFFFF

        # then insert it into a request wrapper
        requestWrapper = control_signals_pb2.RequestWrapper()
        requestWrapper.sequence = 1
        requestWrapper.start.MergeFrom(startRequest)

        # finally, serialize to send across boundary
        serialized = requestWrapper.SerializeToString()

        # setup a server socket to listen for control client connection
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('localhost', 10001))
        server_sock.listen(1)
        print 'ControlServer: listening on %s:%d' % ('localhost', 10001)

        # setup a server socket to listen for data client connection
        sender_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sender_sock.bind(('localhost', 10002))
        sender_sock.listen(1)
        print 'DataServer: listening on %s:%d' % ('localhost', 10002)

        # tell the network controller to attempt a connection to the control server
        nc.connect_control_port()

        control_conn, addr = server_sock.accept()
        print 'ControlServer: accepted connection from %s:%d' % (addr[0], addr[1])

        # load request into queue to be sent over control socket by ControlClient
        from_gui_queue.put(serialized)

        received = recv_request_wrapper(control_conn)

        inner_request = control_signals_pb2.StartRequest()
        inner_request.MergeFrom(received.start)

        assert inner_request.port == 10002

        # construct a reply ACK and send over control connection
        serialized_ack = received.SerializeToString()
        length = sys.getsizeof(serialized_ack)
        control_conn.send(str(length))
        control_conn.send(serialized_ack)

        data_conn, data_addr = sender_sock.accept()
        print 'DataServer: accepted connection from %s:%d' % (data_addr[0], data_addr[1])

        assert data_conn.send('ayy')

        # cleanup and close all connections
        nc.close_control_port()
        sender_sock.close()
        data_conn.close()
        server_sock.close()
        control_conn.close()

class TestControlConnection:
    def test_creation(self):
        nc = setup()
        assert nc.control_client is not None

    def test_gui_queue_receiver(self):
        nc = setup()

        startRequest = control_signals_pb2.StartRequest()
        startRequest.port = 1
        startRequest.channels = 0xDEADBEEF

        requestWrapper = control_signals_pb2.RequestWrapper()
        requestWrapper.sequence = 1
        requestWrapper.start.MergeFrom(startRequest) # can't assign directly for some reason, need to merge

        from_gui_queue.put(requestWrapper.SerializeToString())

        time.sleep(0.5) # wait for nc to read from queue
        assert from_gui_queue.empty()

    def test_mult_types_gui_queue_receiver(self):
        nc = setup()

        # construct inner request
        startRequest = control_signals_pb2.StartRequest()
        startRequest.port = 0
        startRequest.channels = 0xDEADBEEF

        # construct request wrapper containing inner
        requestWrapper1 = control_signals_pb2.RequestWrapper()
        requestWrapper1.sequence = 1
        requestWrapper1.start.MergeFrom(startRequest)  # can't assign directly for some reason, need to merge

        serialized1 = requestWrapper1.SerializeToString()

        # construct inner request
        stopRequest = control_signals_pb2.StopRequest()
        stopRequest.port = 0
        stopRequest.channels = 0xDEADBEEF

        # construct request wrapper containing inner
        requestWrapper2 = control_signals_pb2.RequestWrapper()
        requestWrapper2.sequence = 2
        requestWrapper2.stop.MergeFrom(stopRequest)  # can't assign directly for some reason, need to merge

        serialized2 = requestWrapper2.SerializeToString()

        # pass the serialized message wrappers to the network controller
        # "from" the GUI
        from_gui_queue.put(serialized1)
        from_gui_queue.put(serialized2)

        time.sleep(0.5) # wait for nc to read from queue
        assert from_gui_queue.empty()


    def test_control_socket_send_request(self):
        nc = setup()

        # Simulate message from GUI
        # first construct the inner request
        startRequest = control_signals_pb2.StartRequest()
        startRequest.port = 1
        startRequest.channels = 0xDEADBEEF

        # then insert it into a request wrapper
        requestWrapper = control_signals_pb2.RequestWrapper()
        requestWrapper.sequence = 1
        requestWrapper.start.MergeFrom(startRequest)

        # finally, serialize to send across boundary
        serialized = requestWrapper.SerializeToString()

        # setup a server socket to listen for control client connection
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('localhost', 10001))
        server_sock.listen(1)
        print 'listening on %s:%d' % ('localhost', 10001)

        # tell the network controller to attempt a connection to the server socket
        nc.connect_control_port()

        conn, addr = server_sock.accept()
        print 'accepted connection from %s:%d' % (addr[0], addr[1])

        # load request into queue to be sent over control socket by ControlClient
        from_gui_queue.put(serialized)

        received = recv_request_wrapper(conn)

        startMessage = control_signals_pb2.StartRequest()
        startMessage.MergeFrom(received.start)

        # check that we received a StartRequest back and it has the same fields
        assert received.HasField('start')
        assert startMessage.port == 1
        assert startMessage.channels == 0xDEADBEEF

        nc.close_control_port()
        server_sock.close()
        conn.close()
