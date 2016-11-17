#!/usr/bin/python

import h5py
import numpy as np
import sys
from os import listdir

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

def convert_file(file, source_dir, output_dir):
	print 'starting conversion of %s' % file
	fbin = open(source_dir + file, 'rb')
	outfile = file.split('.')[0] + '.h5'
	fout = h5py.File(output_dir + outfile, 'a')

	# grab the header info
	start_time = int(fbin.readline())
	channel_bitmask = int(fbin.readline())
	chunk_size = int(fbin.readline())

	active_channels = get_channels_from_bitmask(channel_bitmask)
	bytes_per_reading = (len(active_channels) + 4) * 2
	dataset = [] # list of readings to write to HDF file as a block
	block_size = 1000
	block_counter = 0

	for line in fbin:
		line_bytes = bytearray(line)
		for i in range(chunk_size):
			if len(dataset) >= block_size:
				# write block of readings to output HDF5 file
				fout.create_dataset(str(block_counter), data=dataset)
				dataset = []
				block_counter += 1
			start_index = i * bytes_per_reading
			end_index = (i+1) * bytes_per_reading
			raw_reading = line_bytes[start_index:end_index]
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
	if len(dataset) > 0:
		# write the leftover readings to the file before closing
		fout.create_dataset(str(block_counter), data=dataset)

	fout.close()
	fbin.close()
	print 'conversion done, %s produced' % outfile

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'usage: file_converter <source_dir> [output_dir=source_dir]'
		sys.exit()
	source_dir = sys.argv[1]
	if not source_dir.endswith('/'):
		source_dir += '/'
	if len(sys.argv) > 2:
		output_dir = sys.argv[2]
		if not output_dir.endswith('/'):
			output_dir += '/'
	else:
		output_dir = source_dir

	files = [f for f in listdir(source_dir) if f.endswith('.daqula')]
	for file in files:
		success = convert_file(file, source_dir, output_dir)
