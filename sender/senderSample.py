#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import random
import socket
import sys
import threading
import time
from dataclasses import dataclass

NUM_ARGS  = 3  # Number of command-line arguments
BUF_SIZE  = 3  # Size of buffer for receiving messages
MAX_SLEEP = 2  # Max seconds to sleep before sending the next message

@dataclass
class Control:
    """Control block: parameters for the sender program."""
    host: str               # Hostname or IP address of the receiver
    port: int               # Port number of the receiver
    socket: socket.socket   # Socket for sending/receiving messages
    run_time: int           # Run time in seconds
    is_alive: bool = True   # Flag to signal the sender program to terminate

def parse_run_time(run_time_str, min_run_time=1, max_run_time=60):
    """Parse the run_time argument from the command-line.

    The parse_run_time() function will attempt to parse the run_time argument
    from the command-line into an integer. If the run_time argument is not 
    numerical, or within the range of acceptable run times, the program will
    terminate with an error message.

    Args:
        run_time_str (str): The run_time argument from the command-line.
        min_run_time (int, optional): Minimum acceptable run time. Defaults to 1.
        max_run_time (int, optional): Maximum acceptable run time. Defaults to 60.

    Returns:
        int: The run_time as an integer.
    """
    try:
        run_time = int(run_time_str)
    except ValueError:
        sys.exit(f"Invalid run_time argument, must be numerical: {run_time_str}")
    
    if not (min_run_time <= run_time <= max_run_time):
        sys.exit(f"Invalid run_time argument, must be between {min_run_time} and {max_run_time} seconds: {run_time_str}")
                 
    return run_time

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

def setup_socket(host, port):
    """Setup a UDP socket for sending messages and receiving replies.

    The setup_socket() function will setup a UDP socket for sending data and
    receiving replies. The socket will be associated with the peer address 
    given by the host:port arguments. This will allow for send() calls without
    having to specify the peer address each time. It will also limit the 
    datagrams received to only those from the peer address.  The socket will
    be set to non-blocking mode.  If the socket fails to connect the program 
    will terminate with an error message.

    Args:
        host (str): The hostname or IP address of the receiver.
        port (int): The port number of the receiver.

    Returns:
        socket: The newly created socket.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # UDP sockets are "connection-less", but we can still connect() to
    # set the socket's peer address.  The peer address identifies where 
    # all datagrams are sent on subsequent send() calls, and limits the
    # remote sender for subsequent recv() calls.
    try:
        sock.connect((host, port))
    except Exception as e:
        sys.exit(f"Failed to connect to {host}:{port}: {e}")

    # Set socket timeout to 0, this is equivalent to setting it as non-blocking:
    # sock.setblocking(False)
    sock.settimeout(0)  

    return sock

def recv_thread(control):
    """The receiver thread function.

    The recv_thread() function is the entry point for the receiver thread. It
    will sit in a loop, checking for messages from the receiver. When a message 
    is received, the sender will unpack the message and print it to the log. On
    each iteration of the loop, it will check the `is_alive` flag. If the flag
    is false, the thread will terminate. The `is_alive` flag is shared with the
    main thread and the timer thread.

    Args:
        control (Control): The control block for the sender program.
    """
    while control.is_alive:
        try:
            nread = control.socket.recv(BUF_SIZE)
        except BlockingIOError:
            continue    # No data available to read
        except ConnectionRefusedError:
            print(f"recv: connection refused by {control.host}:{control.port}, shutting down...", file=sys.stderr)
            control.is_alive = False
            break

        if len(nread) < BUF_SIZE - 1:
            print(f"recv: received short message of {nread} bytes", file=sys.stderr)
            continue    # Short message, ignore it

        # Convert first 2 bytes (i.e. the number) from network byte order 
        # (big-endian) to host byte order, and extract the `odd` flag.
        num = int.from_bytes(nread[:2], "big")
        odd = nread[2]

        # Log the received message
        print(f"{control.host}:{control.port}: rcv: {num:>5} {'odd' if odd else 'even'}")

def timer_thread(control):
    """Stop execution when the timer expires.

    The timer_thread() function will be called when the timer expires. It will
    print a message to the log, and set the `is_alive` flag to False. This will
    signal the receiver thread, and the sender program, to terminate.

    Args:
        control (Control): The control block for the sender program.
    """
    print(f"{control.run_time} second timer expired, shutting down...")
    control.is_alive = False

if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} host port run_time")

    host     = sys.argv[1]
    port     = parse_port(sys.argv[2])
    run_time = parse_run_time(sys.argv[3])
    sock     = setup_socket(host, port)

    # Create a control block for the sender program.
    control = Control(host, port, sock, run_time)

    # Start the receiver and timer threads.
    receiver = threading.Thread(target=recv_thread, args=(control,))
    receiver.start()

    timer = threading.Timer(run_time, timer_thread, args=(control,))
    timer.start()

    random.seed()  # Seed the random number generator
    
    # Send a sequence of random numbers as separate datagrams, until the 
    # timer expires.
    while control.is_alive:
        num = random.randrange(2**16)       # Random number in range [0, 65535]
        net_num = num.to_bytes(2, "big")    # Convert number to network byte order

        # Log the send and then send the random number.
        print(f"{host}:{port}: snd: {num:>5}")
        nsent = control.socket.send(net_num)
        if nsent != len(net_num):
            control.is_alive = False
            sys.exit(f"send: partial/failed send of {nsent} bytes")

        # Sleep for a random amount of time before sending the next message.
        # This is ONLY done for the sake of the demonstration, it should be 
        # removed to maximise the efficiency of the sender.
        time.sleep(random.uniform(0, MAX_SLEEP + 1))
    
    # Suspend execution here and wait for the threads to finish.
    receiver.join()
    timer.cancel()

    control.socket.close()  # Close the socket

    print("Shut down complete.")

    sys.exit(0)