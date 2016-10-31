from network_controller import NetworkController
import multiprocessing
import control_signals_pb2
import time


def setup():
    stg_queue = multiprocessing.Queue()
    gui_queue = multiprocessing.Queue()
    nc = NetworkController(stg_queue, gui_queue)
    return (stg_queue, gui_queue, nc)

def test_creation():
    stg_queue, gui_queue, nc = setup()
    assert nc.control_sock is not None
    assert nc.data_sock is not None

def test_gui_queue_receiver():
    stg_queue, gui_queue, nc = setup()
    startRequest = control_signals_pb2.StartRequest()
    startRequest.port = 0
    startRequest.channels = 0xDEADBEEF
    gui_queue.put(startRequest)
    time.sleep(0.5) # wait for nc to read from queue
    assert gui_queue.empty()

def test_mult_types_gui_queue_receiver():
    stg_queue, gui_queue, nc = setup()
    startRequest = control_signals_pb2.StartRequest()
    startRequest.port = 0
    startRequest.channels = 0xDEADBEEF
    stopRequest = control_signals_pb2.StopRequest()
    stopRequest.port = 0
    stopRequest.channels = 0xDEADBEEF
    gui_queue.put(startRequest)
    gui_queue.put(stopRequest)
    time.sleep(0.5) # wait for nc to read from queue
    assert gui_queue.empty()