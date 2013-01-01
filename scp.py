####
# StreamerControlProtocol
####

import re
#import logging

#SCP Commands (Supported)
commands = ["SETUP", "TEARDOWN", "PLAY", "PAUSE", "PORTS", "RUNNING"]
terminator = "\r\n"

class SCPMessage:

    def __init__(self):
        self.command 	 	= ""
        self.protocol 		= "SCP/1.0"
        self.clientIp		= ""
        self.clientRtpPort	= ""
        self.clientRtcpPort = ""
        self.sequence = ""
        self.rtptime = ""
        self.message = ""

        #REGEX
        self.ipRegex = re.compile(r'ip: (.*)$', re.IGNORECASE)
        self.rtpRegex = re.compile(r'rtp: (.*)$', re.IGNORECASE)
        self.rtcpRegex = re.compile(r'rtcp: (.*)$', re.IGNORECASE)
        self.sequenceRegex = re.compile(r'sequence: (.*)$', re.IGNORECASE)
        self.rtptimeRegex = re.compile(r'rtptime: (.*)$', re.IGNORECASE)

    def createPlay(self, ip):
        """ Control message to start streaming. """
        self.command = "PLAY"
        self.clientIp = ip
        self.message = self.command + " "+self.protocol+terminator
        self.message += "ip: "+self.clientIp+terminator+terminator
        return self.message

    def createPause(self, ip):
        """ Control message to pause streaming. """
        self.command = "PAUSE"
        self.clientIp = ip
        self.message = self.command + " "+self.protocol+terminator
        self.message += "ip: "+self.clientIp+terminator+terminator
        return self.message

    def createTeardown(self, ip):
        """ Control message to teardown connection to certain client. """
        self.command = "TEARDOWN"
        self.clientIp = ip
        self.message = self.command + " "+self.protocol+terminator
        self.message += "ip: "+self.clientIp+terminator+terminator
        return self.message

    def createSetup(self, ip, rtpPort, rtcpPort):
        """ Control message to setup the streamer. """
        self.command = "SETUP"
        self.clientIp = ip
        self.clientRtpPort = rtpPort
        self.clientRtcpPort = rtcpPort
        self.message = self.command + " "+self.protocol+terminator
        self.message += "ip: "+self.clientIp+terminator
        self.message += "rtp: "+self.clientRtpPort+terminator
        self.message += "rtcp: "+self.clientRtcpPort+terminator+terminator
        return self.message

    def createPort(self, rtpPort, rtcpPort):
        self.command = "PORTS"
        self.clientRtpPort = rtpPort
        self.clientRtcpPort = rtcpPort
        self.message = self.command + " "+self.protocol+terminator
        self.message += "rtp: "+self.clientRtpPort+terminator
        self.message += "rtcp: "+self.clientRtcpPort+terminator+terminator
        return self.message
    
    def createRunning(self, sequence, rtptime):
        self.command  = "RUNNING"
        self.sequence = sequence
        self.rtptime  = rtptime
        self.message = self.command + " "+self.protocol+terminator
        self.message += "sequence: "+self.sequence+terminator
        self.message += "rtptime: "+self.rtptime+terminator+terminator
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
            hits = self.sequenceRegex.search(line)
            if hits is not None:
                self.sequence = hits.group(1)
            hits = self.rtptimeRegex.search(line)
            if hits is not None:
                self.rtptime = hits.group(1)
               

