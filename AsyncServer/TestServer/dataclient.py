import socket
import numpy
from control_signals_pb2 import *

serverName = '10.42.0.2'
serverPort = 10002
dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dataSocket.connect((serverName, serverPort))
print("connected")
rawsize = bytearray(8000);
while True:
   dataSocket.recv_into(rawsize)
dataSocket.close()
