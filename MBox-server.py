import argparse
import socket
import sys
import SIP
import SDP_sip


def server(port_sip):
    print "MBox Server running\r\n"
    HOST = ""
    PORT = port_sip
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))
    server_ip = socket.gethostbyname(socket.gethostname())
    print 
    while 1:
        try:
            data, addr = s.recvfrom(1024)
            print "Received data from " + str(addr[0]) + ":" + str(addr[1]) + ":"
            sip_inst = SIP.SIPMessage(data)
            if sip_inst.parse() is True:
                print sip_inst.SIPMsg
                client_ip = sip_inst.client_ip
                if sip_inst.SIPCommand == "INVITE":
                    sdp_inst = SDP_sip.SDPMessage("123456", "Talk", client_ip)
                    reply = sip_inst.createInviteReplyMessage(sdp_inst.SDPMsg, client_ip, server_ip)
                    print "Sending invite reply:"
                    print reply
                    sent = s.sendto(reply, addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                elif sip_inst.SIPCommand == "OPTIONS":
                    sdp_inst = SDP_sip.SDPMessage("123456", "Talk", client_ip)
                    reply = sip_inst.createOptionsReplyMessage(sdp_inst.SDPMsg, client_ip, server_ip)
                    print "Sending options reply:"
                    print reply
                    sent = s.sendto(reply, addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                elif sip_inst.SIPCommand == "BYE":
                    reply = sip_inst.createByeReplyMessage()
                    print "Sending bye reply:"
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