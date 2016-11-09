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

        # buffer for incoming data stream from socket
        self.incoming_queue = mp.Queue()

        # buffer between stream processing threads
        self.pipeline_queue = mp.Queue()

        self.recv_stop_event = threading.Event()
        self.receiver_thread = threading.Thread(target=self.receive_data, args=[self.recv_stop_event])
        self.sync_recovery_thread = threading.Thread(target=self.synchronize_stream, args=[self.recv_stop_event])
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

    def start_parser_thread(self):
        self.parser_thread.start()

    def update_active_channels(self, active_channels):
        self.active_channels = active_channels
        # print 'ACTIVE CHANNELS: %s' % self.active_channels

    def connect_data_port(self):
        # print 'DataClient: attempting connection'
        self.sock.connect((self.host, self.port))
        self.start_receiver_thread()
        self.start_sync_recovery_thread()
        self.start_parser_thread()
        self.connected = True

    def close_data_port(self):
        # print 'DataClient: close_control_port()'
        self.connected = False
        self.stop_data_threads()
        self.sock.close()

    def receive_data(self, *args):
        stop_event = args[0]
        while not stop_event.is_set():
            byte = self.sock.recv(1)
            if byte != '':
                self.incoming_queue.put(byte)

    def synchronize_stream(self, *args):
        # print '\n\nsync thread started'
        stop_event = args[0]
        self.synchronized = False
        in_timestamp = False
        realign_by_one = False
        temp_buffer = []
        # used in recovery process to store byte from previous iteration
        temp_byte = ''
        n = len(self.active_channels)

        while not stop_event.is_set():
            if self.incoming_queue.empty():
                continue

            # special logic to grab 48-bit timestamp
            if in_timestamp:
                # print 'gathering timestamp bytes'
                ts_bytes = []
                for i in range(6):
                    ts_byte = self.incoming_queue.get_nowait()
                    ts_bytes.append(ts_byte.encode('hex'))
                ts_value = int(ts_bytes[5] + ts_bytes[4] + ts_bytes[3] +
                               ts_bytes[2] + ts_bytes[1] + ts_bytes[0], 16)
                temp_buffer.append(ts_value)
                # print 'added timestamp, new buffer is %s' % temp_buffer
                in_timestamp = False

            # realign in case we got a stray byte somewhere and are off by one byte
            if realign_by_one:
                byte2_enc = temp_byte
                temp_byte = ''
                byte1 = self.incoming_queue.get_nowait()
                byte1_enc = byte1.encode('hex')
                realign_by_one = False
            else:
                byte2 = self.incoming_queue.get_nowait()
                byte2_enc = byte2.encode('hex')
                try:
                    byte1 = self.incoming_queue.get_nowait()
                    byte1_enc = byte1.encode('hex')
                except Queue.Empty:
                    # print 'incoming_queue empty, skipping to next iteration'
                    continue

            # merge the two byte strings and convert to an integer
            value = int(byte1_enc + byte2_enc, 16)
#             # print 'bytes: %s, %s' % (byte1_enc, byte2_enc)

            if not self.synchronized:
                if byte1_enc == 'de':
                    if byte2_enc == 'ad':
                        # we found a DEAD, let's see if it aligns with a previous DEAD
                        # print 'DEAD found, temp_buffer length is %d' % len(temp_buffer)
                        # we need to use '+ 4' here because the timestamp hasn't been recognized yet
                        if len(temp_buffer) >= (n + 4) and temp_buffer[-1 * (n + 4)] == 57005:  # 0xDEAD
                            self.synchronized = True
                            # print 'second DEAD reached, syncronized = True'
                            # flush the buffer to only include the new DEAD
                            temp_buffer = [value]
                            in_timestamp = True
                            continue
                        else:
                            # not in sync yet, store in buffer
                            # print 'no previous DEAD found, continuing...'
                            temp_buffer.append(value)
                            continue
                    else:
                        # no DEAD here, move along
                        temp_buffer.append(value)

                elif byte2_enc == 'de':
                    if temp_byte == 'ad': # where temp_byte is the byte1_enc from the prev iteration
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

            elif self.synchronized:
                if value == 57005:  # 0xDEAD
                    # print 'found a DEAD while synced'
                    # the '+ 2' accounts for the DEAD and timestamp
                    if len(temp_buffer) >= (n + 2) and temp_buffer[-1 * (n + 2)] == 57005:
                        # all good, still synced up
                        # push the most recent set of readings to the parsing stage
                        # print 'S&R: passing buffer to pipeline_queue'
                        self.pipeline_queue.put(temp_buffer)
                        temp_buffer = [value]  # flush the buffer
                        # grab the timestamp next time around
                        in_timestamp = True
                        continue
                    else:
                        # bad news, we're either out of sync or happened to read a DEAD
                        self.synchronized = False
                        temp_buffer.append(value)
                        continue
                elif byte2_enc == 'de' and temp_byte == 'ad':
                    # either we got really unlucky, or we've fallen out of sync again
                    # print 'split DEAD found, syncronized -> False'
                    value = int(byte2_enc + temp_byte, base=16)
                    temp_buffer = [value]
                    realign_by_one = True
                    self.synchronized = False
                    continue
                else:
                    # presumably this is a data reading, throw it in the buffer
                    temp_buffer.append(value)
                    # store byte1_enc in case we run into a split DEAD
                    temp_byte = byte1_enc
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
