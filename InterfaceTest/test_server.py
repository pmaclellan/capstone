import socket
import control_signals_pb2
import sys
import time
import threading

## Global Variables ##
hosting_addr = 'localhost'
control_port = 5000
data_port = control_port + 1
handshake_port = 0

# Helper Function
def _delay(seconds):
	for i in range(seconds):
		time.sleep(1)
		print '...'

def transmitAdcData():
	print('OPEN: data port on %d' % data_port)
	# Initialize a new socket for the data connection
	data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Bind and listen on localhost
	data_sock.bind((hosting_addr, data_port))
	data_sock.listen(1)
	print('LISTEN: (data) on port %d...' % data_port )

	# Accept a client connection
	data_conn, addr = data_sock.accept()
	print('ACCEPT: (data) connection from %s' % str(addr))

	while True:
		data_conn.send(str(0xDEAD))
		time.sleep(1)

# Construct a PbStartRequest container
startRequest = control_signals_pb2.StartRequest()

# Create a TCP socket object
control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind and listen on localhost
print('BIND: attempting with port %d' % control_port)
control_sock.bind((hosting_addr, control_port))

while True:
	control_sock.listen(1)
	print('LISTEN: (status) on port %d...' % control_port )

	# Accept a client connection
	control_conn, addr = control_sock.accept()
	print('ACCEPT: (status) connection from %s' % str(addr))

	length = ''
	try:
		while length == '':
			# Read incoming length header
			length = control_conn.recv(2)
			print('RECV: length %s' % length)
	except Exception, e:
		print e

	try:
		# Read transmission of binary object stream (protobuf)
		protomsg = control_conn.recv(int(length))
	except Exception, e:
		print('ERROR: receiving message object\n%s' % e)

	try:
		# Reconstruct the PbStartRequest object form the binary transmission
		startRequest.ParseFromString(protomsg)
		print('RECV: StartRequest message:')
		print(startRequest)
	except Exception, e:
		print('ERROR: parsing PbStartRequest messsage\n%s' % e)

	# Test some known attribute to indicate an initial handshake message
	if startRequest.port == handshake_port:
		# Run the data transmission on another thread
		transmit_thread = threading.Thread(target=transmitAdcData)
		transmit_thread.daemon = True
		transmit_thread.start()

		_delay(3)
		# Construct an acknowledgement message with the proposed port
		ackStartRequest = control_signals_pb2.StartRequest()
		ackStartRequest.port = data_port

		# TODO: actually report working channels
		ackStartRequest.channels = startRequest.channels
		# ^^^^:
		
		serialized = ackStartRequest.SerializeToString()

		# Send the modified object back to the client (*port number*)
		control_conn.send(str(sys.getsizeof(serialized)))
		print('SEND: next transmission length: %s' % str(sys.getsizeof(serialized)))

		control_conn.send(serialized)
		print('SEND: serialized StartRequest message')