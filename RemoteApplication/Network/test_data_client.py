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
reading_to_be_stored_cond = mp.Condition()
readings_to_be_plotted_cond = mp.Condition()

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

    @pytest.mark.skip
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

        with dc.expected_readings_verified_lock:
            dc.expected_readings_verified = 99999999

        for i in range(input_length):
            for j in range(len(normal_reading)):
                bytes_sent += conn.send(np.uint16(normal_reading[j]))

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = bytes_sent
        print 'Test: finished sending part 1, bytes_sent = %d' % bytes_sent
        # first two readings will get dropped by sync. recovery filter
        with dc.expected_readings_verified_lock:
            dc.expected_readings_verified = input_length - 2

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

        with dc.expected_readings_verified_lock:
            dc.expected_readings_verified = 99999999

        for i in range(input_length):
            for j in range(len(normal_reading)):
                bytes_sent += conn.send(np.uint16(normal_reading[j]))

        print 'Test: finished sending part 3, bytes_sent = %d' % bytes_sent

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = bytes_sent

        with dc.expected_readings_verified_lock:
            dc.expected_readings_verified = (input_length - 2) * 2

        with dc.sync_filter_done_cond:
            dc.sync_filter_done_cond.wait()
            print 'Sync filter finished task 3'

        assert dc.synchronized

        dc.close_data_port()
        conn.close()
        server_sock.close()

class TestPerformance:
    @pytest.mark.skip
    def test_recv_and_verify_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('localhost', 10002))
        server_sock.listen(1)
        print 'listening on %s:%d' % ('localhost', 10002)

        dc.connect_data_port()

        conn, addr = server_sock.accept()
        print 'accepted connection from %s:%d' % (addr[0], addr[1])

        input_length = 1000

        with dc.expected_readings_verified_lock:
            dc.expected_readings_verified = input_length - 2

        start = time.time()

        for i in range(input_length):
            for j in range(len(normal_reading)):
                conn.send(np.uint16(normal_reading[j]))

        with dc.sync_filter_done_cond:
            dc.sync_filter_done_cond.wait()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nReceive and Verify Stages: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

        dc.close_data_port()
        conn.close()
        server_sock.close()

    @pytest.mark.skip
    def test_sync_verify_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_verification_thread()
        dc.start_parser_thread()
        dc.synchronized = True

        input_length = 10000
        chunk_size  = 20

        with dc.expected_readings_verified_lock:
            dc.expected_readings_verified = input_length / chunk_size

        normal_bytearray_chunk = bytearray(0)
        for i in range(chunk_size):
            normal_bytearray_chunk += normal_bytearray

        start = time.time()

        for i in range(input_length / chunk_size):
            dc.fast_path_sender.send(normal_bytearray_chunk)
            with dc.frame_to_be_verified_cond:
                dc.frame_to_be_verified_cond.notify()

        with dc.sync_filter_done_cond:
            dc.sync_filter_done_cond.wait()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nSync Verification Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

    def test_receive_recovery_speed(self):
        dc = DataClient(storage_sender, gui_data_sender, reading_to_be_stored_cond, readings_to_be_plotted_cond)

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(('localhost', 10002))
        server_sock.listen(1)
        print 'listening on %s:%d' % ('localhost', 10002)

        dc.connect_data_port('localhost', 10002)

        conn, addr = server_sock.accept()
        print 'accepted connection from %s:%d' % (addr[0], addr[1])

        input_length = 1000

        bytes_sent = 0

        start = time.time()

        for i in range(input_length):
            for j in range(len(normal_reading)):
                bytes_sent += conn.send(np.uint16(normal_reading[j]))

        with dc.expected_bytes_sent_lock:
            dc.expected_bytes_sent = bytes_sent

        dc.receiver_done_event.wait()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nReceive Recover Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

        dc.close_data_port()
        conn.close()
        server_sock.close()

    @pytest.mark.skip
    def test_parser_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_parser_thread()

        input_length = 10000
        chunk_size = 20

        with dc.expected_readings_parsed_lock:
            dc.expected_readings_parsed = input_length

        normal_bytearray_chunk = bytearray(0)
        for i in range(chunk_size):
            normal_bytearray_chunk += normal_bytearray

        start = time.time()

        for i in range(input_length / chunk_size):
            dc.pipeline_sender.send(normal_bytearray_chunk)
            with dc.reading_available_to_parse_cond:
                dc.reading_available_to_parse_cond.notify()

        with dc.parser_done_cond:
            dc.parser_done_cond.wait()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nParser Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

    @pytest.mark.skip
    def test_verify_and_parse_speed(self):
        dc = DataClient(host, port, storage_sender, gui_data_sender, active_channels)

        dc.start_sync_verification_thread()
        dc.start_parser_thread()

        input_length = 10000
        chunk_size = 20

        with dc.expected_readings_parsed_lock:
            dc.expected_readings_parsed = input_length

        normal_bytearray_chunk = bytearray(0)
        for i in range(chunk_size):
            normal_bytearray_chunk += normal_bytearray

        start = time.time()

        for i in range(input_length / chunk_size):
            dc.fast_path_sender.send(normal_bytearray_chunk)
            with dc.frame_to_be_verified_cond:
                dc.frame_to_be_verified_cond.notify()

        with dc.parser_done_cond:
            dc.parser_done_cond.wait()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nParser Stage: effective frequency over %d samples is %d Hz\n' % (input_length, speed)