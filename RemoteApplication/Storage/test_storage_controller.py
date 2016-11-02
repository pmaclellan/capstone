from storage_controller import StorageController

import multiprocessing as mp
import time

def test_grabbuffer():
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