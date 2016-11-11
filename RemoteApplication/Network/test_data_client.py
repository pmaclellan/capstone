from data_client import DataClient

import multiprocessing as mp
import time

host = 'foo'
port = 5
storage_queue = mp.Queue()
gui_data_queue = mp.Queue()

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

    def test_initial_sync(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

        dc.start_sync_recovery_thread()

        # play the normal_sequence twice so we get in sync
        for i in range(2):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert dc.synchronized

    def test_recovery_added_byte(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

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

    def test_recovery_missing_byte(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

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

    def test_recovery_random_dead(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

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
    def test_sync_to_parser_handoff(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

        dc.start_sync_recovery_thread()
        dc.start_parser_thread()

        # play the normal_sequence twice so we get in sync
        for i in range(3):
            for x in normal_sequence:
                dc.incoming_queue.put(x)

        time.sleep(0.2)
        assert not dc.storage_queue.empty()
        assert not dc.gui_queue.empty()

class TestPerformance:
    def test_fast_path_speed(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

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

    def test_sync_recovery_speed(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

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

    def test_parser_speed(self):
        dc = DataClient(host, port, storage_queue, gui_data_queue, active_channels)

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