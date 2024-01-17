#!/usr/bin/env python3

"""
Tiny Syslog Server in Python.

This is a tiny syslog server that is able to receive UDP based syslog
entries on a specified port and save them to a file.
That's it... it does nothing else...
There are a few configuration parameters.
Usage: sudo ./syslog_server.py
"""

import logging
import socketserver

# User Configuration variables:
LOG_FILE = 'syslog.log'
HOST = "0.0.0.0"
PORT = 514

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='',
    filename=LOG_FILE,
    filemode='a'
)

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    """ A handler """

    def handle(self):
        """ Handle data """
        data = bytes.decode(self.request[0].strip())
        #socket = self.request[1]
        print(f"{self.client_address[0]}: {str(data)}")
        logging.info(str(data))

if __name__ == "__main__":
    try:
        server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
        print("Starting server...")
        server.serve_forever(poll_interval=0.5)
    except PermissionError:
        print("Permission denied while trying to start the server. Try sudo.")
    except (IOError, SystemExit): # pylint: disable=try-except-raise
        raise
    except KeyboardInterrupt:
        print("\nShutting down...")
