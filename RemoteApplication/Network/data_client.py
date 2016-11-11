import socket
import multiprocessing as mp
import numpy as np
import threading
import Queue # just needed for the Empty exception


class DataClient():
    def __init__(self, host, port, storage_queue, gui_data_queue, active_channels):
        # initialize TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # buffer between NetworkController and StorageController
        self.storage_queue = storage_queue

        # buffer between NetworkController and GUI
        self.gui_queue = gui_data_queue

        # list of channel strings (e.g. '0.0')
        self.active_channels = active_channels

        # pipe for passing full readings from socket listener to first stage of pipeline
        self.fast_path_receiver, self.fast_path_sender = mp.Pipe(duplex=False)

        # pipe for passing individual bytes from socket listener to sync & recovery filter
        self.slow_path_receiver, self.slow_path_sender = mp.Pipe(duplex=False)

        # buffer between stream processing threads
        self.pipeline_queue = mp.Queue()

        self.recv_stop_event = threading.Event()
        self.receiver_thread = threading.Thread(target=self.receive_data, args=[self.recv_stop_event])
        self.sync_recovery_thread = threading.Thread(target=self.synchronize_stream, args=[self.recv_stop_event])
        self.sync_verification_thread = threading.Thread(target=self.verify_synchronization, args=[self.recv_stop_event])
        self.parser_thread = threading.Thread(target=self.parse_readings, args=[self.recv_stop_event])

        self.host = host
        self.port = port
        self.connected = False
        self.synchronized = False

    def start_receiver_thread(self):
        self.receiver_thread.start()

    def stop_data_threads(self):
        self.recv_stop_event.set()

    def start_sync_recovery_thread(self):
        self.sync_recovery_thread.start()

    def start_sync_verification_thread(self):
        self.sync_verification_thread.start()

    def start_parser_thread(self):
        self.parser_thread.start()

    def update_active_channels(self, active_channels):
        self.active_channels = active_channels
        # print 'ACTIVE CHANNELS: %s' % self.active_channels

    def connect_data_port(self):
        # print 'DataClient: attempting connection'
        self.sock.connect((self.host, self.port))
        self.start_receiver_thread()
        self.start_sync_verification_thread()
        self.start_parser_thread()
        self.connected = True

    def close_data_port(self):
        # print 'DataClient: close_control_port()'
        self.connected = False
        self.stop_data_threads()
        self.sock.close()

    def receive_data(self, *args):
        stop_event = args[0]
        n = len(self.active_channels)
        realign_by_one = False
        temp_buffer = []

        while not stop_event.is_set():
            # for testing purposes only
            self.receive_flag = True

            # If we are already in sync, take the fast path where we process readings
            # in full and simply check that the DEAD is where we expect it to be. If
            # it is not where we expect it, synchronized will be set to false and the
            # next iteration will send each byte through the recovery filter.
            if self.synchronized:
                # create a buffer to store DEAD, TS, and all channel values
                reading_buffer = bytearray(len(self.active_channels) * 2 + 8)
                self.sock.recv_into(reading_buffer)
                if reading_buffer[-1] != 0:
                    self.fast_path_sender.send(reading_buffer)

            else:
                while not self.synchronized:
                    # realign in case we got a stray byte somewhere and are off by one byte
                    if realign_by_one:
                        byte2_enc = temp_byte
                        temp_byte = ''
                        byte1 = self.sock.recv(1)
                        byte1_enc = byte1.encode('hex')
                        realign_by_one = False
                    else:
                        byte2 = self.sock.recv(1)
                        byte2_enc = byte2.encode('hex')
                        byte1 = self.sock.recv(1)
                        byte1_enc = byte1.encode('hex')

                    # merge the two byte strings and convert to an integer
                    value = int(byte1_enc + byte2_enc, 16)
                    #             # print 'bytes: %s, %s' % (byte1_enc, byte2_enc)

                    if value == 57005:
                        # we found a DEAD, let's see if it aligns with a previous DEAD
                        # print 'DEAD found, temp_buffer length is %d' % len(temp_buffer)
                        # we need to use '+ 4' here because the timestamp hasn't been recognized yet
                        if len(temp_buffer) >= (n + 4) and temp_buffer[-1 * (n + 4)] == 57005:  # 0xDEAD
                            self.synchronized = True

                            # reset temp_buffer so we start fresh next time we need to recover
                            temp_buffer = []

                            # We are now sitting after the DEAD, but we want to align to the next DEAD.
                            # Receive and throw away the timestamp bytes and n ADC values.
                            # Do it one byte at a time because recv() only guarantees up to that many bytes
                            # will be read, not exactly that many.
                            for i in range((n + 3) * 2):
                                self.sock.recv(1)
                            continue
                        else:
                            # not in sync yet, store in buffer
                            # print 'no previous DEAD found, continuing...'
                            temp_buffer.append(value)
                            continue

                    elif byte2_enc == 'de':
                        if temp_byte == 'ad':  # where temp_byte is the byte1_enc from the prev iteration
                            # we found a DEAD, but we're misaligned by one byte
                            # print 'misaligned DEAD detected, attempting recovery'
                            # reconstruct binary string with the DEAD together
                            value = int(byte2_enc + temp_byte, base=16)
                            temp_buffer = [value]
                            realign_by_one = True
                            # We can't be sure we're back in sync yet, need to wait until the next DEAD
                            continue
                        else:
                            # just happened to find a 'de' in one of the readings, carry on
                            temp_buffer.append(value)
                            continue

                    else:
                        # we've got nothing, throw it in the buffer and better luck next time
                        temp_buffer.append(value)
                        # but wait, let's save byte1 in case we're off by one...
                        temp_byte = byte1_enc
                        continue

    def verify_synchronization(self, *args):
        stop_event = args[0]

        while not stop_event.is_set():
            if self.fast_path_receiver.poll():
                reading = self.fast_path_receiver.recv()
                assert len(reading) == len(self.active_channels) * 2 + 8
                if reading[0] == 173 and reading[1] == 222: # 173 == 0xAD, 222 == 0xDE
                    # all good, found DEAD where we expected
                    self.pipeline_queue.put(reading)
                else:
                    self.synchronized = False
            else:
                # nothing to read yet
                continue

    # Parser is in charge of transforming the list output from the Sync and Recovery
    # stage into a NumPy array for use in the GUI and StorageController
    def parse_readings(self, *args):
        stop_event = args[0]
        while not stop_event.is_set():
            try:
                buffer = self.pipeline_queue.get_nowait()
            except Queue.Empty:
                continue

            # make sure we have the proper number of data points
            assert len(buffer) == len(self.active_channels) + 2

            # start by grabbing the timestamp and putting it in a temp list
            intermediate = [('_TS', buffer[1])]

            # trim DEAD and timestamp from the buffer
            buffer = buffer[2:]

            # construct tuple for each reading e.g. ('0.0', 43125) and add to list
            for i in range(len(buffer)):
                intermediate.append((self.active_channels[i], buffer[i]))

            # create numpy array from list for passing to storage
            reading = np.array(intermediate, dtype=[('channel', 'S3'), ('value', 'uint64')])

            # pass the reading along to the other components
            self.gui_queue.put(reading)
            self.storage_queue.put(reading)

