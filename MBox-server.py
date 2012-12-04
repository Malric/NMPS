import argparse
import socket
import sys
import SIP
import SDP_sip


def server(port_sip):
    HOST = ""
    PORT = port_sip
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))

    while 1:
        try:
            data, addr = s.recvfrom(1024)
            print "Received data from " + str(addr[0]) + ":" + str(addr[1]) + ":"
            sip_inst = SIP.SIPMessage(data)
            if sip_inst.parse() is True:
                print sip_inst.SIPMsg
                if sip_inst.SIPCommand == "INVITE":
                    sdp_inst = SDP_sip.SDPMessage("123456", "A conversation")
                    reply = sip_inst.createInviteReplyMessage(sdp_inst.SDPMsg)
                    print "Sending reply:"
                    print reply
                    sent = s.sendto(reply, addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                elif sip_inst.SIPCommand == "BYE":
                    reply = sip_inst.createByeReplyMessage()
                    print "Sending reply:"
                    print reply
                    sent = s.sendto(reply, addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
        except KeyboardInterrupt:
            break
    s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sip", help="SIP server port", type=int)
    args = parser.parse_args()       
    server(args.sip)