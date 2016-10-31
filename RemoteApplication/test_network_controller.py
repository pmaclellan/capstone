from network_controller import NetworkController
import multiprocessing

def test_creation():
    stg_queue = multiprocessing.Queue()
    gui_queue = multiprocessing.Queue()
    nc = NetworkController(stg_queue, gui_queue)
    assert(nc.control_sock is not None)
    assert(nc.data_sock is not None)
