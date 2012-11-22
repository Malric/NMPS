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
       
def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    HOST = None    # Local host
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
    clients = []
    rtp_header = []
    # Stream status
    STREAM = False # Must be present for each client,only one for now,test purpose
    print 'Streamer ready'
    while True:     
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[],0)
        except select.error as msg:
            print 'Streamer: '+str(msg)
        for option in inputready:
            if option is unix_socket:
                data,addr = unix_socket.recvfrom(1024)
                print data,addr
                # print 'Streamer',address
                # IPC message format: Command,parameter,paremeter,...
                args = data.split(',')
                print args
                if args[0] == 'Setup':
                    #rtp = RTP.RTPMessage(random.randint(10000,60000))
                    clients.append([int(args[1]),int(args[2])]) # Append all active clients to list,Find idea to remove  
                    unix_socket.sendto('Ok,9000,9001',addr)
                    print 'sent'         
                elif args[0] == 'Play':
                    STREAM = True                
            if option is rtcp_socket:
                data = rtcp_socket.recv(1024)
                print data
        for client in clients:
            #rtp.sendto(client[2].createMessage(1,2,4),('::1',client[0]))
        time.sleep(1) # For now            
        
if __name__ == "__main__":
    main()


