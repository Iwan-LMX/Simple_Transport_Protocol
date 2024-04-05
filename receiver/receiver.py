#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os

NUM_ARGS = 4  # Number of command-line arguments
BUF_SIZE = 3  # Size of buffer for sending/receiving data
MSL = 1       # Maximum segment lifetimes, second
#--------------------------------------------------------------------------#
#---------------------------------Main body--------------------------------#
#--------------------------------------------------------------------------#
def main():
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} port wait_time")
    receiver_port   = parse_port(sys.argv[1])
    sender_port     = parse_port(sys.argv[2])
    txt_file_received = sys.argv[3]
    max_win         = parse_win(sys.argv[4])

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        #-------------------Listening state------------------------#
        receiver.bind(('', receiver_port))
        while True:
            buf, addr = receiver.recvfrom(BUF_SIZE)
            #Packet was received,
            rcv_type, rcv_seqno,  = parse_packet(buf)

            if rcv_type == 2 and addr[1] == sender_port:
                reply_ACK(receiver, rcv_seqno, 1, addr)
                break
        #-----------------Established state------------------------#
        filename = './receive_log/txt_file_received.txt'
        if os.path.exists(filename):
            root, ext = os.path.splitext(filename)
            index = 1
            while os.path.exists(filename):
                filename = f"{root}_({index}){ext}"
                index += 1
        
        with open(filename, 'a') as file:
            buffer = []
            while True:
                buf, addr = receiver.recvfrom(BUF_SIZE)
                #Packet was received,
                if addr[1] == sender_port:
                    rcv_type, rcv_seqno, rcv_data = parse_packet(buf)
                    if rcv_type == 0:
                        #need fix for unordered packet
                        file.write(rcv_data)
                        reply_ACK(receiver, rcv_seqno, len(buf[4:]), addr)
                    if rcv_type == 2: 
                        reply_ACK(receiver, rcv_seqno, 1, addr)  
                    if rcv_type == 3:
                        reply_ACK(receiver, rcv_seqno, 1, addr)
                        break
            file.close()                
        #-----------------------Time Wait--------------------------#
        receiver.settimeout(2*MSL) 
        while True:
            try:
                buf, addr = receiver.recvfrom(BUF_SIZE)
                rcv_type, rcv_seqno,  = parse_packet(buf)
                if rcv_type == 3 and addr == sender_port:
                    reply_ACK(receiver, rcv_seqno, 1, addr)
            except socket.timeout:
                break
        receiver.close()
    sys.exit(0)
#--------------------------------------------------------------------------#
#------------------------Self defined functions----------------------------#
#--------------------------------------------------------------------------#
def reply_ACK(socket, rcv_seqno, size, addr):
    pkt = (1).to_bytes(2, byteorder='big')
    seqno = (rcv_seqno + size) % 65535
    pkt += seqno.to_bytes(2, byteorder='big')
    while True:
        if (socket.sendto(pkt, addr) == len(pkt)): break

def parse_packet(buf):
    type = int.from_bytes(buf[:2], byteorder='big') #DATA = 0, ACK = 1, SYN = 2, FIN = 3.
    seqno = int.from_bytes(buf[2:4], byteorder='big')
    data = buf[4:].decode("utf-8")
    return type, seqno, data

def parse_port(port_str, min_port=49152, max_port=65535):
    try:
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid port argument, must be numerical: {port_str}")
    
    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
              
    return port

def parse_win(max_win, min_win=1000):
    try:
        win = int(max_win)
    except ValueError:
        sys.exit(f"Invalid max_win argument, must be numerical: {max_win}")
    
    if max_win < min_win:
        sys.exit(f"Invalid window argument, must larger or equal than {min_win}")

    return win

#--------------------------------------------------------------------------#
#------------------------Entrance of the code------------------------------#
#--------------------------------------------------------------------------#
if __name__ == "__main__": 
    main()