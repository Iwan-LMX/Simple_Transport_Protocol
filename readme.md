 
 # Overview receiver file

 
 The scenario is simple: a sender, or multiple senders, send a sequence of 
 random numbers to a receiver. The receiver performs some basic modulo 
 arithmetic to determine whether each random number it receives is odd or
 even, and sends this information back to the sender.
 
 Message format from sender to receiver (2 bytes total):
 
    +-------------+
    | Byte Offset |
    +------+------+
    |   0  |   1  |
    +------+------+
    |    number   |
    +-------------+
 
 Message format from receiver to sender (3 bytes total):
 
    +--------------------+
    |    Byte Offset     |
    +------+------+------+
    |   0  |   1  |   2  |
    +------+------+------+
    |    number   |  odd |
    +-------------+------+
 
 
 Description
 -----------
 
 - The sender is invoked with three command-line arguments:  
     1. the hostname or IP address of the receiver  
     2. the port number of the receiver
     3. the duration to run, in seconds, before terminating
 
 - The receiver is invoked with two command-line arguments:
     1. the port number on which to listen for incoming messages
     2. the duration to wait for a message, in seconds, before terminating
 
 The sender will spawn two child threads: one to listen for responses from
 the receiver, and another to wait for a timer to expire. Meanwhile, the 
 main thread will sit in a loop and send a sequence of random 16-bit 
 unsigned integers to the receiver. Messages will be sent and received 
 through an ephemeral (OS allocated) port. After each message is sent, the 
 sender may sleep for a random amount of time.  Once the timer expires, 
 the child threads, and then the sender process, will gracefully terminate.
 
 The receiver is single threaded and sits in a loop, waiting for messages. 
 Each message is expected to contain a 16-bit unsigned integer. The receiver 
 will determine whether the number is odd or even, and send a message back 
 with the original number as well as a flag indicating whether the number 
 is odd or even. If no message is received within a certain amount of time, 
 the receiver will terminate.
 
 
 Features
 --------
 
 - Parsing command-line arguments
 - Random number generation (sender only)
 - Modulo arithmetic (receiver only)
 - Communication via UDP sockets
 - Non-blocking sockets (sender only)
 - Blocking sockets with a timeout (receiver only)
 - Using a "connected" UDP socket, to send() and recv() (sender only)
 - Using an "unconnected" UDP socket, to sendto() and recvfrom() (receiver 
   only)
 - Conversion between host byte order and network byte order for 
   multi-byte fields.
 - Timers (sender only)
 - Multi-threading (sender only)
 - Simple logging
 
 
 Usage
 -----
 
 1. Run the receiver program:
 
     $ python3 receiver.py 54321 10
 
    This will invoke the receiver to listen on port 54321 and terminate
    if no message is receieved within 10 seconds.
 
 2. Run the sender program:
 
     $ python3 sender.py 127.0.0.1 54321 30
 
    This will invoke the sender to send a sequence of random numbers to
    the receiver at 127.0.0.1:54321, and terminate after 30 seconds.
 
    Multiple instances of the sender can be run against the same receiver.
 
 
 Notes
 -----
 
 - The sender and receiver are designed to be run on the same machine, 
   or on different machines on the same network. They are not designed 
   to be run on different networks, or on the public internet.
 
 
 Author
 ------
 
 Written by Tim Arney (t.arney@unsw.edu.au) for COMP3331/9331.
 
 
 CAUTION
 -------
 
 - This code is not intended to be simply copy and pasted.  Ensure you 
   understand this code before using it in your own projects, and adapt
   it to your own requirements.
 - The sender adds artificial delay to its sending thread.  This is purely 
   for demonstration purposes.  In general, you should NOT add artificial
   delay as this will reduce efficiency and potentially mask other issues.


# Overview sender file

 
 The scenario is simple: a sender, or multiple senders, send a sequence of 
 random numbers to a receiver. The receiver performs some basic modulo 
 arithmetic to determine whether each random number it receives is odd or
 even, and sends this information back to the sender.
 
 Message format from sender to receiver (2 bytes total):
 
    +-------------+
    | Byte Offset |
    +------+------+
    |   0  |   1  |
    +------+------+
    |    number   |
    +-------------+
 
 Message format from receiver to sender (3 bytes total):
 
    +--------------------+
    |    Byte Offset     |
    +------+------+------+
    |   0  |   1  |   2  |
    +------+------+------+
    |    number   |  odd |
    +-------------+------+
 
 
 Description
 -----------
 
 - The sender is invoked with three command-line arguments:  
     1. the hostname or IP address of the receiver  
     2. the port number of the receiver
     3. the duration to run, in seconds, before terminating
 
 - The receiver is invoked with two command-line arguments:
     1. the port number on which to listen for incoming messages
     2. the duration to wait for a message, in seconds, before terminating
 
 The sender will spawn two child threads: one to listen for responses from
 the receiver, and another to wait for a timer to expire. Meanwhile, the 
 main thread will sit in a loop and send a sequence of random 16-bit 
 unsigned integers to the receiver. Messages will be sent and received 
 through an ephemeral (OS allocated) port. After each message is sent, the 
 sender may sleep for a random amount of time.  Once the timer expires, 
 the child threads, and then the sender process, will gracefully terminate.
 
 The receiver is single threaded and sits in a loop, waiting for messages. 
 Each message is expected to contain a 16-bit unsigned integer. The receiver 
 will determine whether the number is odd or even, and send a message back 
 with the original number as well as a flag indicating whether the number 
 is odd or even. If no message is received within a certain amount of time, 
 the receiver will terminate.
 
 
 Features
 --------
 
 - Parsing command-line arguments
 - Random number generation (sender only)
 - Modulo arithmetic (receiver only)
 - Communication via UDP sockets
 - Non-blocking sockets (sender only)
 - Blocking sockets with a timeout (receiver only)
 - Using a "connected" UDP socket, to send() and recv() (sender only)
 - Using an "unconnected" UDP socket, to sendto() and recvfrom() (receiver 
   only)
 - Conversion between host byte order and network byte order for 
   multi-byte fields.
 - Timers (sender only)
 - Multi-threading (sender only)
 - Simple logging
 
 
 Usage
 -----
 
 1. Run the receiver program:
 
     $ python3 receiver.py 54321 10
 
    This will invoke the receiver to listen on port 54321 and terminate
    if no message is receieved within 10 seconds.
 
 2. Run the sender program:
 
     $ python3 sender.py 127.0.0.1 54321 30
 
    This will invoke the sender to send a sequence of random numbers to
    the receiver at 127.0.0.1:54321, and terminate after 30 seconds.
 
    Multiple instances of the sender can be run against the same receiver.
 
 
 Notes
 -----
 
 - The sender and receiver are designed to be run on the same machine, 
   or on different machines on the same network. They are not designed 
   to be run on different networks, or on the public internet.
 
 
 Author
 ------
 
 Written by Tim Arney (t.arney@unsw.edu.au) for COMP3331/9331.
 
 
 CAUTION
 -------
 
 - This code is not intended to be simply copy and pasted.  Ensure you 
   understand this code before using it in your own projects, and adapt
   it to your own requirements.
 - The sender adds artificial delay to its sending thread.  This is purely 
   for demonstration purposes.  In general, you should NOT add artificial
   delay as this will reduce efficiency and potentially mask other issues.