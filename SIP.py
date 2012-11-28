###
#
# SIP message
#
###

import re

commands = ["INVITE", "BYE"]

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
        self.userAgentRegex = re.compile("User-Agent: (.*)$", re.IGNORECASE)
        self.subjectRegex = re.compile(r"Subject: (.*)$", re.IGNORECASE)
        self.contentLenRegex = re.compile("Content-Length: (.*)$", re.IGNORECASE)
            
    def parse(self):
        lines = self.SIPMsg.split("\r\n")
        
        try:
            command, URI, protocol = lines[0].split()
        except ValueError:
            return False
        
        if protocol != self.protocol or command not in commands:
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
            hits = self.SubjectRegex.search(line)
            if hits is not None:
                self.subject = hits.group(1)
            hits = self.contentLenRegex.search(line)
            if hits is not None:
                self.contentLen = hits.group(1)
        
        
            