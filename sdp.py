##
# SDP Message
##

import NTP
import math
import socket

terminator = "\r\n"

class SDPMessage:

    def __init__(self, program, subject, session):
        self.v = "0"
        self.s = subject
        self.o = program+" "+str(session)+" "+NTP.timestamp()+" IN IP4 "\
				 +socket.gethostbyname(socket.getfqdn())
        self.m = "audio 0 RTP/AVP 0" #u-law PCM! <-- Fix me for A-law # removed /2
        self.mode = ""
        self.rtpmap = ""
        self.c = ""
        self.t = ""
	   
    def setPort(self, port):
        self.m = "audio "+str(port)+" RTP/AVP 0"

    def setMode(self, mode):
        self.mode = mode

    def setRtpmap(self):
        self.rtpmap = "rtpmap:0 PCMU/8000/1"

    def setC(self):
        self.c = "IN IP4 " + socket.gethostbyname(socket.getfqdn())

    def setT(self):
        self.t = "0 0"
        
    def getMessage(self):
        #print self.sdpMsg
        self.sdpMsg = "v="+self.v+terminator
        self.sdpMsg +="o="+self.o+terminator
        self.sdpMsg +="s="+self.s+terminator
        if self.c != "":
            self.sdpMsg +="c="+self.t+terminator
        if self.t != "":
            self.sdpMsg +="t="+self.t+terminator
        self.sdpMsg +="m="+self.m+terminator
        if self.rtpmap != "":
            self.sdpMsg +="a="+self.rtpmap+terminator
        if self.mode != "":
            self.sdpMsg +="a="+self.mode
        return self.sdpMsg

