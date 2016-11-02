import threading
import h5py
import time
import Queue
import os.path

class StorageController():
    def __init__(self, incoming_buffer):
        print 'StorageController __init()'
        # Buffer will contain parsed ADC data readings
        self.incoming_buf = incoming_buffer
        self.write_buffer = Queue.Queue()
        self.reader_thread = threading.Thread(target=self.grabbuffer)
        self.reader_thread.start()
        self.writer_thread = threading.Thread(target=self.writefiles)
        self.writer_thread.start()

    def writefiles(self):
        timeout_threshold = 1000

        while True:
            filename = time.strftime('%Y%m%d-%H:%M:%S')+'.h5'
            f = h5py.File(filename, 'x')
            timeout_counter = 0
            while timeout_counter < timeout_threshold:
                if not self.write_buffer.empty():
                    timeout_counter = 0
                    reading = self.write_buffer.get_nowait()
                    # TODO: write reading to HDF file
                    if os.path.getsize(filename) > 1000:
                        print 'file size %d exceeds limit, closing and starting new file' \
                              % os.path.getsize(filename)
                        f.close()
                        break
                else:
                    timeout_counter += 1
            if timeout_counter >= timeout_threshold:
                f.close()
                # if we timeout, stop writing files
                break
            # else continue while loop and create a new file

    def process_reading(self, reading):
        # placeholder for now, this is where we might calculate timestamps, etc.
        # "massage data"
        self.write_buffer.put(reading)

    def grabbuffer(self):
        while True:
            if not self.incoming_buf.empty():
                reading = self.incoming_buf.get()
                self.process_reading(reading)