####
# RTSP Message
#
####

import re
import urllib
import urlparse
import logging

#RTSP Commands (Supported)
commands = ["OPTIONS", "DESCRIBE", "SETUP", "TEARDOWN", "PLAY", "PAUSE"]

class RTSPMessage():

    def __init__(self, message):
        self.rtspCommand = ""
        self.URI         = ""
        self.protocol    = "RTSP/1.0"
        self.pathname    = ""
        self.cseq        = ""
        self.bandwith    = ""
        self.bufsize     = ""
        self.session     = ""
        self.speed       = ""
        self.transport   = ""
        self.range       = ""
        self.clientport  = ""
        
        if message is not None:
            self.rtspMsg = message
        else:
            self.rtspMsg = ""

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
            return False
        
        if protocol != self.protocol:
            return False

        if command not in commands:
            return False

        self.rtspCommand = command
        self.protocol = protocol
        self.URI = uri
        self.parseURI()

        for line in lines:
            hits = self.cseqRegex.search(line)
            if hits is not None:
                self.cseq = hits.group(1)    
            hits = self.bandwidthRegex.search(line)
            if hits is not None:
                self.bandwith = hits.group(1)
            hits = self.sessionRegex.search(line)
            if hits is not None:
                self.session = hits.group(1)
            hits  = self.speedRegex.search(line)
            if hits is not None:
                self.speed = hits.group(1)
            hits = self.bufsizeRegex.search(line)
            if hits is not None:
                self.bufsize = hits.group(1)
            hits = self.transportRegex.search(line)
            if hits is not None:
                self.transport = hits.group(1)
                sections = self.transport.split("client_port=")
                if sections is not None:
                    self.transport = sections[0]
                    self.clientport = sections[1]
            hits = self.rangeRegex.search(line)
            if hits is not None:
                self.range = hits.group(1)
        value = self.sanityCheck()     
        
        if value == False:
            return False
        else:
            return True
        
    ##
    #   Sanitychecker...
    ##
    def sanityCheck(self):
        if self.cseq == "" or self.cseq <0:
            return False
        if self.rtspCommand == "DESCRIBE":
            if self.pathname == "":
                print "Faulty packet! Pathname could not be found!"
        elif self.rtspCommand == "SETUP":
            if self.transport == "":
                print "Faulty packet! Transport missing!"
                return False
            elif self.clientport == "":
                print "Faulty packet! Client_port was missing!"
                return False
        elif self.rtspCommand == "PLAY":
            if self.session == "":
                print "Faulty packet! Session missing!"
                return False
            elif self.range == "":
                print "Fault packet! Range missing!"
                return False
        else:
            return True

    ##
    # URI Parsering routine   
    ##    
    def parseURI(self):
        #Reverse escapes
        self.URI = urllib.unquote(self.URI) 
        uriSections = urlparse.urlparse(self.URI)

        #urlSections[0] == scheme, [1] == netlocation, [2] == path
        #[1:] to remove prepended /
        self.pathname = uriSections[2][1:]

    def dumpMessage(self):
        #Convert using logging methods
        print self.rtspMsg

    ##
    # Description reply message
    ##
    def createDescriptionReplyMessage(self, cseq, URI, SDP):
        self.createReplyHeader(cseq)
        self.rtspMsg += "Content-Base: "+URI+"\r\n"
        self.rtspMsg += "Content-Type: application/sdp\r\n"
        self.rtspMsg += "Content-Length: "+str(len(SDP))+"\r\n\r\n"
        self.rtspMsg += SDP
        return self.rtspMsg

    ##
    # Setup Reply Message
    ##
    def createSetupReplyMessage(self, cseq, transport, clientport, serverport,session):
        self.createReplyHeader(cseq)
        self.rtspMsg += "Transport: "+transport
        self.rtspMsg += "client_port="+clientport+";"
        self.rtspMsg += "server_port="+serverport+"\r\n"
        self.rtspMsg += "Session: "+session+"\r\n"
        self.rtspMsg += "\r\n"
        return self.rtspMsg

    ##
    # Play reply message
    ##
    def createPlayReplyMessage(self, cseq,URI, session, seq, rtptime):
        self.createReplyHeader(cseq)
        self.rtspMsg += "Session: "+session+"\r\n"
        self.rtspMsg += "RTP-Info: "
        self.rtspMsg += "url="+URI+";"
        self.rtspMsg += "seq="+seq+";"
        self.rtspMsg += "rtptime="+rtptime+"\r\n"
        self.rtspMsg += "\r\n"
        return self.rtspMsg

    ##
    # Pause reply message
    ##
    def createPauseReplyMessage(self, cseq, session):
        self.createReplyHeader(cseq)
        self.rtspMsg += "Session: "+session+"\r\n"
        self.rtspMsg +="\r\n"
        return self.rtspMsg

    ##
    # Options reply message
    ##
    def createOptionsReplyMessage(self, cseq):
        self.createReplyHeader(cseq)
        self.rtspMsg += "Public: "
        for command in commands[1:]:
            self.rtspMsg += command +", "
        self.rtspMsg = self.rtspMsg[0:(len(self.rtspMsg) -2)]
        self.rtspMsg +="\r\n\r\n"
        return self.rtspMsg
    ##
    # Teardown reply message.
    ##
    def createTeardownReplyMessage(self, cseq):
        self.createReplyHeader(cseq)
        self.rtspMsg += "\r\n"
        return self.rtspMsg

    ##
    #  Creates hommor header for all RTSP reply messages
    ##
    def createReplyHeader(self, cseq):
        self.rtspMsg = ""
        self.rtspMsg += self.protocol + " 200 OK\r\n"
        self.rtspMsg += "CSeq: " + cseq +"\r\n"

    ##
    # Faulty message
    ##
    def createFaultyReplyMessage(self):
        return "RTSP/1.0 400 Bad Request\r\n\r\n"
