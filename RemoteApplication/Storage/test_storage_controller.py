from storage_controller import StorageController

import multiprocessing as mp
import threading
import time
import random
import numpy as np
import pytest
import os.path
import glob
import subprocess

storage_receiver, storage_sender = mp.Pipe(duplex=False)
filepath_receiver, filepath_sender = mp.Pipe(duplex=False)
file_header_receiver, file_header_sender = mp.Pipe(duplex=False)
reading_to_be_stored_event = mp.Event()
filepath_available_cond = mp.Condition()
file_header_available_cond = mp.Condition()

reading = bytearray([0xad, 0xde, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee,
                     0xff, 0xee, 0xff, 0xee, 0xff, 0xee, 0xff, 0xee])

chunk_size = 20
active_channels = 0xffff
start_time = 1478300446552583

class TestFunctionality:
    def test_binary_writer(self):
        input_length = 1000
        sc = StorageController(storage_receiver, filepath_receiver, file_header_receiver,
                               reading_to_be_stored_event, filepath_available_cond, file_header_available_cond)

        sc.start()

        sc.expected_records = input_length

        filepath_sender.send('/Users/pmaclellan/capstone/RemoteApplication/Storage/testdir/')
        with filepath_available_cond:
            filepath_available_cond.notify()

        file_header_sender.send((start_time, active_channels, chunk_size))
        with file_header_available_cond:
            file_header_available_cond.notify()

        time.sleep(1)

        chunk = bytearray(0)
        for i in range(chunk_size):
            chunk += reading

        start = time.time()

        for i in range(input_length):
            storage_sender.send(chunk)
            reading_to_be_stored_event.set()

        elapsed = time.time() - start

        speed = 1 / (elapsed / input_length)

        print '\n\nFile Writer: effective frequency over %d samples is %d Hz\n' % (input_length, speed)

    @pytest.mark.skip
    def test_grabbuffer_single(self):
        # StorageController should automatically consume data from the ingoing_buffer
        # without any configuration except initialization
        ingoing_buffer = mp.Queue()
        sc = StorageController(ingoing_buffer)
        expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'
        reading = np.array([('_TS', 1478300446552583),
                            ('0.0', 0xDEADBEEF),
                            ('0.1', 0xDEADBEEF),
                            ('0.2', 0xDEADBEEF),
                            ('0.3', 0xDEADBEEF),
                            ('1.0', 0xDEADBEEF),
                            ('1.1', 0xDEADBEEF),
                            ('1.2', 0xDEADBEEF),
                            ('1.3', 0xDEADBEEF)],
                           dtype=[('channel', 'S3'), ('value', 'uint64')])
        ingoing_buffer.put(reading)
        time.sleep(0.1)
        assert ingoing_buffer.empty()

        # cleanup
        print 'test done, removing files'
        subprocess.call(['rm', expected_filename])

    @pytest.mark.skip
    def test_grabbuffer_short_burst(self):
        # StorageController should automatically consume data from the ingoing_buffer
        # without any configuration except initialization
        ingoing_buffer = mp.Queue()
        sc = StorageController(ingoing_buffer)
        expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'
        for i in range(1000):
            reading = np.array([('_TS', 1478300446552583),
                                ('0.0', random.randrange(0, 0xffffffff)),
                                ('0.1', random.randrange(0, 0xffffffff)),
                                ('0.2', random.randrange(0, 0xffffffff)),
                                ('0.3', random.randrange(0, 0xffffffff)),
                                ('1.0', random.randrange(0, 0xffffffff)),
                                ('1.1', random.randrange(0, 0xffffffff)),
                                ('1.2', random.randrange(0, 0xffffffff)),
                                ('1.3', random.randrange(0, 0xffffffff))],
                               dtype=[('channel', 'S3'), ('value', 'uint64')])
            ingoing_buffer.put(reading)
        time.sleep(0.5)
        assert ingoing_buffer.empty()
        # cleanup
        print 'test done, removing files'
        subprocess.call(['rm', expected_filename])

    @pytest.mark.skip
    def test_writefiles_file_created(self):
        # StorageController should ???
        ingoing_buffer = mp.Queue()
        sc = StorageController(ingoing_buffer)
        expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'

        reading = np.array([('_TS', 1478300446552583),
                            ('0.0', random.randrange(0, 0xffffffff)),
                            ('0.1', random.randrange(0, 0xffffffff)),
                            ('0.2', random.randrange(0, 0xffffffff)),
                            ('0.3', random.randrange(0, 0xffffffff)),
                            ('1.0', random.randrange(0, 0xffffffff)),
                            ('1.1', random.randrange(0, 0xffffffff)),
                            ('1.2', random.randrange(0, 0xffffffff)),
                            ('1.3', random.randrange(0, 0xffffffff))],
                           dtype=[('channel', 'S3'), ('value', 'uint64')])

        ingoing_buffer.put(reading)
        time.sleep(0.1)
        assert os.path.isfile(expected_filename)
        # cleanup
        print 'test done, removing files'
        subprocess.call(['rm', expected_filename])

    @pytest.mark.skip
    def test_writefiles_short_burst(self):
        # StorageController should ???
        ingoing_buffer = mp.Queue()
        sc = StorageController(ingoing_buffer)
        expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'

        for i in range(1000):
            reading = np.array([('_TS', 1478301405130783),
                                ('0.0', random.randrange(0, 0xffffffff)),
                                ('0.1', random.randrange(0, 0xffffffff)),
                                ('0.2', random.randrange(0, 0xffffffff)),
                                ('0.3', random.randrange(0, 0xffffffff)),
                                ('1.0', random.randrange(0, 0xffffffff)),
                                ('1.1', random.randrange(0, 0xffffffff)),
                                ('1.2', random.randrange(0, 0xffffffff)),
                                ('1.3', random.randrange(0, 0xffffffff))],
                                dtype=[('channel', 'S3'), ('value', 'uint64')])
            ingoing_buffer.put(reading)

        time.sleep(2)
        assert sc.write_buffer.empty()
        # cleanup
        print 'test done, removing files'
        subprocess.call(['rm', expected_filename])

    @pytest.mark.skip
    def test_writefiles_mult_files(self):
        ingoing_buffer = mp.Queue()
        sc = StorageController(ingoing_buffer)
        expected_filename = time.strftime('%Y%m%d') + '*'

        for i in range(10000):
            reading = np.array([('_TS', 1478301405130783),
                                ('0.0', random.randrange(0, 0xffffffff)),
                                ('0.1', random.randrange(0, 0xffffffff)),
                                ('0.2', random.randrange(0, 0xffffffff)),
                                ('0.3', random.randrange(0, 0xffffffff)),
                                ('1.0', random.randrange(0, 0xffffffff)),
                                ('1.1', random.randrange(0, 0xffffffff)),
                                ('1.2', random.randrange(0, 0xffffffff)),
                                ('1.3', random.randrange(0, 0xffffffff))],
                               dtype=[('channel', 'S3'), ('value', 'uint64')])
            ingoing_buffer.put(reading)

        time.sleep(8)
        assert sc.write_buffer.empty()
        assert len(glob.glob(expected_filename)) > 1
        # cleanup
        subprocess.Popen('rm ' + expected_filename, shell=True)

    @pytest.mark.skip(reason="not implemented yet")
    def test_channel_change(self):
        print 'foo'

