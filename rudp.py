# 2018A7PS0270H    Vishesh Badjatya
# 2018A7PS0304H    Pranav
# 2018A7PS0292H    Riddhish Deotale
# 2018A7PS0631H    Shubhanjay Verma
# 2018A7PS0175H    Sri Satya Aditya Vithanala

import concurrent.futures
import time
import socket

window_size = 4     # maximum window size
timeout = 1         # timeout in seconds

def checksum(bytestring, position):
    result = 0
    for i in range(position, min( position + 986, len(bytestring) ) ):
        result = result + bytestring[i]
    
    return (result % 255).to_bytes(1, 'little')     # compute sum of all bytes mod 255

def rrecv(sock):
    buf = bytearray(0)
    ack_packet = bytearray(8)
    ack_packet += (2).to_bytes(1, 'little')     # building the ACK packet
    nack_packet = bytearray(8)
    nack_packet += (1).to_bytes(1, 'little')    # building the NACK packet

    packet_list = []

    loop_count = -1
    while loop_count != 0:                                              # main loop
        data, addr = sock.recvfrom(1000)

        if data[8] == 2 or data[8] == 1:                                # if the packet is an ACK or NACK from a previous transmission:
            continue                                                        # discard it and receive next packet

        packet_no = int.from_bytes(data[:4], 'little')                  # extract SequenceNumber from packet
        if loop_count == -1 and data[13].to_bytes(1, 'little') == checksum(data[14:], 0):   # if the packet is the first packet and is intact
            loop_count = int.from_bytes(data[4:8], 'little')            # extract LastPacket from packet
            print(f'Total number of incoming packets = {loop_count}')
            for _ in range(loop_count):
                packet_list.append(0)

        if data[13].to_bytes(1, 'little') == checksum(data[14:], 0):    # if checksum checks out
            if loop_count < window_size:                                             # if last packet
                for _ in range(40):
                    sock.sendto(ack_packet + data[:4] + bytes(b'\x00'), addr)   # send 20 ACKs (to mitigate 2 generals upto 95% packet loss)
                print(f"packet {packet_no} received, ACK sent")
            else:
                sock.sendto(ack_packet + data[:4] + bytes(b'\x00'), addr)       # send ACK
                print(f"packet {packet_no} received, ACK sent")
            if packet_list[packet_no] == 0:    # if packet not already in list (not resent)
                packet_list[packet_no] = data  # add to list
                loop_count -= 1

        else:                                                           # if checksum is wrong
            sock.sendto(nack_packet + data[:4] + bytes(b'\x00'), addr)  # send NACK
            print(f"packet {packet_no} corrupted, NACK sent")
    
    for packet in packet_list:
        buf += packet[14:]
    
    return buf, addr

def rsend(buf, sock, addr):
    rsend.window = []

    seq = 0
    last_packet = (len(buf) + 986 - 1) // 986   # ceil(buffer length / usable packet length)
    packet_list = []

    for seq in range(last_packet):      # Packetize the contents of buf
        packet_list.append(bytearray(0))
        packet_list[seq] += seq.to_bytes(4, 'little')                       # write header sequence number
        packet_list[seq] += last_packet.to_bytes(4, 'little')               # write header last packet
        packet_list[seq] += (0).to_bytes(5, 'little')                       # write header ack nack byte
        packet_list[seq] += checksum(buf, seq*986)                          # write header checksum
        packet_list[seq] += buf[seq*986:min( (seq + 1)*986, len(buf)) ]     # write payload

    print(f'buffer packetized into {last_packet} packets')
    with open('out.txt', 'a') as f:
        f.write(str(packet_list[0]))

    # start sending packets using selective repeat    
    rsend.ack_list = []
    for _ in range(last_packet):
        rsend.ack_list.append(0)      # initialize ack_list list with zeroes
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(listen_for_acks, sock)  # start thread that listens for ACKs
        
        for seq in range(last_packet):
            while True:
                if len(rsend.window) < window_size:     # if window is not full then add new packet, else sleep for 1 second
                    rsend.window.append(seq)
                    executor.submit(send_packet, sock, addr, packet_list[seq], seq, timeout)
                    break

def listen_for_acks(sock):
    while 0 in rsend.ack_list:
        ack, _ = sock.recvfrom(14)
        ack_no = int.from_bytes(ack[9:13], 'little')    # extract AckNackNumber from packet
        
        if ack[8] == 2:
            is_ack = True
        else:
            is_ack = False
        
        if is_ack:
            if ack_no in rsend.window:
                if rsend.ack_list[ack_no] == 0:
                    rsend.ack_list[ack_no] = ack
                    rsend.window.remove(ack_no)  # after ACK is received, remove packet from the window
                    print(f'ACK {ack_no} received')
                else:
                    print(f'ACK {ack_no} received again')
        else:
            print(f'NACK {ack_no} received, retransmitting')
    
    print('all ACKs received')

def send_packet(sock, addr, packet, packet_no, timeout):
    while True:
        if rsend.ack_list[packet_no] == 0:
            sock.sendto(packet, addr)
            print(f'packet {packet_no} sent')
        else:
            break
        time.sleep(timeout)