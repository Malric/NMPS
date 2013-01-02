import argparse
import socket
import RTP
import os
import scp
import wave
import ctypes


def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    HOST = socket.gethostbyname(socket.gethostname())
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_DGRAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            print str(msg)
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print str(msg)
            s.close()
            s = None
            continue
        break
    return s


def rtp_receive(port_rtp):
    print "RTP Receiver running\r\n"
    s = bind(port_rtp)

    rtpheader = RTP.RTPMessage(24567)
    Once = True
    while Once:
        try:
            print "Looptaan"
            data, addr = s.recvfrom_into(rtpheader.header,1024)
            print "Received data from " + str(addr[0]) + ":" + str(addr[1]) + ":"
            rtpheader.updateFields()
            rtpheader.printFields()
            rtpheader.printHeader()
            print rtpheader.getOffset()
            #Once = False
        except KeyboardInterrupt:
            break
    s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rtp", help="RTP port", type=int)
    args = parser.parse_args()       
    rtp_receive(args.rtp)