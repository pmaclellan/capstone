import socket
import select
import multiprocessing as mp
import numpy as np
import threading
import Queue # just needed for the Empty exception


class DataClient():
    def __init__(self, host, port, storage_sender, gui_data_sender, reading_to_be_stored_cond, readings_to_be_plotted_cond):
        # initialize TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Pipe connection to send data readings to StorageController
        self.storage_sender = storage_sender

        # Pipe connection to send data readings to GUI
        self.gui_data_sender = gui_data_sender

        # list of channel strings (e.g. '0.0')
        self.active_channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7',
                                '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
                                '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                                '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7']

        self.reading_to_be_stored_cond = reading_to_be_stored_cond

        self.readings_to_be_plotted_cond = readings_to_be_plotted_cond

        # pipe for passing full readings (bytearray) from socket listener to sync verification filter
        self.fast_path_receiver, self.fast_path_sender = mp.Pipe(duplex=False)

        # pipe for passing full readings (bytearray) from sync verification filter to parser stage
        self.pipeline_receiver, self.pipeline_sender = mp.Pipe(duplex=False)

        # Condition variables
        self.receiver_done_cond = threading.Condition()
        self.sync_filter_done_cond = threading.Condition()
        self.parser_done_cond = threading.Condition()
        self.reading_available_to_parse_cond = threading.Condition()
        self.frame_to_be_verified_cond = threading.Condition()

        self.recv_stop_event = threading.Event()

        # Create worker threads
        self.receiver_thread = threading.Thread(target=self.receive_data, args=[self.recv_stop_event])
        self.receiver_thread.daemon = True
        self.sync_verification_thread = threading.Thread(target=self.verify_synchronization, args=[self.recv_stop_event])
        self.sync_verification_thread.daemon = True
        self.parser_thread = threading.Thread(target=self.parse_readings, args=[self.recv_stop_event])
        self.parser_thread.daemon = True

        self.host = host
        self.port = port
        self.connected = False
        self.synchronized = False
        self.synchronized_lock = threading.Lock()

        self.chunk_size = 20

        # for testing purposes only
        self.bytes_received = 0
        self.expected_bytes_sent = 99999999
        self.expected_bytes_sent_lock = threading.Lock()
        self.expected_readings_verified = 99999999
        self.expected_readings_verified_lock = threading.Lock()
        self.expected_readings_parsed = 99999999
        self.expected_readings_parsed_lock = threading.Lock()

    def start_receiver_thread(self):
        self.receiver_thread.start()

    def stop_data_threads(self):
        self.recv_stop_event.set()

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
        carryover_buffer = bytearray(0)
        bytes_received = 0

        while not stop_event.is_set():
            # print 'Receiver: bytes_received = %d' % bytes_received
            with self.expected_bytes_sent_lock:
                if bytes_received >= self.expected_bytes_sent:
                    with self.receiver_done_cond:
                        self.receiver_done_cond.notify()
            # If we are already in sync, take the fast path where we process readings
            # in full and simply check that the DEAD is where we expect it to be. If
            # it is not where we expect it, synchronized will be set to false and the
            # next iteration will send each byte through the recovery filter.
            with self.synchronized_lock:
                in_sync = self.synchronized

            if in_sync:
                # create a buffer to store DEAD, TS, and all channel values
                # if we didn't receive a full reading last time, subtract the carryover length from the total
                reading_buffer = bytearray((len(self.active_channels) + 4) * 2 * self.chunk_size - len(carryover_buffer))

                # check to see if there is data available before calling recv_into() so we don't hang
                readable, writable, exceptional = select.select([self.sock], [], [], 1)
                if self.sock in readable:
                    self.sock.recv_into(reading_buffer)
                    reading_buffer = carryover_buffer + reading_buffer
                    assert len(reading_buffer) == (len(self.active_channels) + 4) * 2 * self.chunk_size

                if reading_buffer[-1] != 0:
                    bytes_received += len(reading_buffer)
                    self.fast_path_sender.send(reading_buffer)
                    # notify sync verification thread that it has work to do
                    with self.frame_to_be_verified_cond:
                        self.frame_to_be_verified_cond.notify()
                else:
                    # didn't receive a full reading, or it happened to end in 0
                    # calculate how many non-zero bytes we actually received and carry those over
                    for i in range(len(reading_buffer)):
                        if reading_buffer[i] == 0:
                            bytes_received += i
                            carryover_buffer = reading_buffer[:i]
                            break

            else:
                # print 'out of sync'
                with self.synchronized_lock:
                    while not self.synchronized:
                        with self.expected_bytes_sent_lock:
                            if bytes_received >= self.expected_bytes_sent:
                                with self.receiver_done_cond:
                                    self.receiver_done_cond.notify()
                        # realign in case we got a stray byte somewhere and are off by one byte
                        if realign_by_one:
                            byte2_enc = temp_byte
                            temp_byte = ''

                            # check to see if there is data available before calling recv() so we don't hang
                            readable, writable, exceptional = select.select([self.sock], [], [])
                            if self.sock in readable:
                                byte1 = self.sock.recv(1)
                            if byte1 != '':
                                bytes_received += 1
                            else:
                                continue
                            byte1_enc = byte1.encode('hex')

                            realign_by_one = False
                        else:
                            readable, writable, exceptional = select.select([self.sock], [], [])
                            if self.sock in readable:
                                byte2 = self.sock.recv(1)
                            if byte2 != '':
                                bytes_received += 1
                            else:
                                continue
                            byte2_enc = byte2.encode('hex')

                            readable, writable, exceptional = select.select([self.sock], [], [])
                            if self.sock in readable:
                                byte1 = self.sock.recv(1)
                            if byte1 != '':
                                bytes_received += 1
                            else:
                                continue
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
                                counter = 0
                                while counter < (n + 3) * 2:
                                    byte = self.sock.recv(1)
                                    if byte != '':
                                        bytes_received += 1
                                        counter += 1
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
                # print 'Recovery complete, back in sync! bytes_received = %d' % bytes_received


    def verify_synchronization(self, *args):
        stop_event = args[0]
        readings_verified = 0

        while not stop_event.is_set():
            # for testing purposes only
            with self.expected_readings_verified_lock:
                if readings_verified >= self.expected_readings_verified:
                    with self.sync_filter_done_cond:
                        self.sync_filter_done_cond.notify()

            if self.fast_path_receiver.poll():
                reading = self.fast_path_receiver.recv()
                assert len(reading) == (len(self.active_channels) + 4) * 2 * self.chunk_size
                if reading[0] == 173 and reading[1] == 222: # 173 == 0xAD, 222 == 0xDE
                    # all good, found DEAD where we expected
                    self.pipeline_sender.send(reading)
                    readings_verified += 1
                    # notify the parser that it has work to do
                    with self.reading_available_to_parse_cond:
                        self.reading_available_to_parse_cond.notify()
                else:
                    with self.synchronized_lock:
                        self.synchronized = False
            else:
                # nothing to read yet
                with self.frame_to_be_verified_cond:
                    self.frame_to_be_verified_cond.wait()
                continue

    # Parser is in charge of transforming the list output from the Sync and Recovery
    # stage into a NumPy array for use in the GUI and StorageController
    def parse_readings(self, *args):
        stop_event = args[0]
        readings_parsed = 0

        while not stop_event.is_set():
            # for testing purposes only
            with self.expected_readings_parsed_lock:
                if readings_parsed >= self.expected_readings_parsed:
                    with self.parser_done_cond:
                        self.parser_done_cond.notify()

            # check that there is a reading to receive
            if self.pipeline_receiver.poll():
                raw_reading = self.pipeline_receiver.recv()
            else:
                with self.reading_available_to_parse_cond:
                    self.reading_available_to_parse_cond.wait()
                continue

            # make sure we have the proper number of data points
            assert len(raw_reading) == (len(self.active_channels) + 4) * 2 * self.chunk_size

            for n in range(self.chunk_size):
                start_index = n * (len(self.active_channels) + 4) * 2
                end_index = (n+1) * (len(self.active_channels) + 4) * 2
                one_reading = raw_reading[start_index:end_index]
                # extract the 48-bit timestamp value
                timestamp = (one_reading[7] << 40) + (one_reading[6] << 32) + (one_reading[5] << 24) + \
                            (one_reading[4] << 16) + (one_reading[3] << 8) + one_reading[2]

                # start building the list that will be converted to a numpy array later
                intermediate = [('_TS', timestamp)]

                # trim DEAD and timestamp from the reading
                one_reading = one_reading[8:]

                # construct tuple for each reading e.g. ('0.0', 43125) and add to list
                for i in range(0, len(one_reading), 2):
                    intermediate.append((self.active_channels[i/2], (one_reading[i + 1] << 8) + one_reading[i]))

                # create numpy array from list for passing to storage
                reading = np.array(intermediate, dtype=[('channel', 'S3'), ('value', 'uint64')])

                readings_parsed += 1

                # pass the reading along to the other components
                #TODO: uncomment these when the other sides are ready to receive

                # self.gui_data_sender.send(reading)
                # self.readings_to_be_plotted_cond.notify()
                # self.storage_sender.send(reading)
                # self.reading_to_be_stored_cond.notify()
