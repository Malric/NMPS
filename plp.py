####
# PlaylistProtocol
####

import re
#import logging

#SCP Commands (Supported)
commands = ["GET PLAYLIST", "Playlist OK", "Playlist Failure"]
terminator = "\r\n"

class PLPMessage:

    def __init__(self):
        self.protocol       = "PLP/1.0"
        self.program        = ""
        self.command 	 	= ""
        self.message        = ""
        self.userid         = ""
        self.playlist       = ""

        #REGEX
        self.ipRegex = re.compile(r'ip: (.*)$', re.IGNORECASE)
        self.rtpRegex = re.compile(r'rtp: (.*)$', re.IGNORECASE)
        self.rtcpRegex = re.compile(r'rtcp: (.*)$', re.IGNORECASE)
        self.sequenceRegex = re.compile(r'sequence: (.*)$', re.IGNORECASE)
        self.rtptimeRegex = re.compile(r'rtptime: (.*)$', re.IGNORECASE)

    def createLTunezClientRequest(self):
        self.program = "LTunez-Client"
        self.command = "GET PLAYLIST"
        self.message = self.command +terminator
        self.message += self.program +terminator+terminator
        return self.message

    def createMBoxClientRequest(self, userid):
        self.program = "MBox-Client"
        self.command = "GET PLAYLIST"
        self.userid = userid
        self.message = self.command +terminator
        self.message += self.program +terminator
        self.message += self.userid +terminator+terminator
        return self.message

    def createServerOkResponse(self, server, playlist):
        self.command = "Playlist OK"
        self.program = server+"-Server"
        self.playlist = playlist
        self.message = self.command +terminator
        self.message += self.program +terminator
        self.message += self.playlist +terminator
        return self.message

    def createServerFailureResponse(self, server):
        self.command = "Playlist Failure"
        self.program = server+"-Server"
        self.message = self.command +terminator
        self.message += self.program +terminator+terminator
        return self.message

    def parse(self,message):
        self.message = message
        self.playlist = ""

        lines = self.message.split('\r\n')
        if len(lines) <2:
            return False
        self.command = lines[0]

        if self.command not in commands:
            return False
        self.program = lines[1]
        if self.command == "GET PLAYLIST":
            if self.program == "MBox-Client":
                self.userid = lines[2]
        elif self.command == "Playlist OK":
            for line in lines[2:len(lines) - 1]:
                if line == "":
                    break
                else:
                    self.playlist += line +terminator