############################  Binary File Format  #############################

StorageController writes raw binary ADC readings to '.daqula' files.
The format of these files is as follows:

<start_time>\n
<channel_bitmask>\n
<chunk_size>\n
data...\n
data...\n
data...\n
...

The first line contains the start time, which is the Unix timestamp (in ns)
associated with the reading whose offset timestamp is 0.

The second line contains the active channels bitmask, which is a uint32 where
each bit represents whether a given ADC channel is active.
A 1 means the channel is active and reporting data and a 0 means the channel
is disabled. This information is necessary for correlating each channel
reading (16-bit ADC value) with its proper channel ID ('0.0', etc.).

The third line contains the chunk size. This is how many samples are on
each following line of data in the file, where one sample is taken to be 
a synchronous time-slice of all active channels, plus the header bytes which
are made up of a 16-bit 0xDEAD sync header and a 48-bit offset timestamp. This
offset timestamp is what gets added to the <start_time> value to determine the
absolute timestamp of any given reading.

###########################  File Converter Script  ###########################

NOTE: The conversion process is very slow and CPU intensive. Be patient!
In an effort to reduce conversion time, files will be processed by a pool of
worker processes based on the number of CPU cores the machine has.

There is a python script in the Storage directory named 'file_converter.py'.
It converts the binary '.daqula' files into HDF5 files.

Usage:
file_converter.py <source_dir> [output_dir=source_dir]

The <source_dir> argument should be the directory where your .daqula files are
located. The script will look in this directory and convert all files with the
'.daqula' extension. It should accept both relative and absolute paths.

The <output_dir> argument is optional, and defaults to <source_dir> if not
specified. If specified, it allows you to write the output HDF5 files to a
separate directory. 

The generated HDF5 files ('.h5') will keep the same timestamped file names as
the '.daqula' files they were converted from.