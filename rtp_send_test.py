import argparse
import socket
import sys


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


def rtp_send(port_rtp, port_rrtp):
    print "RTP Sender running\r\n"
    s = bind(port_rtp)
    receiver_ip = socket.gethostbyname(socket.gethostname())

    sent = s.sendto("Test", (receiver_ip, port_rrtp))
    print >>sys.stderr, "Sent %s bytes to %s" % (sent, (receiver_ip, port_rrtp))
    
    s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rtp", help="RTP port", type=int)
    parser.add_argument("-rr", "--rrtp", help="receiver RTP port", type=int)
    args = parser.parse_args()       
    rtp_send(args.rtp, args.rrtp)
