###
#
# SIP message
#
###

import re

commands = ["INVITE", "ACK", "BYE", "OPTIONS"]
terminator = "\r\n"

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
        self.client_ip =""
        self.userId = ""
        self.callerId = ""

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
        """ Parses SIP Messages"""
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
                self.client_ip = self.via.split(";",3)[0].split(" ",2)[1].split(":",2)[0]
            hits = self.fromRegex.search(line)
            if hits is not None:
                self.fr = hits.group(1)
                self.callerId = self.fr.split("@",2)[0].split(":",2)[1]
            hits = self.toRegex.search(line)
            if hits is not None:
                self.to = hits.group(1)
                self.userId = self.to.split("@",2)[0].split(":",2)[1]
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
        
    
    def createInviteReplyMessage(self, SDPMsg, client_ip, server_ip, sip_port):
        self.SIPMsg = ""
        self.SIPMsg += self.protocol + " 200 OK"+terminator
        temp = self.via.split(";", 3)
        temp2 = self.fr.split(";",2)
        self.SIPMsg += "Via: " + temp[0] + ";rport=" + temp[0].split(":", 2)[1] + ";" + temp[2] + terminator
        self.SIPMsg += "From: " + temp2[0]+";"+temp2[1] + terminator
        self.SIPMsg += "To: " + self.to +terminator #+ ";tag=a6c85cf" + "\r\n
        self.SIPMsg += "Call-ID: " + self.callID + terminator
        self.SIPMsg += "CSeq: " + self.cSeq + terminator
        self.SIPMsg += "Contact: <sip:mbox-owner@"+server_ip+":"+str(sip_port)+">"+terminator
        self.SIPMsg += "Content-Type: application/sdp"+terminator
        self.SIPMsg += "User-Agent: MBox SIP Server 0.1"+terminator
        self.SIPMsg += "Subject: "+self.subject+terminator
        self.SIPMsg += "Content-Length: " + str(len(SDPMsg)) + terminator+terminator
        self.SIPMsg += SDPMsg
        self.SIPMsg += terminator
        return self.SIPMsg
    
    def createOptionsReplyMessage(self, SDPMsg, client_ip, server_ip, sip_port):
        self.SIPMsg = ""
        self.SIPMsg += self.protocol +" 200 OK"+terminator
        temp = self.via.split(";", 3)
        temp2 = self.fr.split(";",2)
        self.SIPMsg += "Via: " + temp[0] + ";rport=" + temp[0].split(":", 2)[1] + ";" + temp[2] + terminator
        self.SIPMsg += "From: " + temp2[0]+";"+temp2[1] + terminator
        self.SIPMsg += "To: " + self.to +terminator #+ ";tag=a6c85cf" + "\r\n
        self.SIPMsg += "Call-ID: " + self.callID + terminator
        self.SIPMsg += "CSeq: " + self.cSeq + terminator
        self.SIPMsg += "Contact: <sip:mbox-owner@"+server_ip+":"+str(sip_port)+">"+terminator
        self.SIPMsg += "Allow: "
        for i in range(len(commands)):
            self.SIPMsg += commands[i]
            if i!=len(commands)-1:
                self.SIPMsg +=", "
        self.SIPMsg +=terminator
        self.SIPMsg += "Content-Type: application/sdp"+terminator
        self.SIPMsg += "Content-Length: " + str(len(SDPMsg)) + terminator+terminator
        self.SIPMsg += SDPMsg
        self.SIPMsg += terminator
        return self.SIPMsg
    
    def createByeReplyMessage(self,server_ip, sip_port):
        self.SIPMsg = ""
        self.SIPMsg += self.protocol + " 200 OK"+terminator
        temp = self.via.split(";", 3)
        self.SIPMsg += "Via: " + temp[0] + ";rport=" + temp[0].split(":", 2)[1] + ";" + temp[2] + terminator
        self.SIPMsg += "From: " + self.fr + "\r\nTo: " + self.to + ";tag=a6c85cf" + "\r\nCall-ID: " + self.callID + "\r\nCSeq: " + self.cSeq + terminator
        self.SIPMsg += "Contact: <sip:mbox-owner@"+server_ip+":"+str(sip_port)+">"+terminator
        self.SIPMsg += "Content-Type: application/sdp"+terminator
        self.SIPMsg += "User-Agent: MBox SIP Server 0.1"+terminator
        self.SIPMsg += "Content-Length: 0"+terminator+terminator
        return self.SIPMsg
    
    
        
            