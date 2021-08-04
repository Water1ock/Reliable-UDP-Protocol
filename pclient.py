# 2018A7PS0270H    Vishesh Badjatya
# 2018A7PS0304H    Pranav
# 2018A7PS0292H    Riddhish Deotale
# 2018A7PS0631H    Shubhanjay Verma
# 2018A7PS0175H    Sri Satya Aditya Vithanala

import os
import socket
import sys

import rudp

filename = sys.argv[1]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 50001))
server_addr = ('127.0.0.1', 50000)

rudp.rsend(filename.encode('utf-8'), sock, server_addr)
file_buf, _ = rudp.rrecv(sock)

if file_buf == b'FNF':
    print('The requested file does not exist.')
else:
    if not os.path.exists('received_files'):
        os.makedirs('received_files')
    with open('received_files/' + filename, 'wb') as f:
        f.write(file_buf[3:])