from control_client import ControlClient
from data_client import DataClient
import control_signals_pb2

import multiprocessing as mp
import numpy as np
import threading
import asyncore
import bisect
import logging


class NetworkController(mp.Process):
    def __init__(self, storage_sender, gui_control_conn, gui_data_queue, file_header_sender,
                 file_header_available_event, reading_to_be_stored_event, readings_to_be_plotted_event,
                 control_msg_from_gui_event, control_msg_from_nc_event):
        super(NetworkController, self).__init__()

        # mp.Connection for sending readings from DataClient to StorageController
        self.storage_sender = storage_sender

        # mp.Connection for sending  and receiving control messages (protobufs) back and forth to GUI
        # Note: full duplex Pipe
        self.gui_control_conn = gui_control_conn

        # mp.Connection for sending ADC readings to GUI for plotting
        self.gui_data_queue = gui_data_queue

        # mp.Connection for sending start_time, channel_bitmask, and chunk_size to SC
        self.file_header_sender = file_header_sender

        # IPC condition variables
        self.file_header_available_event = file_header_available_event
        self.reading_to_be_stored_event = reading_to_be_stored_event
        self.readings_to_be_plotted_event = readings_to_be_plotted_event

        # mp.Condition variable for wait/notify on duplex control message connection GUI <--> NC
        self.control_msg_from_gui_event = control_msg_from_gui_event
        self.control_msg_from_nc_event = control_msg_from_nc_event

        # used to stop listener threads and terminate the process gracefully
        self.stop_event = mp.Event()

        # used to stop asyncore loop on disconnect
        self.disconnect_event = mp.Event()

        # mp.Event variable for ControlClient to notify NC that an ACK is available
        self.ack_msg_from_cc_event = mp.Event()

        # threading.Event variable to wait on for async client to connect
        self.control_client_connected_event = threading.Event()
        self.control_client_disconnected_event = threading.Event()

        # shared with control client, sends request messages to be sent over TCP
        # receives ACK messages
        self.nc_control_conn, self.cc_control_conn = mp.Pipe(duplex=True)

        # control client will write ACK'd requests here
        self.ack_queue = mp.Queue()

        # default to all channels being active
        # NOTE: this needs to match up with the default state of the channel checkboxes on GUI
        # and needs to be propagated to DataClient upon any change
        self.active_channels = ['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7',
                                '1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7',
                                '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                                '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7']

        # host and port will be extracted from GUI connect message
        self.host = ''
        self.port = 0

        # used to keep track of messages that have been sent to ControlClient but not yet ACKed
        self.sent_dict = {}

        self.control_client = ControlClient(control_protobuf_conn=self.cc_control_conn,
                                            ack_msg_from_cc_event=self.ack_msg_from_cc_event,
                                            connected_event=self.control_client_connected_event,
                                            disconnected_event=self.control_client_disconnected_event)

        self.data_client = DataClient(gui_data_queue=self.gui_data_queue,
                                      storage_sender=self.storage_sender,
                                      reading_to_be_stored_event=self.reading_to_be_stored_event,
                                      readings_to_be_plotted_event=self.readings_to_be_plotted_event)

        self.stop_listener_thread = threading.Thread(target=self.listen_for_stop_event)

        # receives request protobuf messages triggered by GUI events
        self.gui_receiver_thread = threading.Thread(target=self.recv_from_gui)
        self.gui_receiver_thread.daemon = True

        # listens for ACK messages being passed back from control client
        self.ack_listener_thread = threading.Thread(target=self.read_ack_messages)
        self.ack_listener_thread.daemon = True

        # handle asyncore blocking loop in a separate thread
        # NOTE: lambda needed so loop() doesn't get called right away and block
        # 1.0 sets the polling frequency (default=30.0)
        # use_poll=True is a workaround to avoid "bad file descriptor" upon closing
        # for python 2.7.X according to GitHub Issue...but it still gives the error
        # self.loop_thread = threading.Thread(target=self.asyncore_loop)
        # self.loop_thread.daemon = True

    def run(self):
        self.stop_listener_thread.start()
        self.gui_receiver_thread.start()
        self.ack_listener_thread.start()
        self.gui_receiver_thread.join()
        logging.debug('NetworkController: gui_receiver thread joined')
        self.ack_listener_thread.join()
        logging.debug('NetworkController: ack_listener thread joined')
        logging.info('NetworkController finished running')

    def listen_for_stop_event(self):
        # block until stop_event gets set externally
        self.stop_event.wait()
        self.close_data_port()
        self.close_control_port()

    def connect_control_port(self, host, port):
        logging.debug('NetworkController: connect_control_port() entered')
        if self.control_client is not None and not self.control_client.connected:
            success, serr = self.control_client.connect_control_port(host, port)
            self.loop_thread = threading.Thread(target=self.asyncore_loop)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            return (success, serr)

    def connect_data_port(self, host, port, chunk_size, active_channels):
        logging.debug('NetworkController: connect_data_port() entered')
        if self.data_client is not None and not self.data_client.connected:
            return self.data_client.connect_data_port(host, port, chunk_size, active_channels)

    def close_control_port(self):
        logging.debug('NetworkController: attempting to close control port')
        if self.data_client.connected:
            self.data_client.close_data_port()
        self.control_client.close_control_port()
        if self.loop_thread.is_alive():
            self.disconnect_event.set()
            asyncore.close_all()
            self.loop_thread.join()
        logging.info('NetworkController: control and data ports closed')

    def close_data_port(self):
        logging.debug('NetworkController: attempting to close data port')
        return self.data_client.close_data_port()

    def asyncore_loop(self):
        while not self.stop_event.is_set() and not self.disconnect_event.is_set():
            asyncore.loop(timeout=1.0, count=1, use_poll=True)
        self.disconnect_event.clear()
        logging.debug('NetworkController: asyncore loop thread finished')

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

    def recv_from_gui(self):
        while not self.stop_event.is_set():
            if self.gui_control_conn.poll():
                msg = self.gui_control_conn.recv()
                logging.info('NetworkController: received control message: \n%s', msg)

                if msg['type'] == 'CONNECT':
                    # TODO: input validation
                    self.host = msg['host']
                    self.port = msg['port']

                    success, serr = self.connect_control_port(self.host, self.port)

                    if not success:
                        # ControlClient connect failed, notify GUI
                        reply_msg = msg
                        reply_msg['success'] = False
                        reply_msg['message'] = 'Failed to connect ControlClient to %s:%d, error is %s' % \
                                               (self.host, self.port, serr)
                        self.gui_control_conn.send(reply_msg)
                        self.control_msg_from_nc_event.set()
                    else:
                        # construct a StartRequest protobuf message
                        startRequest = control_signals_pb2.StartRequest()
                        startRequest.port = self.port + 1
                        startRequest.channels = msg['channels']
                        startRequest.rate = msg['rate']

                        # wrap it up and copy sequence number
                        requestWrapper = control_signals_pb2.RequestWrapper()
                        requestWrapper.sequence = msg['seq']
                        requestWrapper.start.MergeFrom(startRequest)

                        # serialize wrapper for sending over Pipe
                        serialized = requestWrapper.SerializeToString()
                        self.nc_control_conn.send(serialized)
                        logging.debug('NetworkController: sent serialized requestWrapper to CC')
                        # ControlClient uses asyncore so we don't need to notify it

                        if msg['seq'] not in self.sent_dict.keys():
                            self.sent_dict[msg['seq']] = msg
                        else:
                            raise RuntimeWarning('NetworkController: control msg with sequence %d already in sent_dict'
                                                 % msg['seq'])

                        # asyncore client doesn't connect until it tries to recv/send,
                        # so we need to be notified asynchronously
                        control_client_connected = self.control_client_connected_event.wait(timeout=5.0)
                        self.control_client_connected_event.clear()

                        if not control_client_connected:
                            # ControlClient connect timed out, notify GUI
                            reply_msg = msg
                            reply_msg['success'] = False
                            reply_msg['message'] = 'Timed out while trying to connect ControlClient to %s:%d' % \
                                                   (self.host, self.port)
                            self.gui_control_conn.send(reply_msg)
                            self.control_msg_from_nc_event.set()

                elif msg['type'] == 'DISCONNECT':
                    # construct a StopRequest protobuf message
                    stopRequest = control_signals_pb2.StopRequest()
                    stopRequest.port = self.port + 1
                    stopRequest.channels = 0xffff

                    # wrap it up and copy sequence number
                    requestWrapper = control_signals_pb2.RequestWrapper()
                    requestWrapper.sequence = msg['seq']
                    requestWrapper.stop.MergeFrom(stopRequest)

                    # serialize wrapper for sending over Pipe
                    serialized = requestWrapper.SerializeToString()
                    self.nc_control_conn.send(serialized)
                    logging.debug('NetworkController: sent serialized requestWrapper to CC')
                    # ControlClient uses asyncore so we don't need to notify it

                    if msg['seq'] not in self.sent_dict.keys():
                        self.sent_dict[msg['seq']] = msg
                    else:
                        raise RuntimeWarning('NetworkController: control msg with sequence %d already in sent_dict'
                                             % msg['seq'])

            else:
                while not self.stop_event.is_set():
                    if self.control_msg_from_gui_event.wait(1.0):
                        self.control_msg_from_gui_event.clear()
                        break

    def read_ack_messages(self):
        while not self.stop_event.is_set():
            if self.nc_control_conn.poll():
                ack = self.nc_control_conn.recv()
                ack_wrapper = control_signals_pb2.RequestWrapper()
                ack_wrapper.ParseFromString(ack)
                logging.info('NetworkController: received ACK message %s', ack_wrapper)

                if ack_wrapper.sequence in self.sent_dict.keys():
                    msg = self.sent_dict.pop(ack_wrapper.sequence)
                else:
                    msg = {}
                    raise RuntimeWarning('NetworkController: received unexpected ACK from ControlClient')

                if ack_wrapper.HasField('start') and not self.data_client.connected:
                    logging.info('NetworkController: received start ACK, starting data client')
                    start_request = control_signals_pb2.StartRequest()
                    start_request.MergeFrom(ack_wrapper.start)
                    # make sure that we're getting the channels we expect
                    if start_request.channels != msg['channels']:
                        raise RuntimeWarning('NetworkController: active channels in ACK differ from requested')

                    # send header info to SC and notify
                    active_channels = self.get_channels_from_bitmask(start_request.channels)
                    bytes_per_sample = (len(active_channels) + 4) * 2
                    chunk_size = min(113, int(msg['rate'] * bytes_per_sample * 0.00001))
                    print 'received timestamp %d' % start_request.timestamp
                    header = (start_request.timestamp,
                            start_request.channels,
                            chunk_size,
                            start_request.rate)
                    self.file_header_sender.send(header)
                    self.file_header_available_event.set()

                    data_connect_success, data_serr = self.connect_data_port(self.host, start_request.port, chunk_size, active_channels)

                    logging.debug('NetworkController: data_connect_success = %s', data_connect_success)

                    if data_connect_success:
                        # construct a success reply message
                        reply_msg = msg
                        reply_msg['success'] = True
                        reply_msg['message'] = 'Successfully connected control and data ports to host %s' % self.host
                        reply_msg['timestamp'] = start_request.timestamp
                        reply_msg['chunk'] = chunk_size

                        # send an ACK message to GUI and notify its receiver
                        self.gui_control_conn.send(reply_msg)
                        self.control_msg_from_nc_event.set()

                    else:
                        # construct a failure reply message
                        reply_msg = msg
                        reply_msg['success'] = False
                        reply_msg['message'] = 'Failed to connect DataClient to %s:%d, error is %s' % \
                                               (self.host, start_request.port, data_serr)

                        self.gui_control_conn.send(reply_msg)
                        self.control_msg_from_nc_event.set()

                elif ack_wrapper.HasField('stop') and self.data_client.connected:
                    data_port_disconnected = self.close_data_port()
                    self.close_control_port()
                    control_port_disconnected = self.control_client_disconnected_event.wait(timeout=5.0)
                    self.control_client_disconnected_event.clear()
                    if data_port_disconnected and control_port_disconnected:
                        reply_msg = msg
                        reply_msg['success'] = True
                        reply_msg['message'] = 'Control and Data clients disconnected successfully'
                        self.gui_control_conn.send(reply_msg)
                        self.control_msg_from_nc_event.set()
                    else:
                        reply_msg = msg
                        reply_msg['success'] = False
                        reply_msg['message'] = 'Unable to disconnect properly or control client disconnect timed out'
                        self.gui_control_conn.send(reply_msg)
                        self.control_msg_from_nc_event.set()

                else:
                    logging.warning('NetworkController: received an unexpected ACK type %s', ack_wrapper)

            else:
                while not self.stop_event.is_set():
                    if self.ack_msg_from_cc_event.wait(1.0):
                        self.ack_msg_from_cc_event.clear()
                        break
