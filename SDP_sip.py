###
#
# SDP Message (SIP version)
#
###

import socket


class SDPMessage:

    def __init__(self, session, subject):
        self.v = "0"
        self.o = "test " + session + " 654321 IN IP4 " + socket.gethostbyname(socket.gethostname())
        self.s = subject
        self.c = "IN IP4 " + socket.gethostbyname(socket.gethostname())
        self.t = "0 0"
        self.m = "audio 8078 RTP/AVP 0 101"
        self.a = "rtpmap:0 PCMU/8000/1"
        self.SDPMsg = "v=" + self.v + "\r\n"
        self.SDPMsg += "o=" + self.o + "\r\n"
        self.SDPMsg += "s=" + self.s + "\r\n"
        self.SDPMsg += "c=" + self.c + "\r\n"
        self.SDPMsg += "t=" + self.t + "\r\n"
        self.SDPMsg += "m=" + self.m + "\r\n"
        self.SDPMsg += "a=" + self.a
        