from storage_controller import StorageController

import multiprocessing as mp
import time
import random
import numpy as np
import pytest
import os.path
from subprocess import call

def test_grabbuffer_single():
    # StorageController should automatically consume data from the ingoing_buffer
    # without any configuration except initialization
    ingoing_buffer = mp.Queue()
    sc = StorageController(ingoing_buffer)
    expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'
    reading = {('TS' , 15),
               ('0.0', 0xDEADBEEF),
               ('0.1', 0xBEADBEEF),
               ('0.2', 0xBEADDEEF),
               ('0.3', 0xDEAFBEEF),
               ('1.0', 0xDEADBED0),
               ('1.1', 0xEDBE98EF),
               ('1.2', 0xDEA234EF),
               ('1.3', 0xCA56BEEF),
               }
    ingoing_buffer.put(reading)
    time.sleep(0.1)
    assert ingoing_buffer.empty()

    # cleanup
    call(['rm', expected_filename])

def test_grabbuffer_short_burst():
    # StorageController should automatically consume data from the ingoing_buffer
    # without any configuration except initialization
    ingoing_buffer = mp.Queue()
    sc = StorageController(ingoing_buffer)
    expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'
    for i in range(1000):
        reading = {('TS' , random.random() * 15),
                   ('0.0', random.randrange(0, 0xffffffff)),
                   ('0.1', random.randrange(0, 0xffffffff)),
                   ('0.2', random.randrange(0, 0xffffffff)),
                   ('0.3', random.randrange(0, 0xffffffff)),
                   ('1.0', random.randrange(0, 0xffffffff)),
                   ('1.1', random.randrange(0, 0xffffffff)),
                   ('1.2', random.randrange(0, 0xffffffff)),
                   ('1.3', random.randrange(0, 0xffffffff)),
                   }
        ingoing_buffer.put(reading)
    time.sleep(0.1)
    assert ingoing_buffer.empty()
    # cleanup
    call(['rm', expected_filename])

def test_writefiles_file_created():
    # StorageController should ???
    ingoing_buffer = mp.Queue()
    sc = StorageController(ingoing_buffer)
    expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'

    reading = {('TS', random.random() * 15),
               ('0.0', random.randrange(0, 0xffffffff)),
               ('0.1', random.randrange(0, 0xffffffff)),
               ('0.2', random.randrange(0, 0xffffffff)),
               ('0.3', random.randrange(0, 0xffffffff)),
               ('1.0', random.randrange(0, 0xffffffff)),
               ('1.1', random.randrange(0, 0xffffffff)),
               ('1.2', random.randrange(0, 0xffffffff)),
               ('1.3', random.randrange(0, 0xffffffff)),
               }

    ingoing_buffer.put(reading)
    time.sleep(0.1)
    assert os.path.isfile(expected_filename)
    # cleanup
    call(['rm', expected_filename])

def test_writefiles_short_burst():
    # StorageController should ???
    ingoing_buffer = mp.Queue()
    sc = StorageController(ingoing_buffer)
    expected_filename = time.strftime('%Y%m%d-%H:%M:%S') + '.h5'

    for i in range(1000):
        # reading = {('TS', random.random() * 15),
        #            ('0.0', random.randrange(0, 0xffffffff)),
        #            ('0.1', random.randrange(0, 0xffffffff)),
        #            ('0.2', random.randrange(0, 0xffffffff)),
        #            ('0.3', random.randrange(0, 0xffffffff)),
        #            ('1.0', random.randrange(0, 0xffffffff)),
        #            ('1.1', random.randrange(0, 0xffffffff)),
        #            ('1.2', random.randrange(0, 0xffffffff)),
        #            ('1.3', random.randrange(0, 0xffffffff)),
        #            }
        reading = np.array([('0.0', random.randrange(0, 0xffffffff)),
                            ('0.1', random.randrange(0, 0xffffffff)),
                            ('0.2', random.randrange(0, 0xffffffff)),
                            ('0.3', random.randrange(0, 0xffffffff)),
                            ('1.0', random.randrange(0, 0xffffffff)),
                            ('1.1', random.randrange(0, 0xffffffff)),
                            ('1.2', random.randrange(0, 0xffffffff)),
                            ('1.3', random.randrange(0, 0xffffffff))],
                 dtype=[('channel', 'S3'), ('value', 'i2')])
        ingoing_buffer.put(reading)

    time.sleep(1)
    assert sc.write_buffer.empty()
    # cleanup
    call(['rm', expected_filename])

@pytest.mark.skip(reason="not implemented yet")
def test_channel_change():
    print 'foo'