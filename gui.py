#!/usr/bin/env python

import socket
import threading
import time
import Queue

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import matplotlib.animation as animation

import numpy as np
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
daq = DaqConnection()
# Create matplotlib Figure
# this contains the graph of incoming data
# fig = Figure(figsize=(5, 4), dpi=100)
# axes = fig.add_subplot(111)
# timesteps = arange(0.0, 3.0, 0.01)
# s = 0.7*sin(2*pi*timesteps)

# axes.plot(timesteps, s)

def update_line(num, data, line):
  if not daq.queue.empty():
    new_value = daq.queue.get()
    data.append(new_value)
    if len(data) > 255:
      plt.xlim(len(data) - 255, len(data))
      line.set_data(xrange(len(data) - 255, len(data)), 
                    data[len(data) - 255:])
    else:
      line.set_data(xrange(len(data)), data)
  return line,

fig1 = plt.figure()

data = []
l, = plt.plot([], [], 'r-')
plt.xlim(0, 256)
plt.ylim(0, 256)
plt.xlabel('x')
plt.title('DAQula')
line_ani = animation.FuncAnimation(fig1, update_line, 500, fargs=(data, l),
                                   interval=50, blit=True)
plt.show()

# a tk.DrawingArea
canvas = FigureCanvasTkAgg(fig1, master=root)
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

# connectButton = Tk.Button(master=root, text='Connect', command=daq._connect_to_server)
# connectButton.pack(side=Tk.BOTTOM)

quitButton = Tk.Button(master=root, text='Quit', command=_quit)
quitButton.pack(side=Tk.BOTTOM)

Tk.mainloop()
# If you put root.destroy() here, it will cause an error if
# the window is closed with the window manager.