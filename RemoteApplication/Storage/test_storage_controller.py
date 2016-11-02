from storage_controller import StorageController

import multiprocessing as mp
import time
import random
import pytest

def test_grabbuffer_single():
    # StorageController should automatically consume data from the ingoing_buffer
    # without any configuration except initialization
    ingoing_buffer = mp.Queue()
    sc = StorageController(ingoing_buffer)
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

def test_grabbuffer_short_burst():
    # StorageController should automatically consume data from the ingoing_buffer
    # without any configuration except initialization
    ingoing_buffer = mp.Queue()
    sc = StorageController(ingoing_buffer)
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

@pytest.mark.skip(reason="not implemented yet")
def test_channel_change():
    print 'foo'