from daqula_application import DaqulaApplication
from headless_daqula import HeadlessDaqula

import sys
import signal
import logging
import argparse

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    loglevel = ''
    default_loglevel = 'INFO'
    control_port = 0
    default_port = 10001
    default_rate = 200000
    default_output_dir = '.'
    default_log_file = 'daqula_app.log'

    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true', help='start the application in headless mode (no GUI)')
    parser.add_argument('-o', '--output-dir', default=default_output_dir, help='path where binary data files will be stored')
    parser.add_argument('-r', '--rate', default=default_rate, help='ADC sample rate (Hz) in range [1526, 200000]')
    parser.add_argument('-a', '--host-address', help='IP address of DAQ server')
    parser.add_argument('-p', '--port', default=default_port, help='Control port of DAQ server')
    parser.add_argument('-l', '--loglevel', default=default_loglevel,
                        help='application logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL')

    args = parser.parse_args()

    if args.headless and not args.host_address:
        parser.error('If running in headless mode, you must specify at least the DAQ server address (-a, --host-address)')

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(levelname)s: %(asctime)s: %(message)s',
                        filename=default_log_file, level=numeric_level)

    if args.headless:
        app = HeadlessDaqula(output_dir=args.output_dir, rate=int(args.rate),
                             host=args.host_address, port=int(args.port))
        app.start()
    else:
        app = DaqulaApplication(sys.argv)
        app.start()