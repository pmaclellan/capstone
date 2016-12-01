import socket
import select
import multiprocessing as mp
import numpy as np
import threading
import logging
from Queue import Full


class DataClient():
    def __init__(self, storage_sender, gui_data_queue, reading_to_be_stored_event, readings_to_be_plotted_event):

        # Pipe connection to send data readings to StorageController
        self.storage_sender = storage_sender

        # Pipe connection to send data readings to GUI
        self.gui_data_queue = gui_data_queue

        # list of channel strings (e.g. '0.0')
        self.active_channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7',
                                '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
                                '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                                '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7']

        self.reading_to_be_stored_event = reading_to_be_stored_event

        self.readings_to_be_plotted_event = readings_to_be_plotted_event

        # testing purposes only
        self.receiver_done_event = threading.Event()

        self.recv_stop_event = threading.Event()

        # Create worker threads
        self.receiver_thread = None

        self.connected = False
        self.synchronized = False
        self.synchronized_lock = threading.Lock()

        self.chunk_size = None

        # how many bytes are in self.chunk_size readings, including DEADs and timestamps
        self.chunk_byte_length = None

        self.bytes_received = 0
        self.expected_bytes_sent = 99999999
        self.expected_bytes_sent_lock = threading.Lock()

    def start_receiver_thread(self):
        self.receiver_thread = threading.Thread(target=self.receive_data, args=[self.recv_stop_event])
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def stop_data_threads(self):
        if self.receiver_thread is not None and self.receiver_thread.is_alive():
            self.recv_stop_event.set()
            self.receiver_thread.join()
            self.receiver_thread = None
        return True

    def get_channels_from_bitmask(self, bitmask):
        active_channels = []
        num_ADCs = 4
        num_channels_per_ADC = 8
        for adc in range(num_ADCs):
            for channel in range(num_channels_per_ADC):
                active = np.bitwise_and(np.left_shift(0x01, adc * num_channels_per_ADC + channel), bitmask)
                if active > 0:
                    active_channels.append(str(adc) + '.' + str(channel))
        return active_channels

    def connect_data_port(self, host, port, chunk_size, active_channels):
        self.chunk_size = chunk_size
        self.active_channels = active_channels
        self.chunk_byte_length = int((len(self.active_channels) + 4) * 2 * self.chunk_size)
        logging.info('DataClient: attempting connection on %s:%d', host, port)
        try:
            # initialize TCP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
        except socket.error as serr:
            logging.error('DataClient: failed to connect to host, exception is %s', serr)
            self.connected = False
            return (self.connected, serr)

        self.connected = True

        logging.info('DataClient: connected to %s:%d', host, port)
        logging.debug('DataClient: starting receiver thread')
        self.start_receiver_thread()
        return (self.connected, None)

    def close_data_port(self):
        logging.debug('DataClient: close_control_port() entered')
        self.connected = False
        data_threads_stopped = self.stop_data_threads()
        logging.info('DataClient: all threads terminated successfully')
        self.sock.close()
        logging.info('DataClient: data socket closed')
        return data_threads_stopped

    def receive_data(self, *args):
        stop_event = args[0]
        n = len(self.active_channels)
        realign_by_one = False
        temp_buffer = []
        carryover_buffer = bytearray(0)
        reading_byte_length = self.chunk_byte_length / self.chunk_size
        bytes_received = 0
        MB_received = 0

        while not stop_event.is_set():
            # If we are already in sync, take the fast path where we process readings
            # in full and simply check that the DEAD is where we expect it to be. If
            # it is not where we expect it, synchronized will be set to false and the
            # next iteration will send each byte through the recovery filter.
            if self.synchronized:
                # create a buffer to store DEAD, TS, and all channel values
                # if we didn't receive a full reading last time, subtract the carryover length from the total
                reading_buffer = bytearray(self.chunk_byte_length - len(carryover_buffer))

                # check to see if there is data available before calling recv_into() so we don't hang
                readable, writable, exceptional = select.select([self.sock], [], [], 1)
                if self.sock in readable:
                    bytes_recv = self.sock.recv_into(reading_buffer)
                    bytes_received += bytes_recv
                    if bytes_received > 10000000:
                        MB_received += bytes_received / 1000000
                        bytes_received = 0
                        logging.info('DataClient: %d MB received', MB_received)
                    reading_buffer = carryover_buffer + reading_buffer[:bytes_recv]
                    if len(reading_buffer) < self.chunk_byte_length:
                        carryover_buffer = reading_buffer
                    elif reading_buffer[0] == 173 and reading_buffer[1] == 222:  # 173 == 0xAD, 222 == 0xDE
                        # all good, found DEAD where we expected
                        # only send the first reading to GUI to avoid extra data transfer overhead
                        try:
                            self.gui_data_queue.put_nowait(reading_buffer[:reading_byte_length])
                        except Full:
                            pass
                        self.storage_sender.send(reading_buffer)
                        # notify the gui and storage controller that they have work to do
                        self.reading_to_be_stored_event.set()
                        # self.readings_to_be_plotted_event.set()
                        carryover_buffer = bytearray(0)
                    else:
                        self.synchronized = False

            else:
                logging.info('DataClient: out of sync, attempting to re-establish synchronization')
                while not self.synchronized:
                    if stop_event.is_set():
                        break
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

                    if bytes_received > 100000000:
                        MB_received += bytes_received / 1000000
                        bytes_received = 0

                    logging.debug('byte 1 = %s, byte2 = %s' % (byte1_enc, byte2_enc))

                    if value == 57005:
                        # we found a DEAD, let's see if it aligns with a previous DEAD
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
                            temp_buffer.append(value)
                            continue

                    elif byte2_enc == 'de':
                        if temp_byte == 'ad':  # where temp_byte is the byte1_enc from the prev iteration
                            # we found a DEAD, but we're misaligned by one byte
                            logging.debug('misaligned DEAD detected, attempting recovery')
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
                logging.debug('Recovery complete, back in sync! bytes_received = %d', bytes_received)
        logging.info('DataClient: receiver thread terminated, received %d MB', MB_received)
