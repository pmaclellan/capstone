import socket
import sys
import time

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10001)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
  # Wait for a connection
  print('waiting for a connection')
  connection, client_address = sock.accept()
  try:
	  print('connection from', client_address)

	  # Generate and transmit mock data
	  data = 0
	  while True:
	    connection.sendall(str(data) + '\n')
	    data = (data + 1) % 256
	    # time.sleep(0.01)
	            
  finally:
	  # Clean up the connection
	  connection.close()