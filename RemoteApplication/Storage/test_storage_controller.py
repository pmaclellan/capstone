from storage_controller import StorageController

import multiprocessing as mp
import time
import random
import numpy as np
import pytest
import os.path
import glob
import subprocess

def test_grabbuffer_single():
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

def test_grabbuffer_short_burst():
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

def test_writefiles_file_created():
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

def test_writefiles_short_burst():
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

def test_writefiles_mult_files():
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
def test_channel_change():
    print 'foo'