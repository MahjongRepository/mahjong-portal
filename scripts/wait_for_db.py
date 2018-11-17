#!/usr/bin/env python3
"""Script to check if DB is ready to accept connections."""
from os import environ
from time import sleep
import socket


def main():
    HOST = environ.get('DB_HOST', 'postgres')
    PORT = int(environ.get('DB_PORT'))
    with socket.socket() as s:
        for second in range(60):
            try:
                s.connect((HOST, PORT))
                break
            except socket.error:
                sleep(1)
        else:
            exit(1)


if __name__ == '__main__':
    main()
