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

class Client():
    rtp = 0  # rtp port
    rtcp = 0 # rtcp port
    STREAM = False # bool,if streaming on for this client
    ip = '' # # Client ip
    index = 0 # song byte index
    sequence = 1000
    timestamp = 2000

def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    HOST = '127.0.0.1'    # Local host
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
    print path
    if os.path.exists(path): #Caution
        sys.exit(1)
    unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    unix_socket.bind(path)
    # Create rtp and rtcp socket
    while True:
        while True:
            #port = random.randint(10000,65000)
            port = 9000
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
    # List of client
    clients = dict() #dict containing all clients for this song
    # Stream status
    STREAM = False # Must be present for each client,only one for now,test purpose
    print 'Streamer ready'
    rr = RTP.RTPMessage(24567)
    f = None
    try:
        f = wave.open('Wavs/jayate.wav','rb' )
    except wave.Error as msg:
        print 'Wav open ',msg    
    song = f.readframes(f.getnframes())
    f.close()
    print rtp_socket.getsockname()
    count = 0
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
                    c = Client()
                    c.rtp = m.clientRtpPort
                    c.rtcp = m.clientRtcpPort
                    c.ip = m.clientIp
                    clients[addr] = c
                elif m.command == "TEARDOWN":
                    clients.pop(addr)
                elif m.command == "PLAY":
                    clients[addr].STREAM = True
                elif m.command == "PAUSE":
                    clients[addr].STREAM = False	                
            if option is rtcp_socket:
                data = rtcp_socket.recv(1024)
                print data # For now,lets see how it goes
        vs = clients.values()
        for v in vs:
            if v.STREAM:
                mmm = rr.createMessage(v.sequence,v.timestamp,0)
                packet = buffer(mmm)
                packet = packet + song[v.index:v.index+32]
                print 'Size',len(packet)
                rtp_socket.sendto(packet,(v.ip,int(v.rtp)))
                print 'Add',v.ip,v.rtp
                v.index = v.index + 32
                v.sequence = v.sequence + 1
                v.timestamp = v.timestamp + 32  
                count = count + 1
        #time.sleep(1)      
        if count > 10000:
            break
    rtp_socket.close()
    rtcp_socket.clsoe()
        
if __name__ == "__main__":
    main()


