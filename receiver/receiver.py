#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import time
import threading
from dataclasses import dataclass

@dataclass
class Control:
    """Control block: parameters for the sender program."""
    receiver_port: int
    sender_port: int
    txt_file_received: str
    max_win: int         
    is_alive: bool = True
    ori_data_recv: int = 0; ori_seg_recv: int = 0
    dup_seg_recv: int = 0; dup_seg_snd: int = 0
#--------------------------------------------------------------------------#
#---------------------------------Main body--------------------------------#
#--------------------------------------------------------------------------#
def main():
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} port wait_time")
    global startTime, window, remainWin, control
    control = parse_argv(sys.argv)
    next_seq = 0

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        #-------------------Listening state------------------------#
        receiver.bind(('', control.receiver_port)); receiver.settimeout(None)
        while control.is_alive:
            buf, addr = receiver.recvfrom(1024)

            rcv_type, rcv_seqno, rcv_data= parse_packet(buf)

            if rcv_type == 2 and addr[1] == control.sender_port:
                startTime = time.time()
                record_log('rcv', 'SYN', rcv_seqno, 0)
                next_seq = reply_ACK(receiver, rcv_seqno, 1, addr)
                break
            else:
                print("Detect unexpected behaviour, here to terminate!")
                sys.exit(0)
        #-----------------Established state------------------------#
        remainWin = control.max_win

            if addr[1] == control.sender_port:
                rcv_type, rcv_seqno, rcv_data = parse_packet(buf)
                if rcv_type == 0 and remainWin >= len(rcv_data):
                    if  (rcv_seqno - next_seq + 65536)%65536 <= control.max_win:
                        record_log('rcv', 'DATA', rcv_seqno, len(rcv_data))
                        window[rcv_seqno] = rcv_data;   remainWin -= len(rcv_data)

                        while next_seq in window:
                            data = window.pop(next_seq);    remainWin+=len(data)
                            control.ori_data_recv += len(data); control.ori_seg_recv += 1
                            file.write(data.decode("utf-8"))
                            next_seq =  (next_seq + len(data))%65536
                            
                    record_log('rcv', 'FIN', rcv_seqno, 0)
                    reply_ACK(receiver, rcv_seqno, 1, addr)
                    break               
        #-----------------------Time Wait--------------------------#
        timer = threading.Timer(2*MSL, timer_thread)
        timer.start();  receiver.settimeout(MSL)
        while control.is_alive:
            try:
                buf, addr = receiver.recvfrom(1024)
                rcv_type, rcv_seqno, rcv_data = parse_packet(buf)
                if rcv_type == 3 and addr[1] == control.sender_port:
                    record_log('rcv', 'FIN', rcv_seqno, 0)
                    reply_ACK(receiver, rcv_seqno, 1, addr)
                else:
                    print("Detect unexpected behaviour, here to terminate!")
                    sys.exit(0)
            except socket.timeout:
                continue


    log.write(f"\nOriginal data received:\t\t{control.ori_data_recv}\n")
    log.write(f"Original segments received:\t{control.ori_seg_recv}\n")
    log.write(f"Dup data segments received:\t{control.dup_seg_recv}\n")
    log.write(f"Dup ack segments sent:\t\t{control.dup_seg_snd}\n")
    file.close();   log.close()
    sys.exit(0)
#--------------------------------------------------------------------------#
#------------------------Self defined functions----------------------------#
#--------------------------------------------------------------------------#
def timer_thread():
    pkt = (1).to_bytes(2, byteorder='big');     
    seqno = (rcv_seqno + size) % 65536
    pkt += seqno.to_bytes(2, byteorder='big')
    while True:
        if (socket.sendto(pkt, addr) == len(pkt)): break
    record_log('snd', 'ACK', seqno, 0)
    return seqno

def parse_packet(buf):
    type = int.from_bytes(buf[:2], byteorder='big')
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
        control = Control(receiver_port, sender_port, txt_file_received, max_win)
    except ValueError:
        sys.exit(f"Invalid argument!")
    
    if not (min_port <= sender_port <= max_port or min_port <= receiver_port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}")
    if max_win < min_win:
        sys.exit(f"Invalid window argument, must larger or equal than {min_win}")

    return control

#--------------------------------------------------------------------------#
#------------------------Entrance of the code------------------------------#
#--------------------------------------------------------------------------#
if __name__ == "__main__":
    NUM_ARGS = 4  # Number of command-line arguments
    MSL = 1       # Maximum segment lifetimes, second
    t = {0: 'DATA', 1:'ACK', 2:'SYN', 3:'FIN'}
    window = {};    remainWin = 0;  startTime = 0
    control: Control
    main()