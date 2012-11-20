###
# RTP/RTCP streamer
###

import select
import socket
import sys
import time
import RTP
       
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
 
def main():
    """ Streamer """
    fd = int(sys.argv[1])
    u_sock = socket.fromfd(fd,socket.AF_UNIX, socket.SOCK_STREAM) #Create socket object
    rtp_sock = bind(9000)
    if rtp_sock is None:
        sys.exit(1)
    rtcp_sock = bind(9001)
    if rtcp_sock is None:
        sys.exit(1)
    inputs = []
    inputs.append(u_sock)   # adding unix socket
    inputs.append(rtcp_sock) # adding rtcp socket
    while True:     
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[])
        except select.error as msg:
            print 'Streamer: '+str(msg)
        for option in inputready:
            if option is u_sock:
                data = u_sock.recv(1024)
                print data
            if option is rtcp_sock:
                data = rtcp_sock.recv(1024)
                print data

if __name__ == "__main__":
    main()


