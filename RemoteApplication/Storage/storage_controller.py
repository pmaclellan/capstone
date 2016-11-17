import threading
import h5py
import numpy as np
import multiprocessing as mp
import time
import os.path
import logging

class StorageController(mp.Process):
    def __init__(self, storage_receiver, filepath_receiver, file_header_receiver,
                 reading_to_be_stored_event, filepath_available_event, file_header_available_event):
        super(StorageController, self).__init__()

        # mp.Connection for receiving raw ADC data readings (bytearray from NC.DC)
        self.storage_receiver = storage_receiver

        # mp.Connection for receiving directory (from GUI) to write files to
        self.filepath_receiver = filepath_receiver

        # mp.Connection for receiving start_time, channel_bitmask, and chunk_size
        self.file_header_receiver = file_header_receiver

        # mp.Event variable to wait on for new readings to be available
        self.reading_to_be_stored_event = reading_to_be_stored_event

        # mp.Condition variable to wait on for new directory to write files to to be available
        self.filepath_available_event = filepath_available_event

        # mp.Condition variable to wait on for file header updates from NC
        self.file_header_available_event = file_header_available_event

        # Pipe for passing data internally
        self.from_reader, self.to_writer = mp.Pipe(duplex=False)

        # Create worker threads
        # self.reader_thread = threading.Thread(target=self.grabbuffer)
        self.writer_thread = threading.Thread(target=self.write_binary_files)
        self.filepath_listener_thread = threading.Thread(target=self.listen_for_filepath_update)
        self.filepath_listener_thread.daemon = True
        self.file_header_listener_thread = threading.Thread(target=self.listen_for_file_header_update)
        self.file_header_listener_thread.daemon = True

        self.stop_event = mp.Event()

        # start_time will hold the Unix time to add to each reading's timestamp offset
        # will be set upon receiving a start message from NC upon successful NC.CC connection
        self.start_time = 0

        # channel_bitmask will be sent along with start_time by the NetworkController upon connecting to server
        self.channel_bitmask = 0x0000
        self.chunk_size = 0

        # filepath is the absolute directory path to write files to
        self.filepath = ''

        # Lock for filepath
        self.filepath_lock = threading.Lock()

        # for testing purposes only
        self.expected_records = 99999999
        self.file_writer_done_cond = threading.Condition()

    def run(self):
        self.writer_thread.start()
        self.filepath_listener_thread.start()
        self.file_header_listener_thread.start()
        self.writer_thread.join()
        logging.info('StorageController process finished, terminating')

    def listen_for_filepath_update(self):
        while not self.stop_event.is_set():
            if self.filepath_receiver.poll():
                with self.filepath_lock:
                    self.filepath = self.filepath_receiver.recv()
                    if not os.path.exists(self.filepath):
                        print '%s not found, creating...' % self.filepath
                        os.makedirs(self.filepath)
                logging.debug('StorageController: updated filepath to %s', self.filepath)
                # TODO: input validation
            else:
                while not self.stop_event.is_set():
                    if self.filepath_available_event.wait(1.0):
                        self.filepath_available_event.clear()
                        break

    def listen_for_file_header_update(self):
        while not self.stop_event.is_set():
            if self.file_header_receiver.poll():
                self.start_time, self.channel_bitmask, self.chunk_size = self.file_header_receiver.recv()
                logging.debug('StorageController: received header info, \n'
                              'start_time=%d, channel_bitmask=%d, chunk_size=%d',
                              self.start_time, self.channel_bitmask, self.chunk_size)
            else:
                while not self.stop_event.is_set():
                    if self.file_header_available_event.wait(1.0):
                        self.file_header_available_event.clear()
                        break

    def write_binary_files(self):
        filesize_threshold = 1000
        records_written = 0
        f = None

        while not self.stop_event.is_set():
            # wait to have something to write before we open a new file
            while not self.stop_event.is_set():
                if self.reading_to_be_stored_event.wait(1.0):
                    self.reading_to_be_stored_event.clear()
                    break
            if self.stop_event.is_set():
                break
            bytes_written = 0
            filename = time.strftime('%Y%m%d%H%M%S') + '.daqula'
            file_to_open = os.path.join(self.filepath, filename)
            logging.debug('StorageController: opening new binary file \n%s', file_to_open)
            f = open(file_to_open, 'wb')
            # print 'StorageController: opened a new file: %s' % filename
            f.write(str(self.start_time) + '\n')
            f.write(str(self.channel_bitmask) + '\n')
            f.write(str(self.chunk_size) + '\n')
            while bytes_written < filesize_threshold:
                if self.storage_receiver.poll():
                    reading = self.storage_receiver.recv()
                    f.write(reading + '\n')
                    records_written += 1
                    # for testing purposes only
                    if records_written >= self.expected_records:
                        with self.file_writer_done_cond:
                            self.file_writer_done_cond.notify()
                else:
                    timed_out = not self.reading_to_be_stored_event.wait(3.0)
                    if timed_out:
                        logging.debug('StorageController: writer thread timed out, closing file')
                        break
                    else:
                        self.reading_to_be_stored_event.clear()
                        continue
            f.close()
        if f is not None and not f.closed:
            logging.debug('StorageController: binary writer thread terminating, closing open file')
            f.close()


    # def writeHDF5files(self):
    #     timeout_threshold = 100000
    #     filesize_threshold = 512000
    #     chunk_size = 200
    #     records_written = 0
    #     write_buffer = []
    #     storage_type = np.dtype([('channel', 'S3'), ('value', 'uint64')])
    #
    #     while not self.stop_event.is_set():
    #         with self.file_writer_done_cond:
    #             if records_written >= self.expected_records:
    #                 self.file_writer_done_cond.notify()
    #
    #         if self.from_reader.poll():
    #             filename = time.strftime('%Y%m%d-%H:%M:%S')+'.h5'
    #             f = h5py.File(filename, 'a')
    #             # print 'new file created: %s' % filename
    #             timeout_counter = 0
    #             i = 0
    #
    #             while timeout_counter < timeout_threshold:
    #                 with self.file_writer_done_cond:
    #                     if records_written >= self.expected_records:
    #                         self.file_writer_done_cond.notify()
    #
    #                 if self.from_reader.poll():
    #                     timeout_counter = 0
    #                     reading = self.from_reader.recv()
    #                     # print 'SC recv\'d a reading'
    #                     write_buffer.append(reading.astype(storage_type))
    #                     if len(write_buffer) >= chunk_size:
    #                         f.create_dataset(str(i), data=write_buffer)
    #                         # print 'wrote dataset %d' % i
    #                         records_written += chunk_size
    #                         write_buffer = []
    #                         i += 1
    #                     if os.path.getsize(filename) > filesize_threshold:
    #                         # print 'file size %d exceeds limit, closing and starting new file' \
    #                         #       % os.path.getsize(filename)
    #                         f.close()
    #                         break
    #                 else:
    #                     timeout_counter += 1
    #             if timeout_counter >= timeout_threshold:
    #                 if len(write_buffer) > 0:
    #                     num_records = len(write_buffer)
    #                     # print 'buffer length to flush: %d' % len(write_buffer)
    #                     # print 'i = %d' % i
    #                     #write the partial buffer to file before closing
    #                     f.create_dataset(str(i), data=write_buffer)
    #                     records_written += num_records
    #                 f.close()
    #             # else continue while loop and create a new file
    #     if f is not None:
    #         # write remaining buffer to file and close before terminating thread
    #         if len(write_buffer) > 0:
    #             print 'buffer length to flush: %d' % len(write_buffer)
    #             print 'i = %d' % i
    #             # write the partial buffer to file before closing
    #             f.create_dataset(str(i), data=write_buffer)
    #         f.close()

    # def process_reading(self, reading):
    #     # reading[0] += self.start_time
    #     self.to_writer.send(reading)

    # def grabbuffer(self):
    #     while not self.stop_event.is_set():
    #         if self.storage_receiver.poll():
    #             reading = self.storage_receiver.recv()
    #             self.process_reading(reading)
    #         else:
    #             self.reading_to_be_stored_event.wait()