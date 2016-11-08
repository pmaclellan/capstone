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

    def test_initial_sync(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue)

        dc.start_sync_recovery_thread()

        sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

        # play the sequence twice so we get in sync
        for i in range(2):
            for x in sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.1)
        assert dc.synchronized

    def test_recovery(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue)

        dc.start_sync_recovery_thread()

        sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

        # play the sequence twice so we get in sync
        for i in range(2):
            for x in sequence:
                dc.incoming_queue.put(x)

        # throw a wrench in the pipeline
        dc.incoming_queue.put('c')

        # play the sequence once again
        print '\n\n%d\n\n' % len(sequence)
        for x in sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)

        assert not dc.synchronized

        # play the sequence once again, this is where we recover
        for x in sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)
        assert dc.synchronized