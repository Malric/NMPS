####
#
# RTSP Message
#
####

import re
import urllib
import urlparse
import logging

#RTSP Commands (Supported)
commands = ["DESCRIBE", "SETUP", "TEARDOWN", "PLAY", "PAUSE"]

class RTSPMessage:

    def __init__(self, message):
        self.rtspCommand = ""
        self.URI         = ""
        self.protocol    = ""
        self.pathname    = ""
        self.cseq        = ""
        self.bandwith    = ""
        self.bufsize     = ""
        self.session     = ""
        self.speed       = ""
        self.transport   = ""
        self.range       = ""
        self.clientport  = ""
 
        self.rtspMsg = message

        #Regex for different fields

        self.bandwidthRegex = re.compile(r'Bandwith: (.*)$', re.IGNORECASE)
        self.cseqRegex = re.compile(r'Cseq: (.*)$', re.IGNORECASE)
        self.sessionRegex = re.compile(r'Session: (.*)$', re.IGNORECASE)
        self.speedRegex = re.compile(r'Speed: (.*)$', re.IGNORECASE)
        self.bufsizeRegex = re.compile(r'BufSize: (.*)$', re.IGNORECASE)
        self.transportRegex = re.compile(r'Transport: (.*)$', re.IGNORECASE)
        self.rangeRegex = re.compile(r'Range: (.*)$', re.IGNORECASE)
        self.clientportRegex = re.compile(r'client_port=: (.*)$', re.IGNORECASE)

    def tostring(self):
        return self.rtspMsg

    def fromstring(self, message):
        self.rtspMsg = message

    ####
    #
    # Parsering
    #
    ####

    def parse(self):
        lines = self.rtspMsg.split('\r\n')
                   
        #Line 1: Command, URI, Protocol
        try:
            (command, uri, protocol) = lines[0].split()
        except ValueError:
            return
        
        self.rtspCommand = command
        self.protocol = protocol
        print "Command: "+command+"\n"
        print "Protocol: "+protocol+"\n"
        self.URI = uri
        self.parseURI()
    
        for line in lines:
            hits = self.cseqRegex.search(line)
            if hits is not None:
                self.cseq = hits.group(1)
                print "Cseq: " +self.cseq+"\n"
            
            hits = self.bandwidthRegex.search(line)
            if hits is not None:
                self.bandwith = hits.group(1)
                print "Bandwidth: " +self.bandwidth + "\n"

            hits = self.sessionRegex.search(line)
            if hits is not None:
                self.session = hits.group(1)
                print "Session: " + self.session + "\n"

            hits  = self.speedRegex.search(line)
            if hits is not None:
                self.speed = hits.group(1)
                print "Bufsize: " +self.speed + "\n"

            hits = self.bufsizeRegex.search(line)
            if hits is not None:
                self.bufsize = hits.group(1)
                print "Bufsize: " + self.bufsize +"\n"

            hits = self.transportRegex.search(line)
            if hits is not None:
                self.transport = hits.group(1)
                print "Transport: "+self.transport+"\n"
                sections = self.transport.split("=")
                clientport = sections[0]

            hits = self.rangeRegex.search(line)
            if hits is not None:
                self.range = hits.group(1)
                print "Range: "+self.range+"\n"

            
    def parseURI(self):
        #Reverse escapes
        self.URI = urllib.unquote(self.URI) 
        uriSections = urlparse.urlparse(self.URI)

        #urlSections[0] == scheme, [1] == netlocation, [2] == path
        #[1:] to remove prepended /
        self.pathname = uriSections[2][1:]
        print self.pathname +"\n"

    def dumpMessage(self):
        #Convert using logging methods
        print self.rtspMsg

    def createOptionsReplyMessage(self):
        self.rtspMsg = ""
        self.rtspMsg += self.protocol +" 200 OK\r\n"
        self.rtspMsg += "CSeq: "+ self.cseq +"\r\n"
        self.rtspMsg += "Public: "
        for command in commands:
            self.rtspMsg += command +", "
        self.rtspMsg = self.rtspMsg[0:(len(self.rtspMsg) -2)]
        self.rtspMsg +="\r\n"
        return self.rtspMsg

a = RTSPMessage("OPTIONS rtsp://example.com/media.mp4 RTSP/1.0 \r\n"\
                "CSeq: 1\r\n"\
                "Require: implicit-play\r\n"\
                "Proxy-Require: gzipped-messages\r\n")

print a.tostring()
a.parse()
print a.createOptionsReplyMessage()

b = RTSPMessage("DESCRIBE rtsp://example.com/media.mp4 RTSP/1.0\r\n"\
                "CSeq: 2\r\n")

print b.tostring()
b.parse()


c= RTSPMessage("SETUP rtsp://example.com/media.mp4/streamid=0 RTSP/1.0\r\n"\
               "CSeq: 3\r\n"\
               "Transport: RTP/AVP;unicast;client_port=8000-8001\r\n")

print c.tostring()
c.parse()

d= RTSPMessage("PLAY rtsp://example.com/media.mp4 RTSP/1.0\r\n"\
               "CSeq: 4\r\n"\
               "Range: npt=5-20\r\n"\
               "Session: 12345678\r\n")

print d.tostring()
d.parse()

e= RTSPMessage("TEARDOWN rtsp://example.com/media.mp4 RTSP/1.0\r\n"\
               "CSeq: 8\r\n"\
               "Session: 12345678\r\n")

print e.tostring()
e.parse()

f = RTSPMessage("PAUSE rtsp://example.com/media.mp4 RTSP/1.0\r\n"\
                "CSeq: 5\r\n"\
                "Session: 12345678\r\n")

print f.tostring()
f.parse()