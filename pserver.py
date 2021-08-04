# 2018A7PS0270H    Vishesh Badjatya
# 2018A7PS0304H    Pranav
# 2018A7PS0292H    Riddhish Deotale
# 2018A7PS0631H    Shubhanjay Verma
# 2018A7PS0175H    Sri Satya Aditya Vithanala

import socket

import rudp

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 50000))
print('Server started, listening for requests...')
while True:
    filename, client_addr = rudp.rrecv(sock)
    filename = filename.decode('utf-8')

    print(f"Client requested file: {filename}")

    try:
        f = open(filename, 'rb')
        file_buf = b'FFF' + f.read()

        f.close()

    except FileNotFoundError:
        file_buf = b'FNF'
        print('Error: The requested file does not exist.')
    
    rudp.rsend(file_buf, sock, client_addr)