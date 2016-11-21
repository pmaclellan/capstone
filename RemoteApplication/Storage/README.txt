############################  Output File Format  #############################

StorageController writes raw binary ADC readings to 'daqulaXXXX.bin' files, and
 metadata files to 'stream.json'.

The binary files contain all of the raw data coming from the DAQ system, which
includes a 0xDEAD header followed by a 48-bit timestamp and then the ADC 
readings in order of channels 0.0-0.7, 1.0-1.7, ... 3.7

###########################  File Converter Script  ###########################

NOTE: The conversion process is very slow and CPU intensive. Be patient!
In an effort to reduce conversion time, files will be processed by a pool of
worker processes based on the number of CPU cores the machine has.

There is a python script in the Storage directory named 'file_converter.py'.
It converts the binary '.bin' files into HDF5 files.

Usage:
file_converter.py <source_dir> [output_dir=source_dir]

The <source_dir> argument should be the directory where your output files are
saved. The script will look in this directory for the 'stream.json' file, 
which will be rea to gater the list of '.bin' files to convert. It should accept
both relative and absolute paths.

The <output_dir> argument is optional, and defaults to <source_dir> if not
specified. If specified, it allows you to write the output HDF5 files to a
separate directory. 

The generated HDF5 files ('.h5') will keep the same file names as
the '.bin' files they were converted from.