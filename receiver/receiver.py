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

    #-------------------Listening state------------------------#
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(('', receiver_port))
        while True:
            buf, addr = receiver.recvfrom(BUF_SIZE)
            #Packet was received,
            rcv_type = int.from_bytes(buf[:2], byteorder='big') #DATA = 0, ACK = 1, SYN = 2, FIN = 3.
            rcv_seqno = int.from_bytes(buf[2:4], byteorder='big')

            if rcv_type == 2 and addr[1] == sender_port:
                pkt = (1).to_bytes(2, byteorder='big')  #type = ACK 1
                snd_seqno = (rcv_seqno + 1) %  65535    #calculate the sequence number
                pkt += snd_seqno.to_bytes(2, byteorder='big')

                while True:
                    if (receiver.sendto(pkt, addr) == len(pkt)): break
                
                break   #Send back ACK exist Listening state
    #-----------------Established state------------------------#
        filename = './receive_log/txt_file_received.txt'
        if os.path.exists(filename):
            root, ext = os.path.splitext(filename)
            index = 1
            while os.path.exists(filename):
                filename = f"{root}_({index}){ext}"
                index += 1
        
        with open(filename, 'a') as file:
            while True:
                buf, addr = receiver.recvfrom(BUF_SIZE)
                #Packet was received,
                rcv_type = int.from_bytes(buf[:2], byteorder='big') #DATA = 0, ACK = 1, SYN = 2, FIN = 3.
                rcv_seqno = int.from_bytes(buf[2:4], byteorder='big')
                rcv_data = buf[4:].decode("utf-8")

                if rcv_type == 0 and addr[1] == sender_port:
                    #need fix for unordered packet
                    file.write(rcv_data)
                    snd_seqno = (rcv_seqno + len(buf[4:])) %  65535  
                if rcv_type == 2 and addr[1] == sender_port:
                    snd_seqno = (rcv_seqno + 1) %  65535    
                if rcv_type == 3 and addr[1] == sender_port:
                    snd_seqno = (rcv_seqno + 1) %  65535
                
                pkt = (1).to_bytes(2, byteorder='big')
                pkt += snd_seqno.to_bytes(2, byteorder='big')
                while True:
                    if (receiver.sendto(pkt, addr) == len(pkt)): break

                if rcv_type == 3 and addr[1] == sender_port: break

            file.close()                
    #-----------------------Time Wait--------------------------#
    
        receiver.settimeout(2*MSL) 

#--------------------------------------------------------------------------#
#------------------------Self defined functions----------------------------#
#--------------------------------------------------------------------------#
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