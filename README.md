# capstone

<i>daqula</i> is a high throughput synchronous data acquisition system (DAQ). 

It is designed to work with up to 32 analog input channels, which connect to a custom PCB containing four 8-channel Analog-to-Digital Converters (ADC), and hosting a Microzed Programmable SoC. The system is capable of sampling all ADCs simultaneously at a configurable rate and recording readings timestamped in nanoseconds.

<b>Features:</b>
-
- Configurable sampling rate (up to 200 kHz)
- 16-bit ADC precision
- GUI or headless operation
- Supports full-speed storage into binary and metadata files (json)
  - Offline conversion script included to parse binary files into HDF5 format

<b>Usage - Setting up Hardware and Software</b>
-
<b><i> Hardware Setup </i></b>

Follow these steps to ensure proper hardware setup.

1. Make sure MicroZed is fully connected to DAQuLA PCB and contains microSD card.
2. Connect ethernet between host computer and jack on MicroZed
  * For use at 200kHz, this connection should be made with at least 1GB ethernet. 
3. Connect 12v power supply to DAQuLA PCB and power on.
4. Observe blue LED on MicroZed and terminal output on host computer. 
  * If necessary, MicroZed uses 'root' for both user login and password. You may change these, but don't forget them!
  * If output to host computer is not as expected, press the MicroZed reset button near the blue LED to re-start the system. 
5. Start DAQuLA software on host computer (see next section).

- <i> For more information regarding MicroZed please refer to the following <a href=http://microzed.org/sites/default/files/documentations/MicroZed_HW_UG_v1_4.pdf> user guide.</a> </i>


<b><i> Software Setup </i></b>

<i>GUI  Mode</i>

- <b>ex:</b> `python daqula.py` will launch the <i>daqula</i> application. This application can be used to configure the DAQ device. Currently, the application accepts user inputted server IP addresses and sample rates. The port at this time will always default to 10001 for control messages and 10002 for data. The channel selection is also unsupported by the server at this time but will be added in a future version.
- The '-l' flag can be used to change the logging level. The default logging level is INFO. Full options are: (in order of decreasing verbosity)
    - DEBUG
    - INFO
    - WARNING
    - ERROR

<i>Headless Mode</i>

- <b>ex:</b> `python daqula.py --headless -a 10.42.0.2 --rate 100000 --output-dir ./output`
- When running in <i>headless</i> mode, you must specify the host address using the `-a` or `--host-address` flags.
- Upon starting in headless mode, the program will automatically connect to the DAQ device over a TCP connection.
- To disconnect and exit the program, you just need to press `Ctrl-C`
  - If you are running the program in the background or calling it form a script, you can kill the application by sending it a SIGINT signal using `kill -2 <pid>`. The application spawns multiple Python processes, the one you want to send the signal to will be printed to the console (or to a file via redirection) upon startup.
  
There is no included file reader at this time for the final HDF5 files that are written to the file system upon running the conversion script. To read a file, you must use the `h5py` module:

```
# python
>>> import h5py
>>> f = h5py.File('Storage/daqula0000.h5', 'r')
>>> x = f.get('0')
>>> x[0]
array([('TS0', 0), ('TS1', 2), ('TS2', 45387), ('TS3', 53056),
       ...
       ('3.4', 24440), ('3.5', 24394), ('3.6', 24352), ('3.7', 24400)], 
      dtype=[('channel', 'S3'), ('value', '<u2')])
>>> x = f.get('100')
>>> for i in x:
...     print i
... 
[('TS0', 0) ('TS1', 2) ('TS2', 48808) ('TS3', 39106) ('0.0', 23768)
 ('0.1', 23762) ('0.2', 2) ('0.3', 23710) ('0.4', 23754) ('0.5', 23706)
 ...
[('TS0', 0) ('TS1', 2) ('TS2', 48808) ('TS3', 47110) ('0.0', 23778)
  ...
 ('3.7', 24394)]

```

<b>Note:</b> The timestamps in the converted HDF5 files are stored as four `uint16`s, labelled `'TS0'` through `'TS3'` from MSB to LSB. The full 64-bit timestamp can be reconstructed as follows:
TODO
-
