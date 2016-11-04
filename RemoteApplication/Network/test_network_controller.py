from network_controller import NetworkController
import multiprocessing as mp
import control_signals_pb2
import time
import socket

def setup():
    stg_queue = mp.Queue()
    gui_queue = mp.Queue()
    nc = NetworkController(stg_queue, gui_queue)
    return (stg_queue, gui_queue, nc)

def test_creation():
    stg_queue, gui_queue, nc = setup()
    assert nc.control_client is not None
    assert nc.data_sock is not None

def test_gui_queue_receiver():
    stg_queue, gui_queue, nc = setup()

    startRequest = control_signals_pb2.StartRequest()
    startRequest.port = 1
    startRequest.channels = 0xDEADBEEF

    requestWrapper = control_signals_pb2.RequestWrapper()
    requestWrapper.sequence = 1
    requestWrapper.start.MergeFrom(startRequest) # can't assign directly for some reason, need to merge

    gui_queue.put(requestWrapper.SerializeToString())

    time.sleep(0.5) # wait for nc to read from queue
    assert gui_queue.empty()

def test_mult_types_gui_queue_receiver():
    stg_queue, gui_queue, nc = setup()

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
    gui_queue.put(serialized1)
    gui_queue.put(serialized2)

    time.sleep(0.5) # wait for nc to read from queue
    assert gui_queue.empty()


# def test_control_socket_send_request():
#     # stg_queue, gui_queue, nc = setup()
#
#     stg_queue = mp.Queue()
#     gui_queue = mp.Queue()
#     nc = NetworkController(stg_queue, gui_queue)
#
#     print 'trying to create a StartRequest'
#     # simulate message from GUI
#     startRequest = control_signals_pb2.StartRequest()
#     startRequest.port = 0
#     startRequest.channels = 0xDEADBEEF
#     print type(startRequest)
#     print startRequest
#
#     # load request into queue to be sent by ControlClient
#     gui_queue.put(startRequest)
#
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.bind(('localhost', 10001))
#     sock.listen(1)
#     print 'gui-queue empty from test side: %s' % gui_queue.empty()
#
#     nc.connect_control_port()
#
#     print 'listening on %s:%d' % ('localhost', 10001)
#     conn, addr = sock.accept()
#     print 'accepted connection from %s:%d' % (addr[0], addr[1])
#     print 'gui-queue empty from test side: %s' % gui_queue.empty()
#
#     length = ''
#     while length == '':
#         length = conn.recv(2)
#         print length
#     print 'test received length header: %s' % length
#     msg = conn.recv(int(length))
#     reply = control_signals_pb2.RequestWrapper()
#     reply.ParseFromString(msg)
#     print 'test received request message:\n%s' % reply
#
#     assert reply.HasField('start')
#     startMessage = reply.start
#     assert startMessage is control_signals_pb2._STARTREQUEST
#     assert startMessage.port == 0
#     assert startMessage.channels == 0xDEADBEEF
