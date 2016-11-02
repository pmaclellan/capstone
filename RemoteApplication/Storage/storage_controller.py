import threading

class StorageController():
    def __init__(self, incoming_buffer):
        print 'StorageController __init()'
        # Buffer will contain parsed ADC data readings
        self.incoming_buf = incoming_buffer
        self.reader_thread = threading.Thread(target=self.grabbuffer)
        self.reader_thread.start()
        self.writer_thread = threading.Thread(target=self.writefiles)
        # TODO: start thread

    def writefiles(self):
        while True:
            if not self.incoming_buf.empty():
                reading = self.incoming_buf.get_nowait()
                # TODO: write reading to HDF file

    def grabbuffer(self):
        while True:
            if not self.incoming_buf.empty():
                reading = self.incoming_buf.get()