#!/usr/bin/env python

import socket
import threading
import time
import Queue

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler


from matplotlib.figure import Figure

import sys
# import Tkinter GUI library
if sys.version_info[0] < 3:
  import Tkinter as Tk
else:
  import tkinter as Tk


class DaqConnection:
  def __init__(self):
    # Create a TCP/IP socket
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.queue = Queue.Queue()
    self._connect_to_server()

  def _connect_to_server(self):
    # Connect the socket to the port where the server is listening
    self.server_address = ('localhost', 10001)
    print('connecting to %s port %s' % self.server_address)
    self.sock.connect(self.server_address)
    self.receiver_thread = threading.Thread(target=self.listen_for_data)
    self.receiver_thread.daemon = True
    self.receiver_thread.start()

  # TCP Receiver thread
  def listen_for_data(self):
    while True:
      if self.sock:
        new_data = self.sock.recv(4096)
        points = new_data.split()
        for point in points:
          self.queue.put(point)
        # print(new_data)
        time.sleep(1)

  def yield_data_point(self):
    if not self.queue.empty():
      yield self.queue.get()
    else:
      print("No more data!")

root = Tk.Tk()
root.wm_title("DAQula Mock Data")

# Create matplotlib Figure
# this contains the graph of incoming data
fig = Figure(figsize=(5, 4), dpi=100)
axes = fig.add_subplot(111)
timesteps = arange(0.0, 3.0, 0.01)
s = 0.7*sin(2*pi*timesteps)

axes.plot(timesteps, s)


# a tk.DrawingArea
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)


def on_key_event(event):
  print('you pressed %s' % event.key)
  key_press_handler(event, canvas, toolbar)

canvas.mpl_connect('key_press_event', on_key_event)


def _quit():
  root.quit()     # stops mainloop
  root.destroy()  # this is necessary on Windows to prevent
                  # Fatal Python Error: PyEval_RestoreThread: NULL tstate

daq = DaqConnection()

# connectButton = Tk.Button(master=root, text='Connect', command=daq._connect_to_server)
# connectButton.pack(side=Tk.BOTTOM)

quitButton = Tk.Button(master=root, text='Quit', command=_quit)
quitButton.pack(side=Tk.BOTTOM)

Tk.mainloop()
# If you put root.destroy() here, it will cause an error if
# the window is closed with the window manager.