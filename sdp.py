##
# SDP Message
##

import NTP
import math
import socket


class SDPMessage:

    def __init__(self, subject, session, port):
        self.v = "0"
        self.s = subject
        self.o = "Ltunez "+session+" "+NTP.timestamp()+" IN IP4 "\
				 +socket.gethostbyname(socket.gethostname())
        self.m = "audio 0 RTP/AVP 0" #u-law PCM! <-- Fix me for A-law # removed /2
        self.a = "sendonly"
        self.sdpMsg = "v="+self.v+"\r\n"
        self.sdpMsg +="o="+self.o+"\r\n"
        self.sdpMsg +="s="+self.s+"\r\n"
        self.sdpMsg +="m="+self.m+"\r\n"
        self.sdpMsg +="a="+self.a
	
    def getMessage(self):
        #print self.sdpMsg
        return self.sdpMsg

