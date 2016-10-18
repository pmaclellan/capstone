import Queue
import socket
import bisect
import numpy as np
import threading

import custom_signals
import control_signals_pb2

class DaqConnection:
    def __init__(self, parent):
        self.parentWindow = parent
        self.queue = Queue.Queue()
        self.sig = custom_signals.CustomSignal()
        self.sig.connected.connect(lambda: self.parentWindow.setStatusBarMessage('Connected'))
        self.sig.connected.connect(lambda: self.parentWindow.daqWidget.toggleConnectionButtons(self.connected))
        self.sig.disconnected.connect(lambda: self.parentWindow.setStatusBarMessage('Disconnected'))
        self.sig.disconnected.connect(lambda: self.parentWindow.daqWidget.toggleConnectionButtons(self.connected))
        self.sig.new_data.connect(self.parentWindow.forward_to_plot)
        self.connected = False
        self.server_address = ('192.168.211.18X', 10001)
        self.data_port = 0
        self.active_channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7',
                                '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
                                '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                                '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7',]
        self.channel_mask = self.generateChannelBitMask()

    def update_server_address(self, string):
        self.server_address = string, 10001

    def processChannelUpdate(self, sender, checked):
        if checked:
            if sender.text() not in self.active_channels:
                bisect.insort(self.active_channels, str(sender.text()))
        else:
            if sender.text() in self.active_channels:
                self.active_channels.remove(sender.text())

        print(self.active_channels)
        self.channel_mask = self.generateChannelBitMask()
        print(self.channel_mask)
        # TODO: find a way to check if socket is still open
        if checked:
            startRequest = control_signals_pb2.StartRequest()
            startRequest.port = self.data_port
            startRequest.channels = self.channel_mask
            if self.connected:
                self.control_sock.send(startRequest.SerializeToString())
        else:
            stopRequest = control_signals_pb2.StopRequest()
            stopRequest.port = self.data_port
            stopRequest.channels = self.channel_mask
            if self.connected:
                self.control_sock.send(stopRequest.SerializeToString())

    def generateChannelBitMask(self):
        bit_mask = np.uint32(0)
        offset = 0
        for i in range(4):
            for j in range(8):
                if (str(i) + '.' + str(j)) in self.active_channels:
                    # bit_mask |= 0x01 << offset
                    bit_mask = np.bitwise_or(bit_mask, np.left_shift(np.uint32(1), offset))
                else:
                    # bit_mask &= ~(0x01 << offset)
                    bit_mask = np.bitwise_and(bit_mask, np.bitwise_not(np.left_shift(np.uint32(1), offset)))
                offset += 1
        return bit_mask


    def connect_to_server(self):
        # Create a TCP/IP socket
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.control_sock.connect(self.server_address)
            self.connected = True
            self.sig.connected.emit()
        except Exception, e:
            print("Something's wrong with %s. Exception type is %s" % (self.server_address, e))
            self.parentWindow.setStatusBarMessage("Unable to connect to server at %s:%s" % self.server_address)

        startRequest = control_signals_pb2.StartRequest()
        startRequest.port = 0
        startRequest.channels = self.channel_mask
        try:
            self.control_sock.send(startRequest.SerializeToString())
            handshake_buffer = bytearray(256)
            self.control_sock.recv_into(handshake_buffer)
            reply = control_signals_pb2.StartRequest()
            reply.ParseFromString(handshake_buffer)
            self.data_port = reply.port
            self.data_sock.connect(self.server_address[0], reply.port)
            self.receiver_thread = threading.Thread(target=self.listen_for_data)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()
        except Exception, e:
            print("Something's wrong with %s. Exception type is %s" % (self.server_address, e))
            self.parentWindow.setStatusBarMessage("Unable to establish data stream on secondary port")

    def disconnect_from_server(self):
        if self.control_sock is not None:
            self.control_sock.close()
            self.connected = False
            self.sig.disconnected.emit()

    def listen_for_data(self):
        synchronized = False
        temp_buffer = []
        temp_byte = '00000000'
        readings = {}
        block_offset = 0 # which reading we are currently expecting: 0 -> (n-1) **NOTE: DEAD and TS not counted

        while True:
            if self.data_sock: # TODO: dual-socket system
                n = len(self.active_channels)  # number of channels
                incoming_buffer = bytearray(b' ' * 512)  # create "empty" buffer to store incoming data
                self.data_sock.recv_into(incoming_buffer)
                i = 0
                while i+1 < len(incoming_buffer) and incoming_buffer[i+1] != b' ':
                    # convert each byte to binary strings
                    byte1 = '{:08b}'.format(incoming_buffer[i + 1])
                    byte2 = '{:08b}'.format(incoming_buffer[i])
                    binary = byte1 + byte2
                    value = int(binary, base=2)
                    if value == 8224:
                        break
                    if not synchronized:
                        if byte1 == '11011110': # 0xDE
                            if byte2 == '10101101': # 0xAD
                                # we found a DEAD, let's see if it aligns with a previous DEAD
                                if len(temp_buffer) >= (n + 2) and temp_buffer[-1 * (n + 2)] == 57005: # 0xDEAD
                                    synchronized = True
                                    # flush the buffer to only include the new DEAD
                                    temp_buffer = [value]
                                    temp_buffer.append(0) # TODO: placeholder for timestamp
                                    # reset readings just to be sure
                                    readings = {}
                                    i += 4 #just skip over the timestamp bytes for now
                                    continue
                                else:
                                    # not in sync yet, store in buffer
                                    temp_buffer.append(value)
                                    i += 2
                                    continue
                            else:
                                # no DEAD here, move along
                                temp_buffer.append(value)
                        elif byte2 == '11011110': # 0xDE
                            # carry = True
                            if temp_byte == '10101101': # 0xAD where temp_byte is the byte1 from the prev iteration
                                # we found a DEAD, but we're misaligned by one byte
                                # reconstruct binary string with the DEAD together
                                binary = byte2 + temp_byte
                                value = int(binary, base=2)
                                temp_buffer.append(value)
                                i += 1 # only move ahead by one byte to realign ourselves
                                # We can't be sure we're back in sync yet, need to wait until the next DEAD
                                continue
                            else:
                                temp_buffer.append(value)
                                i += 2
                                continue
                        else:
                            # we've got nothing, throw it in the buffer and better luck next time
                            temp_buffer.append(value)
                            i += 2
                            # but wait, let's save byte1 in case we're off by one...
                            temp_byte = byte1
                            continue

                    elif synchronized:
                        if value == 57005: # 0xDEAD
                            if len(temp_buffer) >= (n + 2) and temp_buffer[-1 * (n + 2)] == 57005:
                                # all good, still synced up
                                temp_buffer = [value] # flush the buffer
                                temp_buffer.append(0) # TODO: placeholder for timestamp
                                block_offset = 0
                                i += 4 #skip the timestamp bytes for now
                                continue
                            else:
                                # well fuck, we're either out of sync or happened to read a DEAD
                                synchronized = False
                                temp_buffer.append(value)
                                i += 2
                                continue
                        else:
                            readings[self.active_channels[block_offset]] = value
                            i += 2
                            block_offset += 1
                            if block_offset >= n:
                                # self.queue.put(readings) # TODO: define new queue that holds dictionaries
                                self.sig.new_data.emit(readings)
                                print(readings)
                                readings = {} # clear readings before starting next block
                                block_offset = 0
                                # NOTE: block_offset will be reset when we hit another 0xDEAD
                            continue

    def yield_data_point(self):
        if not self.queue.empty():
          yield self.queue.get()
        else:
          print("No more data!")