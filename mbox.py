####
# SIP server
####

import RTP
import sys
import argparse
import socket
import threading
import select
import re
import os
import shutil
import RTSP
import sdp
import playlist
import time
import scp
import tempfile
import random
import SIP
import SDP_sip
import ctypes
import writer

RTP_PACKET_MAX_SIZE = 1500

def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    HOST = '192.168.11.20'    # Local host
    #HOST = socket.gethostbyname(socket.gethostname())
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

class Flow():
    start = True
    stop = False

flows = dict()

class Receiver(threading.Thread):
    """ Receives rtp and rtcp messages """
    def __init__(self,addr):
        """ Init """
        threading.Thread.__init__(self)
        self.load = ''
        self.addr = addr
        self.rtp_socket = bind(8000)
        self.rtcp_socket = bind(8001)
	self.count = 0
    def run(self):
        """ Main loop """
	print 'Thread'
        inputs = []
        inputs.append(self.rtp_socket)
        inputs.append(self.rtcp_socket)
        rtpmessage = RTP.RTPMessage(24567)
        while True:
            if flows[self.addr].stop == True:
		print 'OK,Done'
                writer.wavwriter(self.load,len(self.load),'msg.wav')
                flows.pop(self.addr)
                inputs.remove(self.rtp_socket)
                inputs.remove(self.rtcp_socket)
                self.rtp_socket.close()
                self.rtcp_socket.close()
                break
            try:
                inputready,outputready,exceptready = select.select(inputs,[],[],0)
            except select.error as msg:
                print 'Receiver: '+str(msg)
            for option in inputready:        
                if option is self.rtcp_socket:
                    data = self.rtcp_socket.recv(1024)
                    pass                
                    #print data # For now,lets see how it goes
                if option is self.rtp_socket:
		    print '.--------------------'
                    data, addr = self.rtp_socket.recvfrom_into(rtpmessage.header,12)
                    rtpmessage.updateFields()
                    offset = rtpmessage.getOffset()
                    #print "Offset: "+str(offset)
                    if offset != 0:
                        data2,addr = self.rtp_socket.recvfrom(offset)
                        #print data2
                    payload, addr = self.rtp_socket.recvfrom(RTP_PACKET_MAX_SIZE)
                    self.count += len(payload)
		    print self.count
                    self.load += payload                    
                    # HANDLE PAYLOAD
         
def server(sip_port):
    """ Sip server """
    print sip_port
    sip_socket = bind(sip_port)  
    inputs = []
    print 'Sip server started'
    inputs.append(sip_socket)
    while True:
        try:
            inputready,outputready,exceptready = select.select(inputs, [], [])
        except KeyboardInterrupt:
            inputs.remove(sip_socket)
            sip_socket.close()
            break
        for option in inputready:
            if option is sip_socket: # only this possible
                buff = ''
                try:
                    buff, addr = sip_socket.recvfrom(1024)
                except socket.error as msg:
                    print 'Server: SIP ', msg
                    continue
                print 'Server: SIP message from ', addr, ':'
                server_ip = '192.168.11.20' #socket.gethostbyname(socket.gethostname())
                sip_inst = SIP.SIPMessage(buff)
                if sip_inst.parse() is True:
                    print sip_inst.SIPMsg
                    client_ip = sip_inst.client_ip
                    if sip_inst.SIPCommand == "INVITE":
                        #Start receiving
                        f = Flow()
                        flows[addr] = f # Use port of remote end too
			print 'invite'                
		        r = Receiver(addr)
                        r.start()
			print 'started'
                        sdp_inst = SDP_sip.SDPMessage("123456", "Talk", client_ip)
                        reply = sip_inst.createInviteReplyMessage(sdp_inst.SDPMsg, client_ip, server_ip)
                        print "Sending invite reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                    elif sip_inst.SIPCommand == "OPTIONS":
                        sdp_inst = SDP_sip.SDPMessage("123456", "Talk", client_ip)
                        reply = sip_inst.createOptionsReplyMessage(sdp_inst.SDPMsg, client_ip, server_ip)
                        print "Sending options reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                    elif sip_inst.SIPCommand == "BYE":
                        #Leave
                        flows[addr].stop = True
                        reply = sip_inst.createByeReplyMessage(server_ip)
                        print "Sending bye reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                        break
                   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sip", help="SIP server port", type=int)
    args = parser.parse_args()       
    server(args.sip)