class TestPerformance:
    def test_write_speed(self):
        storage_receiver, storage_writer = mp.Pipe(duplex=False)
        reading_to_be_stored_cond = threading.Condition()
        sc = StorageController(storage_receiver, reading_to_be_stored_cond)

        input_length = 1000

        reading = np.array([('_TS', 5),
                            ('0.0', 10000), ('0.1', 20000), ('0.2', 30000), ('0.3', 40000),
                            ('0.4', 10000), ('0.5', 20000), ('0.6', 30000), ('0.7', 40000),
                            ('1.0', 10000), ('1.1', 20000), ('1.2', 30000), ('1.3', 40000),
                            ('1.4', 10000), ('1.5', 20000), ('1.6', 30000), ('1.7', 40000),
                            ('2.0', 10000), ('2.1', 20000), ('2.2', 30000), ('2.3', 40000),
                            ('2.4', 10000), ('2.5', 20000), ('2.6', 30000), ('2.7', 40000),
                            ('3.0', 10000), ('3.1', 20000), ('3.2', 30000), ('3.3', 40000),
                            ('3.4', 10000), ('3.5', 20000), ('3.6', 30000), ('3.7', 40000)],
                           dtype=[('channel', 'S3'), ('value', 'uint64')])

        # pass in a Unix timestamp in uSec
        sc.start(1479000497954177)
        sc.expected_records = input_length

        start_time = time.time()

        for i in range(input_length):
            storage_writer.send(reading)
            with sc.reading_to_be_stored_cond:
                sc.reading_to_be_stored_cond.notify()

        with sc.file_writer_done_cond:
            sc.file_writer_done_cond.wait()

        elapsed = time.time() - start_time

        speed = 1 / (elapsed / input_length)

        print '\n\nFile Writer: effective frequency over %d samples is %d Hz\n' % (input_length, speed)
