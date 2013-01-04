###
# RTP/RTCP streamer
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

class Client():
    rtp = 0  # rtp port
    rtcp = 0 # rtcp port
    STREAM = False # bool,if streaming on for this client
    ip = '' # # Client ip
    index = 0 # song byte index
    sequence = random.randint(1,10000)
    timestamp = random.randint(1,10000)

def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    #HOST = '127.0.0.1'    # Local host
    HOST = "192.168.11.20"
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_DGRAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            print 'Streamer: '+str(msg)
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print 'Streamer: '+str(msg)
            s.close()
            s = None
            continue
        break
    return s
 
# One streamer per song for all clients
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
    inputs.append(rtcp_socket) # Add rtcp socket
    # Is list filled once
    ONCE = False
    # List of client
    clients = dict() #dict containing all clients for this song
    rtpheader = RTP.RTPMessage(24567)
    wavef = wav.Wave(sys.argv[2]+'/'+sys.argv[1])
    song = wavef.getdata()
    songsize = wavef.getnframes()
    while True:     
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[],0)
        except select.error as msg:
            print 'Streamer: '+str(msg)
        for option in inputready:
            if option is unix_socket:
                data,addr = unix_socket.recvfrom(1024)
                m = scp.SCPMessage()
                t = m.parse(data)
                if m.command == "SETUP":
                    ONCE = True
                    c = Client()
                    c.rtp = m.clientRtpPort
                    c.rtcp = m.clientRtcpPort
                    c.ip = m.clientIp
                    clients[addr] = c
                    unix_socket.sendto(m.createPort(None,str(port),str(port+1)),addr)
                elif m.command == "TEARDOWN":
                    clients.pop(addr)
                elif m.command == "PLAY":
                    clients[addr].STREAM = True
                    unix_socket.sendto(m.createRunning(str(clients[addr].sequence), str(clients[addr].timestamp)),addr)
                elif m.command == "PAUSE":
                    clients[addr].STREAM = False	                
            if option is rtcp_socket:
                data = rtcp_socket.recv(1024)
                pass                 
                #print data # For now,lets see how it goes
        vs = clients.values()
        rtpPacketSendRate = 1
        for v in vs:
            if v.STREAM and v.index < songsize:
                buff = rtpheader.createMessage(v.sequence,v.timestamp,0)
                packet = buffer(buff)
                packet = packet + song[v.index:v.index+1400*rtpPacketSendRate]
                rtp_socket.sendto(packet,(v.ip,int(v.rtp)))
                v.index = v.index + 1400*rtpPacketSendRate
                v.sequence = v.sequence + 1
                v.timestamp = v.timestamp + 1400*rtpPacketSendRate  
        time.sleep(0.175)      
        if ONCE and len(clients) == 0:
            break
    unix_socket.close()
    os.remove(path)
    rtp_socket.close()
    rtcp_socket.close()
        
if __name__ == "__main__":
    main()

