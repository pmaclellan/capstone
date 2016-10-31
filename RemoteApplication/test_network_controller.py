from network_controller import NetworkController
import multiprocessing


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
    gui_queue.put(5)
    assert gui_queue.empty()