import socket
import numpy
import time
from control_signals_pb2 import *

serverName = '10.42.0.2'
serverPort = 10001
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
print("connected")
wrapper = RequestWrapper()
wrapper.sequence = 1
wrapper.start.port = 1
wrapper.start.channels = 4183856184 #4294967295
wrapper.start.rate = 100
#while(True):
# Send size of message
sendsize = numpy.uint16(len(wrapper.SerializeToString()))
#print("sending size={0}".format(sendsize))
clientSocket.send(sendsize)
# Send message
print("sending wrapper with port={0} and channels={1}".format(wrapper.start.port, wrapper.start.channels))
clientSocket.send(wrapper.SerializeToString())

rawsize = bytearray(2)
# Receive size of message
clientSocket.recv_into(rawsize)
size = '{:08b}'.format(rawsize[0])
#print("received size={0}".format(size))
# Receive message
hello, addr = clientSocket.recvfrom(int(size))
wrapper.ParseFromString(hello)
print("received wrapper with port={0} and channels={1}".format(wrapper.start.port, wrapper.start.channels))
time.sleep(10000)

stop = RequestWrapper()
stop.sequence = 2
stop.stop.port = 1
stop.stop.channels = 15
sendsize = numpy.uint16(len(stop.SerializeToString()))
clientSocket.send(sendsize)
print("sending stop request")
clientSocket.send(stop.SerializeToString())
