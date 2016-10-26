import socket
import control_signals_pb2
import sys
import time

## Global Variables ##
hosting_addr = 'localhost'
control_port = 50000
data_port = control_port + 1
handshake_port = 0

# Construct a PbStartRequest container
startRequest = control_signals_pb2.StartRequest()

# Create a TCP socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind and listen on localhost
sock.bind((hosting_addr, control_port))
sock.listen(1)
print('LISTEN: (stat) on port %d...' % control_port )

time.sleep(1)
print '...'
time.sleep(1)
print '...'
time.sleep(1)
print '...'

# Accept a client connection
conn, addr = sock.accept()
print('ACCEPT: connection from %s' % str(addr))

time.sleep(1)
print '...'
time.sleep(1)
print '...'
time.sleep(1)
print '...'

length = ''
while length == '':
	# Read incoming length header
	length = conn.recv(2)
	print('RECV: length %s' % length)

# Read transmission of binary object stream (protobuf)
protomsg = conn.recv(int(length))

# Reconstruct the PbStartRequest object form the binary transmission
startRequest.ParseFromString(protomsg)
print('RECV: StartRequest message:')
print(startRequest)

time.sleep(1)
print '...'
time.sleep(1)
print '...'
time.sleep(1)
print '...'

# Test some known attribute to indicate an initial handshake message
if startRequest.port == handshake_port:
	print('OPEN: data port on %d' % data_port)
	# Initialize a new socket for the data connection
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Bind and listen on localhost
	sock.bind((hosting_addr, data_port))
	sock.listen(1)
	print('LISTEN: (data) on port %d...' % data_port )

	# Construct an acknowledgement message with the proposed port
	ackStartRequest = control_signals_pb2.StartRequest()
	ackStartRequest.port = data_port

	# TODO: actually report working channels
	ackStartRequest.channels = startRequest.channels
	# ^^^^:
	
	serialized = ackStartRequest.SerializeToString()

	# Send the modified object back to the client (*port number*)
	conn.send(str(sys.getsizeof(serialized)))
	print('SEND: next transmission length: %s' % str(sys.getsizeof(serialized)))

	time.sleep(1)
	print '...'
	time.sleep(1)
	print '...'
	time.sleep(1)
	print '...'

	conn.send(serialized)
	print('SEND: serialized StartRequest message')