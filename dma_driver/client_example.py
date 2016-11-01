import socket
import numpy
from control_signals_pb2 import StartRequest

serverName = '10.0.0.208'
serverPort = 10001
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
print("connected")
foo = StartRequest()
foo.port = 1
foo.channels = 32
# Send size of message
sendsize = numpy.uint16(len(foo.SerializeToString()))
print("sending size={0}".format(sendsize))
clientSocket.send(sendsize)
# Send message
print("sending foo with port={0} and channels={1}".format(foo.port, foo.channels))
clientSocket.send(foo.SerializeToString())

rawsize = bytearray(2)
# Receive size of message
clientSocket.recv_into(rawsize)
size = '{:08b}'.format(rawsize[0])
print("received size={0}".format(size))
# Receive message
hello, addr = clientSocket.recvfrom(int(size))
foo.ParseFromString(hello)
print("received foo with port={0} and channels={1}".format(foo.port, foo.channels))

clientSocket.close();

dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dataSocket.connect((serverName, foo.port))
print("connected")

dataSocket.close()
