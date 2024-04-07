#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import time
NUM_ARGS = 4  # Number of command-line arguments
MSL = 1       # Maximum segment lifetimes, second
t = {0: 'DATA', 1:'ACK', 2:'SYN', 3:'FIN'}
#--------------------------------------------------------------------------#
#---------------------------------Main body--------------------------------#
#--------------------------------------------------------------------------#
def main():
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} port wait_time")
    receiver_port, sender_port, txt_file_received, max_win = parse_argv(sys.argv)
    next_seq = 0
    global startTime, window, remainWin

    log = open('./receiver/receiver_log.txt', 'w+')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        #-------------------Listening state------------------------#
        receiver.bind(('', receiver_port))
        while True:
            buf, addr = receiver.recvfrom(max_win)
            #Packet was received,
            rcv_type, rcv_seqno, rcv_data= parse_packet(buf)

            if rcv_type == 2 and addr[1] == sender_port:
                startTime = time.time()
                next_seq = reply_ACK(receiver, rcv_seqno, 0, addr, log, time.time(), 'SYN')
                break
        #-----------------Established state------------------------#
        remainWin = max_win

        filename = f'./receiver/{txt_file_received}';   file = open(filename, 'w+')
        while True:
            buf, addr = receiver.recvfrom(max_win)
            #Packet was received,
            if addr[1] == sender_port:
                rcv_type, rcv_seqno, rcv_data = parse_packet(buf)

                if rcv_type == 0 and remainWin >= len(rcv_data):
                    window[rcv_seqno] = rcv_data;   remainWin -= len(rcv_data)
                    if next_seq in window:
                        while next_seq in window:
                            data = window.pop(next_seq);    remainWin+=len(data)
                            file.write(data.decode("utf-8"))
                            next_seq = reply_ACK(receiver, next_seq, len(data), addr, log, time.time(), 'DATA')
                    else: #unordered pkt
                        reply_ACK(receiver, next_seq, 0, addr, log)
                elif rcv_type == 0 and remainWin < len(rcv_data):
                    print(f"drop a packet: seqno = {rcv_seqno}")
                    continue
                
                if rcv_type == 2:
                    reply_ACK(receiver, rcv_seqno, 0, addr, log, time.time(), 'SYN')  
                if rcv_type == 3:
                    reply_ACK(receiver, rcv_seqno, 0, addr, log, time.time(), 'FIN')
                    break
        file.close()                
        #-----------------------Time Wait--------------------------#
        receiver.settimeout(2*MSL) 
        while True:
            try:
                buf, addr = receiver.recvfrom(max_win)
                rcv_type, rcv_seqno,  rcv_data = parse_packet(buf)
                if rcv_type == 3 and addr == sender_port:
                    reply_ACK(receiver, rcv_seqno, 1, addr, log, time.time(), 'FIN')
            except socket.timeout:
                break
        receiver.close()
    log.close()
    sys.exit(0)
#--------------------------------------------------------------------------#
#------------------------Self defined functions----------------------------#
#--------------------------------------------------------------------------#
def reply_ACK(socket, rcv_seqno, size, addr, log, time, type):
    global startTime
    log.write(f"rcv\t %7.2f\t\t {type}\t {rcv_seqno}\t {size}\n" %((time - startTime)*1000))

    pkt = (1).to_bytes(2, byteorder='big');     
    if size == 0: size = 1
    seqno = (rcv_seqno + size) % 65535
    pkt += seqno.to_bytes(2, byteorder='big')
    while True:
        if (socket.sendto(pkt, addr) == len(pkt)): break

    log.write(f"snd\t %7.2f\t\t ACK\t {seqno}\t 0\n" %((time - startTime)*1000))
    return seqno

def parse_packet(buf):
    type = int.from_bytes(buf[:2], byteorder='big') #DATA = 0, ACK = 1, SYN = 2, FIN = 3.
    seqno = int.from_bytes(buf[2:4], byteorder='big')
    data = buf[4:]
    return type, seqno, data

def parse_argv(argv):
    min_port = 49152;   max_port = 65535
    min_win = 1000
    try:
        receiver_port = int(argv[1])
        sender_port = int(argv[2])
        txt_file_received = argv[3]
        max_win = int(argv[4])
    except ValueError:
        sys.exit(f"Invalid argument!")
    
    if not (min_port <= sender_port <= max_port or min_port <= receiver_port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}")
    if max_win < min_win:
        sys.exit(f"Invalid window argument, must larger or equal than {min_win}")

    return receiver_port, sender_port, txt_file_received, max_win

#--------------------------------------------------------------------------#
#------------------------Entrance of the code------------------------------#
#--------------------------------------------------------------------------#
if __name__ == "__main__": 
    window = {}
    remainWin = 0
    startTime = 0
    main()