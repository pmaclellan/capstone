import threading
import h5py
import numpy as np
import multiprocessing as mp
import time
import os.path

class StorageController():
    def __init__(self, storage_receiver, reading_to_be_stored_cond):
        print 'StorageController __init()'
        # Pipe connection object that will contain parsed ADC data readings (numpy arrays)
        self.storage_receiver = storage_receiver

        # Pipe for passing data internally
        self.from_reader, self.to_writer = mp.Pipe(duplex=False)

        # Create worker threads
        self.reader_thread = threading.Thread(target=self.grabbuffer)
        self.writer_thread = threading.Thread(target=self.writefiles)

        self.stop_event = threading.Event()

        self.reading_to_be_stored_cond = reading_to_be_stored_cond
        self.file_writer_done_cond = threading.Condition()

        # start_time will hold the Unix time to add to each reading's timestamp offset
        self.start_time = 0

        # for testing purposes only
        self.expected_records = 99999999

    def start(self, start_time):
        self.start_time = start_time
        self.reader_thread.start()
        self.writer_thread.start()

    def stop(self):
        self.stop_event.set()

    def writefiles(self):
        timeout_threshold = 100000
        filesize_threshold = 512000
        chunk_size = 200
        records_written = 0
        write_buffer = []
        storage_type = np.dtype([('channel', 'S3'), ('value', 'uint64')])

        while not self.stop_event.is_set():
            with self.file_writer_done_cond:
                if records_written >= self.expected_records:
                    self.file_writer_done_cond.notify()

            if self.from_reader.poll():
                filename = time.strftime('%Y%m%d-%H:%M:%S')+'.h5'
                f = h5py.File(filename, 'a')
                # print 'new file created: %s' % filename
                timeout_counter = 0
                i = 0

                while timeout_counter < timeout_threshold:
                    with self.file_writer_done_cond:
                        if records_written >= self.expected_records:
                            self.file_writer_done_cond.notify()

                    if self.from_reader.poll():
                        timeout_counter = 0
                        reading = self.from_reader.recv()
                        # print 'SC recv\'d a reading'
                        write_buffer.append(reading.astype(storage_type))
                        if len(write_buffer) >= chunk_size:
                            f.create_dataset(str(i), data=write_buffer)
                            # print 'wrote dataset %d' % i
                            records_written += chunk_size
                            write_buffer = []
                            i += 1
                        if os.path.getsize(filename) > filesize_threshold:
                            # print 'file size %d exceeds limit, closing and starting new file' \
                            #       % os.path.getsize(filename)
                            f.close()
                            break
                    else:
                        timeout_counter += 1
                if timeout_counter >= timeout_threshold:
                    if len(write_buffer) > 0:
                        num_records = len(write_buffer)
                        # print 'buffer length to flush: %d' % len(write_buffer)
                        # print 'i = %d' % i
                        #write the partial buffer to file before closing
                        f.create_dataset(str(i), data=write_buffer)
                        records_written += num_records
                    f.close()
                # else continue while loop and create a new file
        if f is not None:
            # write remaining buffer to file and close before terminating thread
            if len(write_buffer) > 0:
                print 'buffer length to flush: %d' % len(write_buffer)
                print 'i = %d' % i
                # write the partial buffer to file before closing
                f.create_dataset(str(i), data=write_buffer)
            f.close()

    def process_reading(self, reading):
        # reading[0] += self.start_time
        self.to_writer.send(reading)

    def grabbuffer(self):
        while not self.stop_event.is_set():
            if self.storage_receiver.poll():
                reading = self.storage_receiver.recv()
                self.process_reading(reading)
            else:
                with self.reading_to_be_stored_cond:
                    self.reading_to_be_stored_cond.wait()