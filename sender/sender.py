#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import sys
import threading
import time
from dataclasses import dataclass

@dataclass
class Control:
    """Control block: parameters for the sender program."""
    sender_port: int
    receiver_port: int
    txt_file_to_send: str
    max_win: int
    rto: int;    flp: float;    rlp: float
    socket: socket.socket          
    is_alive: bool = True
#--------------------------------------------------------------------------#
#---------------------------------Main body--------------------------------#
#--------------------------------------------------------------------------#
def main():
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} port wait_time")
    control = parse_argv(sys.argv)
    global window, remainWin, startTime, log
    #-------------------------SYN_SENT-----------------------#
    random.seed();  seqno = random.randrange(2**16)
    control.socket.settimeout(control.rto)
    send_pkt(control, SYN, seqno);  startTime = time.time()
    while control.is_alive:
        try:
            pkt = control.socket.recv(control.max_win)
            if int.from_bytes(pkt[:2], 'big') == 1:
                seqno = (seqno + 1) % 65535
                log.write(f"rcv\t %7.2f\t\t {t[1]}\t {seqno}\t 0\n" %((time.time() - startTime)*1000))
                break
        except socket.timeout:
            send_pkt(control, SYN, seqno);  continue
    control.socket.settimeout(None)

    #--------------------Established & Finish state-------------------#
    listener = threading.Thread(target=listen_thread, args=(control, ))
    

    filename = f'./sender/sendFiles/{control.txt_file_to_send}'
    with open(filename, 'r') as file:
        
        file = file.read().encode(); i = 1000
        pkt = send_pkt(control, DATA, seqno, file[0: i])
        seqno = (seqno + len(file[0: i]))%65535
        window[seqno] = pkt;   remainWin = control.max_win - len(file[0: i])
        listener.start()

        while control.is_alive:
            if i < len(file) and remainWin > len(file[i:i+1000]):
                data = file[i:i+1000];  i += 1000
                pkt = send_pkt(control, DATA, seqno, data)
                
                data_len = len(data);    seqno = (seqno + data_len)%65535
                with threading.Lock():
                    remainWin -= data_len; window[seqno] = pkt 
            #--------------Closing state---------------------#
            elif i>=len(file) and remainWin >= 1:   
                pkt = send_pkt(control, FIN, seqno)
                with threading.Lock():    window[seqno] = pkt
                break
            else:
                continue

    #------------------------FIN_WAIT------------------------#
    while control.is_alive:
        if not window:
            listener.join()
            control.is_alive = False
        else:
            continue
    control.socket.close()
    
#--------------------------------------------------------------------------#
#------------------------Self defined functions----------------------------#
#--------------------------------------------------------------------------#
def send_pkt(control: Control, type: int, seqno: int, data = b''):
    global startTime, log
    pkt = type.to_bytes(2, "big")
    pkt += seqno.to_bytes(2, "big");    pkt += data

    control.socket.send(pkt)
    log.write(f"snd\t %7.2f\t\t {t[type]}\t {seqno}\t {len(data)}\n" %((time.time() - startTime)*1000))
    return pkt

def timer_thread(control: Control, pkt): #will retransmit the file while timeout
    global startTime, log
    control.socket.send(pkt)

    type = 'DATA' if len(pkt) > 4 else 'FIN'
    log.write(f"snd\t %7.2f\t\t {type}\t {int.from_bytes(pkt[2:4], "big")}\t 0\n" %((time.time() - startTime)*1000))

def listen_thread(control: Control):
    global window, remainWin
    timer = threading.Timer(control.rto, timer_thread, args=(control, window[min(window)]));    timer.start()

    while control.is_alive:
        try:
            recv = control.socket.recv(control.max_win)
            seqno = int.from_bytes(recv[2:4], "big")
            if seqno in window:
                log.write(f"rcv\t %7.2f\t\t {t[1]}\t {seqno}\t 0\n" %((time.time() - startTime)*1000))  
                with threading.Lock():  
                    remainWin += len(window.pop(seqno))
                timer.cancel()

                if window: #没有考虑 如果win 只有一个pkt
                    timer = threading.Timer(control.rto, timer_thread, args=(control, window[min(window)]))
                    timer.start()
                else:
                    break
            else:
                log.write(f"drp\t %7.2f\t\t {t[1]}\t {seqno}\t 0\n" %((time.time() - startTime)*1000))
        except BlockingIOError: #No data available to read
            continue
        
def setup_socket(remote, sender_port, receiver_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('', sender_port))
        sock.connect((remote, receiver_port))
    except Exception as e:
        sys.exit(f"Failed to connect to {remote}:{receiver_port}: {e}")
    return sock

def parse_argv(argv: list) -> Control:
    min_port = 49152;   max_port = 65535
    min_win = 1000
    try:
        sender_port = int(argv[1]); receiver_port = int(argv[2])
        txt_file_to_send = argv[3]
        max_win = int(argv[4])
        rto = int(argv[5]) / 1000.0
        flp = float(argv[6]); rlp = float(argv[7])

        host = '127.0.0.1';     socket = setup_socket(host, sender_port, receiver_port)
        control = Control(sender_port, receiver_port, txt_file_to_send, max_win, rto, flp, rlp, socket)
    except ValueError:
        sys.exit(f"Invalid argument!")
    
    if not (min_port <= control.sender_port <= max_port or min_port <= control.receiver_port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}")
    if control.max_win < min_win:
        sys.exit(f"Invalid window argument, must larger or equal than {min_win}")
    if not (0<= control.flp <=1):
        sys.exit(f"Invalid flp argument, must within [0, 1]")
    if not (0<= control.rlp <=1):
        sys.exit(f"Invalid rlp argument, must within [0, 1]")
    return control

#--------------------------------------------------------------------------#
#------------------------Entrance of the code------------------------------#
#--------------------------------------------------------------------------#
if __name__ == "__main__":
    NUM_ARGS  = 7  # Number of command-line arguments
    BUF_SIZE  = 3  # Size of buffer for receiving messages
    MAX_SLEEP = 2  # Max seconds to sleep before sending the next message
    DATA = 0;   ACK = 1;    SYN = 2;    FIN = 3
    t = {0: 'DATA', 1:'ACK', 2:'SYN', 3:'FIN'}
    window = {};   remainWin = 0;   startTime = 0
    log = open('./sender/sender_log.txt ', 'w+')
    main()