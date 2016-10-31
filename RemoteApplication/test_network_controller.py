from network_controller import NetworkController
from multiprocessing import queues

def test_creation():
    stg_queue = queues.SimpleQueue()
    gui_queue = queues.SimpleQueue()
    nc = NetworkController(stg_queue, gui_queue)
    assert(nc.control_sock is not None)
    assert(nc.data_sock is not None)
