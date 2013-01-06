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
import sdp
import ctypes
import writer
import helpers
import io
import datetime

server_ip = ""
RTP_PACKET_MAX_SIZE = 1500


def getTimestamp():
    time = datetime.datetime.today()
    timestamp = str(time.year)+"."+str(time.month)+"."+str(time.day)+"_"+str(time.hour)+":"+str(time.minute)+":"+str(time.second)
    return timestamp

def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    #HOST = '127.0.0.1'    # Local host
    HOST = server_ip
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
    def __init__(self,addr, userid):
        """ Init """
        threading.Thread.__init__(self)
        self.load = ''
        self.addr = addr
        self.rtp_socket = bind(8078)
        self.rtcp_socket = bind(8079)
        self.rbuf = io.BytesIO()
        self.offset = 0
        self.userid = userid

    def run(self):
        """ Main loop """
        inputs = []
        inputs.append(self.rtp_socket)
        inputs.append(self.rtcp_socket)
        rtpmessage = RTP.RTPMessage(24567)
        while True:
            if flows[self.addr].stop == True:
                print "Printing file"
                writer.wavwriter(self.load,len(self.load),self.userid+"_"+getTimestamp()+".wav")
                flows.pop(self.addr)
                inputs.remove(self.rtp_socket)
                inputs.remove(self.rtcp_socket)
                self.rtp_socket.close()
                self.rtcp_socket.close()
                self.rbuf.close()
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
                    data, addr = self.rtp_socket.recvfrom(RTP_PACKET_MAX_SIZE)
                    self.rbuf.seek(0, io.SEEK_END)
                    written = self.rbuf.write(data)
                    self.rbuf.seek(-written, io.SEEK_CUR)
                    self.rbuf.readinto(rtpmessage.header)
                    rtpmessage.updateFields()
                    self.offset += rtpmessage.getOffset()
                    self.rbuf.seek(self.offset, io.SEEK_CUR)
                    payloadLen = written-self.offset-12
                    payload = self.rbuf.read(payloadLen)
                    print "Single packet: " +str(len(payload))
                    self.load += payload
                    print "Total load: " +str(len(self.load))            
                    # HANDLE PAYLOAD
         
def server(sip_port):
    """ Sip server """
    print sip_port
    sip_socket = bind(sip_port)
    inputs = []
    print 'Sip server started'
    inputs.append(sip_socket)
    session = random.randint(1,10000)
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
                #server_ip = socket.gethostbyname(socket.gethostname())
                sip_inst = SIP.SIPMessage(buff)
                if sip_inst.parse() is True:
                    print sip_inst.SIPMsg
                    client_ip = sip_inst.client_ip
                    if sip_inst.SIPCommand == "INVITE":
                        #Start receiving
                        f = Flow()
                        flows[addr] = f # Use port of remote end too
                        r = Receiver(addr,sip_inst.userId)
                        r.start()
                        sdp_inst = sdp.SDPMessage("MBox", "Talk", session)
                        sdp_inst.setPort(8078)
                        sdp_inst.setRtpmap()
                        sdp_inst.setC()
                        sdp_inst.setT()
                        reply = sip_inst.createInviteReplyMessage(sdp_inst.getMessage(), client_ip, server_ip, sip_port)
                        print "Sending invite reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                    elif sip_inst.SIPCommand == "OPTIONS":
                        sdp_inst = sdp.SDPMessage("MBox", "Talk", session)
                        sdp_inst.setPort(8078)
                        sdp_inst.sip_port = sip_port
                        sdp_inst.setRtpmap()
                        sdp_inst.setC()
                        sdp_inst.setT()
                        reply = sip_inst.createOptionsReplyMessage(sdp_inst.getMessage(), client_ip, server_ip, sip_port)
                        print "Sending options reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                    elif sip_inst.SIPCommand == "BYE":
                        #Leave
                        flows[addr].stop = True
                        reply = sip_inst.createByeReplyMessage(server_ip, sip_port)
                        print "Sending bye reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                        break
                   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sip", help="SIP server port", type=int)
    args = parser.parse_args()
    server_ip = helpers.sockLocalIp()      
    server(args.sip)
