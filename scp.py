####
# StreamerControlProtocol
####

import re
#import logging

#RTSP Commands (Supported)
commands = ["SETUP", "TEARDOWN", "PLAY", "PAUSE", "PORTS"]
terminator = "\r\n\r\n"

class SCPMessage:

    def __init__(self):
        self.command 	 	= ""
        self.protocol 		= "SCP/1.0"
        self.clientIp		= ""
        self.clientRtpPort	= ""
        self.clientRtcpPort = ""
        self.message = ""

        #REGEX
        self.ipRegex = re.compile(r'ip: (.*)$', re.IGNORECASE)
        self.rtpRegex = re.compile(r'rtp: (.*)$', re.IGNORECASE)
        self.rtcpRegex = re.compile(r'rtcp: (.*)$', re.IGNORECASE)

    def createPlay(self, ip, UNUSED3, UNUSED4):
        self.command = "PLAY"
        self.clientIp = ip
        self.message = self.command + " "+self.protocol+"\r\n"
        self.message += "ip: "+self.clientIp+terminator
        return self.message

    def createPause(self, ip, UNUSED3, UNUSED4):
        self.command = "PAUSE"
        self.clientIp = ip
        self.message = self.command + " "+self.protocol+"\r\n"
        self.message += "ip: "+self.clientIp+terminator
        return self.message

    def createTeardown(self, ip, UNUSED3, UNUSED4):
        self.command = "TEARDOWN"
        self.clientIp = ip
        self.message = self.command + " "+self.protocol+"\r\n"
        self.message += "ip: "+self.clientIp+terminator
        return self.message

    def createSetup(self, ip, rtpPort, rtcpPort):
        self.command = "SETUP"
        self.clientIp = ip
        self.clientRtpPort = rtpPort
        self.clientRtcpPort = rtcpPort
        self.message = self.command + " "+self.protocol+"\r\n"
        self.message += "ip: "+self.clientIp+"\r\n"
        self.message += "rtp: "+self.clientRtpPort+"\r\n"
        self.message += "rtcp: "+self.clientRtcpPort+terminator
        return self.message

    def createPort(self, UNUSED2, rtpPort, rtcpPort):
        self.command = "PORTS"
        self.clientRtpPort = rtpPort
        self.clientRtcpPort = rtcpPort
        self.message = self.command + " "+self.protocol+"\r\n"
        self.message += "rtp: "+self.clientRtpPort+"\r\n"
        self.message += "rtcp: "+self.clientRtcpPort+terminator
        return self.message
    
    def parse(self,message):
        self.message = message

        lines = self.message.split('\r\n')
                   
        #Line 1: Command, Protocol
        try:
            (command, protocol) = lines[0].split()
        except ValueError:
            return False

        if protocol != self.protocol:
            return False

        if command not in commands:
            return False

        self.command = command

        for line in lines:
            hits = self.ipRegex.search(line)
            if hits is not None:
                self.clientIp = hits.group(1)
            hits = self.rtpRegex.search(line)
            if hits is not None:
                self.clientRtpPort = hits.group(1)
            hits = self.rtcpRegex.search(line)
            if hits is not None:
                self.clientRtcpPort = hits.group(1)
               

