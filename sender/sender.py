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
    ori_data_recv: int = 0; orig_data_snd: int = 0
    ori_seg_snd: int = 0;   resend_seg: int = 0;    snd_seg_drp: int = 0
    dup_ack_recv: int = 0;  ack_drp: int = 0
#--------------------------------------------------------------------------#
#---------------------------------Main body--------------------------------#
#--------------------------------------------------------------------------#
def main():
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} port wait_time")
    global window, remainWin, startTime, log, control
    control = parse_argv(sys.argv)
    # print(control.rto)
    #-------------------------SYN_SENT-----------------------#
    seqno = random.randrange(2**16)
    control.socket.settimeout(control.rto);     startTime = time.time()
    remainWin = control.max_win;    send_pkt(SYN, seqno)

    while control.is_alive:
        try:
            pkt = control.socket.recv(1024)
            if int.from_bytes(pkt[:2], 'big') == 1:
                seqno = (seqno + 1) % 65536
                window.pop(seqno)
                record_log('rcv', t[1], seqno, 0)
                break
        except socket.timeout:
            send_pkt(SYN, seqno);  continue
    control.socket.settimeout(None)

    #--------------------Established & Finish state-------------------#
    filename = f'./sender/sendFiles/{control.txt_file_to_send}'
    with open(filename, 'r') as file:
        file = file.read().encode();    i = 1000
        seqno = send_pkt(DATA, seqno, file[0: i])
        control.orig_data_snd+=len(file[0: i]); control.ori_seg_snd+=1
        listener = threading.Thread(target=listen_thread, args=());    listener.start()
        timer = RepeatTimer(control.rto, resend_pkt, args=(window[min(window)], ))

        while control.is_alive:
            if i < len(file) and remainWin >= len(file[i:i+1000]):
                data = file[i:i+1000];  i += 1000
                seqno = send_pkt(DATA, seqno, data)
                control.ori_seg_snd+=1;     control.orig_data_snd += len(data)

                timer.cancel()
                timer = RepeatTimer(control.rto, resend_pkt, args=(window[min(window)], ))
                timer.start()
            #--------------Closing state---------------------#
            if i>=len(file) and remainWin == control.max_win : 
                timer.cancel()
                # print(f"closing {control.rto}")
                send_pkt(FIN, seqno)
                timer = RepeatTimer(control.rto, resend_pkt, args=(window[min(window)], ))
                timer.start()
                break
    #------------------------FIN_WAIT------------------------#
    with threading.Lock(): control.socket.settimeout(2)
    while control.is_alive:
        if not window:
            timer.cancel(); listener.join()
            control.is_alive = False
        else:
            continue
    log.write(f"\nOriginal data sent:\t\t\t{control.orig_data_snd}\n")
    log.write(f"Original data acked:\t\t{control.ori_data_recv}\n")
    log.write(f"Original segments sent:\t\t{control.ori_seg_snd}\n")
    log.write(f"Retransmitted segments:\t\t{control.resend_seg}\n")
    log.write(f"Dup acks received:\t\t\t{control.dup_ack_recv}\n")
    log.write(f"Data segments dropped:\t\t{control.snd_seg_drp}\n")
    log.write(f"Ack segments dropped:\t\t{control.ack_drp}\n")
    log.close()
    control.socket.close()
    sys.exit(0)
#--------------------------------------------------------------------------#
#------------------------Self defined functions----------------------------#
#--------------------------------------------------------------------------#
def send_pkt(type: int, seqno: int, data = b''):
    global startTime, log, window, remainWin, control
    pkt = type.to_bytes(2, "big")
    pkt += seqno.to_bytes(2, "big");    pkt += data
    if not drop(control.flp):
        control.socket.send(pkt)
        record_log('snd', t[type], seqno, len(data))
    else:
        record_log('drp', t[type], seqno, len(data))
        control.snd_seg_drp+=1

    len_data = len(data) if len(data) else 1
    seqno = (seqno + len_data) % 65536
    with threading.Lock():
        window[seqno] = pkt;   remainWin -= len(data) 
    # print(f"seqnos: {window.keys()}")
    return seqno

def listen_thread():
    global control, window, remainWin, log
    cnt = 0; last_seqno = 65536

    while control.is_alive:
        try:
            recv = control.socket.recv(1024)
            seqno = int.from_bytes(recv[2:4], "big")
            if not drop(control.rlp):
                record_log('rcv', t[1], seqno, 0)
                cnt = cnt + 1 if last_seqno == seqno else 1
                last_seqno = seqno
                if seqno in window:
                    with threading.Lock():
                        while window and min(window) <= seqno: 
                            length = len(window.pop(min(window))) -4
                            control.ori_data_recv += length
                            remainWin += length
                else:
                    # record_log('dupACKrecv', t[1], seqno, 0)
                    control.dup_ack_recv += 1
                if cnt == 3:
                    # print('cnt = 3:')
                    resend_pkt(window[min(window)])
                # print(f"seqnos: {window.keys()}")
            else:
                record_log('drp', t[1], seqno, 0)
                control.ack_drp += 1
        except socket.timeout:
            if window: 
                print(window.keys())
                continue
            else:  break
        except ConnectionRefusedError:
            control.is_alive = False
            break

def record_log(kind, type, seqno, length):
    global log, startTime
    print(f"{kind}\t %7.2f\t\t {type}\t {seqno}\t {length}\n" %((time.time() - startTime)*1000))

def drop(rate):
    random.seed()
    rand = random.random()
    if rand < rate: return True
    else:   return False

class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def resend_pkt(pkt): #will retransmit the file while timeout
    global control
    control.socket.send(pkt)
    type = int.from_bytes(pkt[:2], 'big');  seqno = int.from_bytes(pkt[2:4], 'big')
    # if type == 3:
        # print("resend: FIN")
    record_log('snd', t[type], seqno, len(pkt[4:]))
    control.resend_seg += 1

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
    DATA = 0;   ACK = 1;    SYN = 2;    FIN = 3
    t = {0: 'DATA', 1:'ACK', 2:'SYN', 3:'FIN'}
    window = {};   remainWin = 0;   startTime = 0
    log = open('./sender/sender_log.txt ', 'w+')
    control: Control
    main()