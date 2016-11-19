#!/usr/bin/python

import h5py
import numpy as np
import sys
from os import listdir
import os.path
import multiprocessing
import json

meta_filename = 'stream.json'

# generate list of strings from bitmask
def get_channels_from_bitmask(bitmask):
  active_channels = []
  num_ADCs = 4
  num_channels_per_ADC = 8
  for adc in range(num_ADCs):
    for channel in range(num_channels_per_ADC):
      active = np.bitwise_and(np.left_shift(0x01, adc * num_channels_per_ADC + channel), bitmask)
      if active > 0:
        active_channels.append(str(adc) + '.' + str(channel))
  return active_channels

def convert_file(file, source_dir, output_dir, active_channels, start_time):
	print '%s starting conversion of %s' % \
		(multiprocessing.current_process().name, file)

	outfile = file.split('.')[0] + '.h5'
	bytes_per_reading = (len(active_channels) + 4) * 2
	dataset = [] # list of readings to write to HDF file as a block
	block_size = 1000
	block_counter = 0

	with open(os.path.join(source_dir, file), 'rb') as fbin:
		with h5py.File(os.path.join(output_dir, outfile), 'a') as fout:
			while True:
				if len(dataset) >= block_size:
					# write block of readings to output HDF5 file
					fout.create_dataset(str(block_counter), data=dataset)
					dataset = []
					block_counter += 1
				raw_reading = bytearray(fbin.read(bytes_per_reading))
				if len(raw_reading) < bytes_per_reading:
					# EOF reached
					if len(dataset) > 0:
						# write the leftover readings to the file before closing
						fout.create_dataset(str(block_counter), data=dataset)
					break
				# extract the 48-bit timestamp value
				timestamp = (raw_reading[7] << 40) + (raw_reading[6] << 32) + \
										(raw_reading[5] << 24) + (raw_reading[4] << 16) + \
										(raw_reading[3] << 8) + raw_reading[2]

				abs_ts = timestamp + start_time

				# split the 64-bit timestamp into 16-bit chunks for more 
				# efficient storage (ts0 is MSB, ts3 is LSB)
				ts0 = (abs_ts & (0xff << 48)) >> 48
				ts1 = (abs_ts & (0xff << 32)) >> 32
				ts2 = (abs_ts & (0xff << 16)) >> 16
				ts3 = abs_ts & 0xff

				# start building the list that will be converted to a numpy array later
				intermediate = [('TS0', ts0), ('TS1', ts1), ('TS2', ts2), ('TS3', ts3)]

				# trim DEAD and timestamp from the reading
				raw_reading = raw_reading[8:]

				# construct tuple for each reading e.g. ('0.0', 43125) and add to list
				for i in range(0, len(raw_reading), 2):
					intermediate.append((active_channels[i/2], 
															(raw_reading[i + 1] << 8) + raw_reading[i]))

				# create numpy array from list for passing to storage
				reading = np.array(intermediate, 
													dtype=[('channel', 'S3'), ('value', 'uint16')])
				dataset.append(reading)

	print '%s finished conversion, %s produced' % \
		(multiprocessing.current_process().name, outfile)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'usage: file_converter.py <source_dir> [output_dir=source_dir]'
		sys.exit(2)
	source_dir = sys.argv[1]
	if len(sys.argv) > 2:
		output_dir = sys.argv[2]
	else:
		output_dir = source_dir

	if meta_filename in listdir(source_dir):
		with open(os.path.join(source_dir, meta_filename), 'r') as mf:
			metadata = json.load(mf)
	else:
		print 'ERROR: JSON metadata file not found, aborting...'
		sys.exit(1)

	try:
		files = metadata['file_list']
	except KeyError, e:
		print 'ERROR: JSON metadata file does not contain list of binary files'

	try:
		channel_mask = metadata['channel_bitmask']
		start_time = metadata['start_time']
	except KeyError, e:
		print 'ERROR: JSON metadata does not contain necessary fields'

	active_channels = get_channels_from_bitmask(channel_mask)

	pool = multiprocessing.Pool()

	for file in files:
		pool.apply_async(convert_file, 
			(file, source_dir, output_dir, active_channels, start_time))
	pool.close()
	pool.join()
	print 'SUCCESS: all files converted!'
