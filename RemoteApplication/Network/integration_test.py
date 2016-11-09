from network_controller import NetworkController

import multiprocessing as mp
import control_signals_pb2
import time
import socket
import sys

global stg_queue
global from_gui_queue
global to_gui_queue
global gui_data_queue

stg_queue = mp.Queue()
from_gui_queue = mp.Queue()
to_gui_queue = mp.Queue()
gui_data_queue = mp.Queue()
nc = NetworkController(stg_queue, from_gui_queue, to_gui_queue, gui_data_queue)

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

# tell the network controller to attempt a connection to the control server
nc.connect_control_port()

# load request into queue to be sent over control socket by ControlClient
from_gui_queue.put(serialized)

time.sleep(1)
assert nc.data_client.connected