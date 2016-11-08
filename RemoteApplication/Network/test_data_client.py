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

    def test_recovery_added_byte(self):
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
        for x in sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)

        assert not dc.synchronized

        # play the sequence once again, this is where we recover
        for x in sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)
        assert dc.synchronized

    def test_recovery_missing_byte(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue)

        dc.start_sync_recovery_thread()

        sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

        # play the sequence twice so we get in sync, but skip the last byte
        for x in sequence:
            dc.incoming_queue.put(x)

        for i in range(len(sequence) - 1):
            dc.incoming_queue.put(sequence[i])


        # play the sequence once again
        for x in sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)

        assert not dc.synchronized

        # play the sequence once again, this is where we recover
        for x in sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)
        assert dc.synchronized

    def test_recovery_random_dead(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue)

        dc.start_sync_recovery_thread()

        sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                    '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

        dead_sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                         '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                         '\xff', '\xee', '\xad', '\xde', '\xff', '\xee', '\xff', '\xee',
                         '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

        # play the sequence twice so we get in sync
        for i in range(2):
            for x in sequence:
                dc.incoming_queue.put(x)


        # play the sequence with a random DEAD to break sync
        for x in dead_sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.1)

        assert not dc.synchronized

        # play the sequence again twice, this is where we recover
        for i in range(2):
            for x in sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.1)
        assert dc.synchronized