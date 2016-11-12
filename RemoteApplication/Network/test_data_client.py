from data_client import DataClient

import multiprocessing as mp
import numpy as np
import socket
import time
import pytest

host = 'localhost'
port = 10002
storage_receiver, storage_sender = mp.Pipe(duplex=False)
gui_data_receiver, gui_data_sender = mp.Pipe(duplex=False)

# 32 channel reading with DEAD and 48-bit timestamp offset
normal_sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                   '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

# same as above, but with a DEAD thrown in the middle somewhere
dead_sequence = ['\xad', '\xde', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa', '\xaa',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xad', '\xde', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee',
                 '\xff', '\xee', '\xff', '\xee', '\xff', '\xee', '\xff', '\xee']

normal_reading = [57005, 40000, 40000, 40000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000,
                  60000, 60000, 60000, 60000]

corrupt_reading = [57006, 40000, 40000, 40000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000,
                   60000, 60000, 60000, 60000]

normal_bytearray = bytearray([0xad, 0xde, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee])

corrupt_bytearray = bytearray([0xaf, 0xbe, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                              0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee])

parser_input = [57005, 187649984473770,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183,
                61183, 61183, 61183, 61183]

active_channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7',
                   '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
                   '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                   '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7']

class TestSyncRecoveryStage:

    @pytest.mark.skip
    def test_initial_sync(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_verification_thread()

        # play the normal_sequence twice so we get in sync
        for i in range(2):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert dc.synchronized

    @pytest.mark.skip
    def test_recovery_added_byte(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_recovery_thread()

        # play the normal_sequence twice so we get in sync
        for i in range(2):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        # throw a wrench in the pipeline
        dc.incoming_queue.put('c')

        # play the normal_sequence once again
        for x in normal_sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.2)

        assert not dc.synchronized

        # play the normal_sequence once again, this is where we recover
        for x in normal_sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert dc.synchronized

    @pytest.mark.skip
    def test_recovery_missing_byte(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_recovery_thread()

        # play the normal_sequence twice so we get in sync, but skip the last byte
        for x in normal_sequence:
            dc.incoming_queue.put(x)

        for i in range(len(normal_sequence) - 1):
            dc.incoming_queue.put(normal_sequence[i])


        # play the normal_sequence once again
        for x in normal_sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.2)

        assert not dc.synchronized

        # play the normal_sequence once again, this is where we recover
        for x in normal_sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert dc.synchronized

    @pytest.mark.skip
    def test_recovery_random_dead(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_recovery_thread()

        # play the normal_sequence twice so we get in sync
        for i in range(2):
            for x in normal_sequence:
                dc.incoming_queue.put(x)


        # play the normal_sequence with a random DEAD to break sync
        for x in dead_sequence:
            dc.incoming_queue.put(x)

        time.sleep(0.2)

        assert not dc.synchronized

        # play the normal_sequence again twice, this is where we recover
        for i in range(2):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert dc.synchronized

class TestCombinedStages:
    @pytest.mark.skip
    def test_sync_to_parser_handoff(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_recovery_thread()
        dc.start_parser_thread()

        # play the normal_sequence twice so we get in sync
        for i in range(3):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert not dc.storage_queue.empty()
        assert not dc.gui_queue.empty()

    def test_receive_and_sync_verification(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('localhost', 10002))
        server_sock.listen(1)
        print 'listening on %s:%d' % ('localhost', 10002)

        dc.connect_data_port()

        conn, addr = server_sock.accept()
        print 'accepted connection from %s:%d' % (addr[0], addr[1])

        input_length = 4
        bytes_sent = 0

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = 99999999

        with dc.expected_readings_passed_lock:
            dc.expected_readings_passed = 99999999

        for i in range(input_length):
            for j in range(len(normal_reading)):
                bytes_sent += conn.send(np.uint16(normal_reading[j]))

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = bytes_sent
        print 'Test: finished sending part 1, bytes_sent = %d' % bytes_sent
        # first two readings will get dropped by sync. recovery filter
        with dc.expected_readings_passed_lock:
            dc.expected_readings_passed = input_length - 2

        # with dc.receiver_done_cond:
        #     dc.receiver_done_cond.wait()
        #     print 'Receiver finished task 1'

        with dc.sync_filter_done_cond:
            dc.sync_filter_done_cond.wait()
            print 'Sync filter finished task 1'

        assert dc.synchronized

        print 'Part 1 passed, synchronization achieved'

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = 99999999

        for j in range(len(corrupt_reading)):
            bytes_sent += conn.send(np.uint16(corrupt_reading[j]))

        print 'Test: finished sending part 2, bytes_sent = %d' % bytes_sent

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = bytes_sent

        with dc.receiver_done_cond:
            dc.receiver_done_cond.wait()
            print 'Receiver finished task 2'

        assert not dc.synchronized
        print 'Part 2 passed, synchronization lost as expected'

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = 99999999

        with dc.expected_readings_passed_lock:
            dc.expected_readings_passed = 99999999

        for i in range(input_length):
            for j in range(len(normal_reading)):
                bytes_sent += conn.send(np.uint16(normal_reading[j]))

        print 'Test: finished sending part 3, bytes_sent = %d' % bytes_sent

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = bytes_sent

        with dc.expected_readings_passed_lock:
            dc.expected_readings_passed = (input_length - 2) * 2

        # with dc.receiver_done_cond:
        #     dc.receiver_done_cond.wait()
        #     print 'Receiver finished task 3'

        with dc.sync_filter_done_cond:
            dc.sync_filter_done_cond.wait()
            print 'Sync filter finished task 3'

        assert dc.synchronized

        conn.close()
        server_sock.close()

class TestPerformance:
    def test_recv_and_verify_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('localhost', 10002))
        server_sock.listen(1)
        print 'listening on %s:%d' % ('localhost', 10002)

        dc.connect_data_port()

        conn, addr = server_sock.accept()
        print 'accepted connection from %s:%d' % (addr[0], addr[1])

        input_length = 10000

        with dc.expected_readings_passed_lock:
            dc.expected_readings_passed = input_length - 2

        start = time.time()

        for i in range(input_length):
            for j in range(len(normal_reading)):
                conn.send(np.uint16(normal_reading[j]))

        with dc.sync_filter_done_cond:
            dc.sync_filter_done_cond.wait()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nReceive and Verify Stages: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

        conn.close()
        server_sock.close()

    @pytest.mark.skip
    def test_fast_path_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_verification_thread()
        dc.synchronized = True

        print normal_bytearray[0]

        input_length = 1000

        start = time.time()

        for i in range(input_length):
            dc.fast_path_sender.send(normal_bytearray)

        dc.fast_path_sender.send(corrupt_bytearray)

        while dc.fast_path_receiver.poll():
            # wait for the parser to finish processing the input
            continue

        assert not dc.synchronized

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nSync Recovery Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

    @pytest.mark.skip
    def test_sync_recovery_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_recovery_thread()

        input_length = 1000

        start = time.time()

        for i in range(input_length):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        while not dc.incoming_queue.empty():
            # wait for the parser to finish processing the input
            continue

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nSync Recovery Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

    @pytest.mark.skip
    def test_parser_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_parser_thread()

        input_length = 10000

        start = time.time()

        for i in range(input_length):
            dc.pipeline_queue.put(parser_input)

        while not dc.pipeline_queue.empty():
            # wait for the parser to finish processing the input
            continue

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nParser Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)