###
# RTP/RTCP reciever
###

import random
import select
import socket
import sys
import time
import RTP
import os
import scp
import wave
import ctypes
import wav

RTP_PACKET_MAX_SIZE = 1500


def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    #HOST = '127.0.0.1'    # Local host
    HOST = socket.gethostbyname(socket.gethostname())
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_DGRAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            print 'Receiver: '+str(msg)
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print 'Receiver: '+str(msg)
            s.close()
            s = None
            continue
        break
    return s
 
# One Reciever / client / song
def main():
    """ Control section for streamer. """
    # Create unix socket for IPC
    path = 'Sockets/'+sys.argv[1]
    if os.path.exists(path): #Caution
        sys.exit(1)
    unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    unix_socket.bind(path)
    # Create rtp and rtcp socket
    while True:
        while True:
            port = random.randint(10000,65000)
            rtp_socket = bind(port)
            if rtp_socket is None:
                continue
            else:
                break
        rtcp_socket = bind(port + 1)
        if rtcp_socket is None:
            rtp_socket.close()
        else:
            break
    inputs = []
    inputs.append(unix_socket) # Add unix socket
    inputs.append(rtp_socket) # Add rtp socket
    inputs.append(rtcp_socket) # Add rtcp socket
    # Is list filled once
    # List of client
    #clients = dict() #dict containing all clients for this song
    rtpmessage = RTP.RTPMessage(24567)
    #wavef = wav.Wave('Wavs/'+sys.argv[1])
    #song = wavef.getdata()
    #songsize = wavef.getnframes()
    while True:     
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[],0)
        except select.error as msg:
            print 'Receiver: '+str(msg)
        for option in inputready:
            if option is unix_socket:
                data,addr = unix_socket.recvfrom(1024)
                m = scp.SCPMessage()
                t = m.parse(data)
                if m.command == "SETUP":
                    unix_socket.sendto(m.createPort(None,str(port),str(port+1)),addr)
                elif m.command == "TEARDOWN":
                    #SAVE FILE
                    break        
            if option is rtcp_socket:
                data = rtcp_socket.recv(1024)
                pass                 
                #print data # For now,lets see how it goes
            if option is rtp_socket:
                data, addr = rtp_socket.recvfrom_into(rtpmessage.header,12)
                rtpmessage.updateFields()
                offset = rtpmessage.getOffset()
                #print "Offset: "+str(offset)
                if offset != 0:
                    data2,addr = s.recvfrom(offset)
                    #print data2
                payload, addr = s.recvfrom(RTP_PACKET_MAX_SIZE)
                # HANDLE PAYLOAD
       
    unix_socket.close()
    os.remove(path)
    rtp_socket.close()
    rtcp_socket.close()
        
if __name__ == "__main__":
    main()

