###
#
# SDP Message (SIP version)
#
###

import socket

terminator="\r\n"

class SDPMessage:

    def __init__(self, session, subject, ip):
        self.v = "0"
        self.o = "test " + session + " 654321 IN IP4 " + ip
        self.s = subject
        self.c = "IN IP4 " + ip
        self.t = "0 0"
        self.m = "audio 8000 RTP/AVP 0 101"
        self.a = "rtpmap:0 PCMU/8000/1"
        self.SDPMsg = "v=" + self.v + terminator
        self.SDPMsg += "o=" + self.o + terminator
        self.SDPMsg += "s=" + self.s + terminator
        self.SDPMsg += "c=" + self.c + terminator
        self.SDPMsg += "t=" + self.t + terminator
        self.SDPMsg += "m=" + self.m + terminator
        self.SDPMsg += "a=" + self.a + terminator
        
