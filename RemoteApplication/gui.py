#!/usr/bin/env python

import socket
import threading
import Queue

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import matplotlib.animation as animation

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

ramp_max = 511

class DaqConnection:
  def __init__(self):
    # Create a TCP/IP socket
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.queue = Queue.Queue()
    self._connect_to_server()

  def _connect_to_server(self):
    # Connect the socket to the port where the server is listening
    self.server_address = ('localhost', 10001)
    # print('connecting to %s port %s' % self.server_address)
    self.sock.connect(self.server_address)
    self.receiver_thread = threading.Thread(target=self.listen_for_data)
    self.receiver_thread.daemon = True
    self.receiver_thread.start()

  # TCP Receiver thread
  def listen_for_data(self):
    while True:
      if self.sock:
        incoming_buffer = bytearray(b" " * 512) # create "empty" buffer to store incoming data
        self.sock.recv_into(incoming_buffer)
        i = 0
        while i < len(incoming_buffer) and incoming_buffer[i] != b' ':
            # convert each byte to binary strings and combine into one 16-bit string
            binary = '{:08b}'.format(incoming_buffer[i + 1]) + '{:08b}'.format(incoming_buffer[i])
            # convert 16-bit string to int
            received = int(binary, base=2)
            # add new value to queue to be processed by graph
            self.queue.put(received)
            # increment by 2 bytes each time to account for uint16_t type
            i += 2

  def yield_data_point(self):
    if not self.queue.empty():
      yield self.queue.get()
    else:
      print("No more data!")

root = Tk.Tk()
root.wm_title("DAQula Mock Data")
daq = DaqConnection()

def update_line(num, data, line):
  if not daq.queue.empty():
    # update 4 values at a time to increase speed
    for i in range(4):
      new_value = daq.queue.get()
      data.append(new_value)
    if len(data) > ramp_max:
      plt.xlim(len(data) - ramp_max, len(data))
      plt.axis([len(data) - ramp_max, len(data), 0, ramp_max + 1])
      line.set_data(xrange(len(data) - ramp_max, len(data)),
                    data[len(data) - ramp_max:])
    else:
      line.set_data(xrange(len(data)), data)
  return line,

fig1 = plt.figure()

data = []
l, = plt.plot([], [], 'r-')
plt.xlim(0, ramp_max)
plt.ylim(0, ramp_max)
plt.xlabel('Sample #')
plt.ylabel('Value')
plt.title('DAQula')
line_ani = animation.FuncAnimation(fig1, update_line, 500, fargs=(data, l),
                                   interval=50, blit=False)
plt.show()

# a tk.DrawingArea
canvas = FigureCanvasTkAgg(fig1, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

def on_key_event(event):
  # print('you pressed %s' % event.key)
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