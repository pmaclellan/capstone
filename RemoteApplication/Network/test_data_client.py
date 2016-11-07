from data_client import DataClient

import pytest
import multiprocessing as mp
import time
import socket
import sys

host = 'foo'
port = 5
storage_queue = mp.Queue()
gui_data_queue = mp.Queue()

class TestDataClient:

    def test_normal_conditions(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue)

        dc.start_sync_recovery_thread()

        sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']
        for x in sequence:
            dc.incoming_queue.put(x)