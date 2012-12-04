###
#
# SIP message
#
###

import re

commands = ["INVITE", "ACK", "BYE"]


class SIPMessage:


    def __init__(self, message):
        self.SIPCommand = ""
        self.requestURI = ""
        self.protocol = "SIP/2.0"
        self.via = ""
        self.fr = ""
        self.to = ""
        self.callID = ""
        self.cSeq = ""
        self.contact = ""
        self.contentType = ""
        self.allow = "" # optional
        self.maxForwards = "" # optional
        self.userAgent = "" # optional
        self.subject = "" # optional
        self.contentLen = ""
        
        if message is not None:
            self.SIPMsg = message
        else:
            self.SIPMsg = ""
            
        self.viaRegex = re.compile(r"Via: (.*)$", re.IGNORECASE)
        self.fromRegex = re.compile(r"From: (.*)$", re.IGNORECASE)
        self.toRegex = re.compile(r"To: (.*)$", re.IGNORECASE)
        self.callIDRegex = re.compile(r"Call-ID: (.*)$", re.IGNORECASE)
        self.cSeqRegex = re.compile(r"CSeq: (.*)$", re.IGNORECASE)
        self.contactRegex = re.compile(r"Contact: (.*)$", re.IGNORECASE)
        self.contentTypeRegex = re.compile(r"Content-Type: (.*)$", re.IGNORECASE)
        self.allowRegex = re.compile(r"Allow: (.*)$", re.IGNORECASE)
        self.maxForwardsRegex = re.compile(r"Max-Forwards: (.*)$", re.IGNORECASE)
        self.userAgentRegex = re.compile(r"User-Agent: (.*)$", re.IGNORECASE)
        self.subjectRegex = re.compile(r"Subject: (.*)$", re.IGNORECASE)
        self.contentLenRegex = re.compile(r"Content-Length: (.*)$", re.IGNORECASE)

          
    def parse(self):
        lines = self.SIPMsg.split("\r\n")
        
        try:
            command, URI, protocol = lines[0].split()
        except ValueError:
            return False
        
        if protocol != self.protocol:
            print "Unsupported protocol: " + protocol
            return False
        
        if command not in commands:
            print "Unsupported command: " + command
            return False
        
        self.SIPCommand = command
        self.requestURI = URI
        
        for line in lines:
            hits = self.viaRegex.search(line)
            if hits is not None:
                self.via = hits.group(1)
            hits = self.fromRegex.search(line)
            if hits is not None:
                self.fr = hits.group(1)
            hits = self.toRegex.search(line)
            if hits is not None:
                self.to = hits.group(1)
            hits  = self.callIDRegex.search(line)
            if hits is not None:
                self.callID = hits.group(1)
            hits = self.cSeqRegex.search(line)
            if hits is not None:
                self.cSeq = hits.group(1)
            hits = self.contactRegex.search(line)
            if hits is not None:
                self.contact = hits.group(1)
            hits = self.contentTypeRegex.search(line)
            if hits is not None:
                self.contentType = hits.group(1)
            hits = self.allowRegex.search(line)
            if hits is not None:
                self.allow = hits.group(1)
            hits = self.maxForwardsRegex.search(line)
            if hits is not None:
                self.maxForwards = hits.group(1)
            hits = self.userAgentRegex.search(line)
            if hits is not None:
                self.userAgent = hits.group(1)
            hits = self.subjectRegex.search(line)
            if hits is not None:
                self.subject = hits.group(1)
            hits = self.contentLenRegex.search(line)
            if hits is not None:
                self.contentLen = hits.group(1)
                
        return True
        
    
    def createInviteReplyMessage(self, SDPMsg):
        self.SIPMsg = ""
        self.SIPMsg += self.protocol + " 200 OK\r\n"
        temp = self.via.split(";", 3)
        self.SIPMsg += "Via: " + temp[0] + ";rport=" + temp[0].split(":", 2)[1] + ";" + temp[2] + "\r\n"
        self.SIPMsg += "From: " + self.fr + "\r\nTo: " + self.to + ";tag=a6c85cf" + "\r\nCall-ID: " + self.callID + "\r\nCSeq: " + self.cSeq + "\r\n"
        self.SIPMsg += "Contact: <sip:mbox-owner@127.0.0.1:6000>\r\n"
        self.SIPMsg += "Content-Type: application/sdp\r\n"
        self.SIPMsg += "User-Agent: MBox SIP Server 0.1\r\n"
        self.SIPMsg += "Content-Length: " + str(len(SDPMsg)) + "\r\n\r\n"
        self.SIPMsg += SDPMsg
        self.SIPMsg += "\r\n"
        return self.SIPMsg
    
    
    def createByeReplyMessage(self):
        self.SIPMsg = ""
        self.SIPMsg += self.protocol + " 200 OK\r\n"
        temp = self.via.split(";", 3)
        self.SIPMsg += "Via: " + temp[0] + ";rport=" + temp[0].split(":", 2)[1] + ";" + temp[2] + "\r\n"
        self.SIPMsg += "From: " + self.fr + "\r\nTo: " + self.to + ";tag=a6c85cf" + "\r\nCall-ID: " + self.callID + "\r\nCSeq: " + self.cSeq + "\r\n"
        self.SIPMsg += "Contact: <sip:mbox-owner@127.0.0.1:6000>\r\n"
        self.SIPMsg += "Content-Type: application/sdp\r\n"
        self.SIPMsg += "User-Agent: MBox SIP Server 0.1\r\n"
        self.SIPMsg += "Content-Length: 0\r\n\r\n"
        return self.SIPMsg
    
    
        
            