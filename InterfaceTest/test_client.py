import socket
import control_signals_pb2
import sys
import time

server_addr = 'localhost'
control_port = 5000

# Helper Function
def _delay(seconds):
	for i in range(seconds):
		time.sleep(1)
		print '...'

# Create a TCP socket object
controlSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to localhost server
controlSock.connect((server_addr, control_port))
print('Connected to server at %s:%d' % (server_addr, control_port))

# Construct a PbStartRequest object (protobuf)
pbStartRequest = control_signals_pb2.StartRequest()
pbStartRequest.port = 0
pbStartRequest.channels = 0xFFFFFFFF

# serialize the contructed PbStartRequest for sending over the wire
serialized = pbStartRequest.SerializeToString()

# Send the transmission length to the server
controlSock.send(str(sys.getsizeof(serialized)))
print('sent size %d' % sys.getsizeof(serialized))

# Send the serialized protobuf message
controlSock.send(serialized)
print('sent message payload %s' % serialized)

# Receive the response from server in two parts:
# 1) length of incoming transmission
# 2) protobuf response message (PbStartRequest)

length = ''
while length == '':
	length = controlSock.recv(2)
	print('received msg length %s' % length)

msg = controlSock.recv(int(length))

# Reconstruct the PbStartRequest message from the binary
pbStartRequest.ParseFromString(msg)
print('StartRequest Message received:')
print(pbStartRequest)

data_port = pbStartRequest.port

# Create a second TCP socket for the data connection
dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('CONN: attempting conection to %s:%d' % (server_addr, data_port))
dataSock.connect((server_addr, data_port))

# Start the listener thread
print('Reday to receive raw data stream.')

while True:
	data = dataSock.recv(2)
	if data != '':
		print(data)

