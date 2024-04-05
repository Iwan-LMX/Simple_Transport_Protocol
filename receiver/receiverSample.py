#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys

NUM_ARGS = 2  # Number of command-line arguments
BUF_SIZE = 3  # Size of buffer for sending/receiving data

def parse_wait_time(wait_time_str, min_wait_time=1, max_wait_time=60):
    """Parse the wait_time argument from the command-line.

    The parse_wait_time() function will attempt to parse the wait_time argument
    from the command-line into an integer. If the wait_time argument is not 
    numerical, or within the range of acceptable wait times, the program will
    terminate with an error message.

    Args:
        wait_time_str (str): The wait_time argument from the command-line.
        min_wait_time (int, optional): Minimum acceptable wait time. Defaults to 1.
        max_wait_time (int, optional): Maximum acceptable wait time. Defaults to 60.

    Returns:
        int: The wait_time as an integer.
    """
    try:
        wait_time = int(wait_time_str)
    except ValueError:
        sys.exit(f"Invalid wait_time argument, must be numerical: {wait_time_str}")
    
    if not (min_wait_time <= wait_time <= max_wait_time):
        sys.exit(f"Invalid wait_time argument, must be between {min_wait_time} and {max_wait_time} seconds: {wait_time_str}")
                 
    return wait_time

def parse_port(port_str, min_port=49152, max_port=65535):
    """Parse the port argument from the command-line.

    The parse_port() function will attempt to parse the port argument
    from the command-line into an integer. If the port argument is not 
    numerical, or within the acceptable port number range, the program will
    terminate with an error message.

    Args:
        port_str (str): The port argument from the command-line.
        min_port (int, optional): Minimum acceptable port. Defaults to 49152.
        max_port (int, optional): Maximum acceptable port. Defaults to 65535.

    Returns:
        int: The port as an integer.
    """
    try:
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid port argument, must be numerical: {port_str}")
    
    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
                 
    return port

if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} port wait_time")

    port      = parse_port(sys.argv[1])
    wait_time = parse_wait_time(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', port))              # bind to `port` on all interfaces
        s.settimeout(wait_time)         # set timeout for receiving data

        while True:
            # Here we're using recvfrom() and sendto(), but we could also 
            # connect() this UDP socket to set communication with a particular 
            # peer. This would allow us to use send() and recv() instead, 
            # but only communicate with one peer at a time.
            
            try:
                buf, addr = s.recvfrom(BUF_SIZE)
            except socket.timeout:
                print(f"No data within {wait_time} seconds, shutting down.")
                break

            if len(buf) < BUF_SIZE-1:
                print(f"recvfrom: received short message: {buf}", file=sys.stderr)
                continue

            # Packet was received, first (and only) field is multi-byte, 
            # so need to convert from network byte order (big-endian) to 
            # host byte order.  Then log the recv.
            num = int.from_bytes(buf[:2], byteorder='big')
            print(f"{addr[0]}:{addr[1]}: rcv: {num:>5}")

            # Determine whether the number is odd or even, and append the 
            # result (as a single byte) to the buffer.
            odd = num % 2
            buf += odd.to_bytes(1, byteorder='big')

            # Log the send and send the reply.
            print(f"{addr[0]}:{addr[1]}: snd: {num:>5} {'odd' if odd else 'even'}")
            if (s.sendto(buf, addr) != len(buf)):
                print(f"sendto: partial/failed send, message: {buf}", file=sys.stderr)
                continue

    sys.exit(0)