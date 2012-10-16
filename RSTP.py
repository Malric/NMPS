####
#
# RSTP Message
#
####

import re
import urllib
import urlparse
import logging

class RSTPMessage:

    def __init__(self, message):
        self.rstpCommand = ""
        self.URI         = ""
        self.pathname    = ""
        self.cseq        = ""
        self.bandwith    = ""
        self.bufsize     = ""
        self.session     = ""
        self.speed       = ""
 
        self.rtspMsg = message

        #Regex for different fields

        self.bandwithRegex = re.compile(r'Bandwith: (.*)$', re.IGNORECASE)
        self.cseqRegex = re.compile(r'Cseq: (.*)$', re.IGNORECASE)
        self.sessionRegex = re.compile(r'Session: (.*)$', re.IGNORECASE)
        self.speedRegex = re.compile(r'Speed: (.*)$', re.IGNORECASE)
        self.bufsizeRegex = re.compile(r'BufSize: (.*)$', re.IGNORECASE)

    def tostring(self):
        return self.rstpMsg

    def fromstring(self):
        self.rstpMsg = message

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

        self.rstpCommand = command
        self.URI = uri

    
    def parseURI(self):
        #Parse URI
        

    def dumpMessage(self):
        #Convert using logging methods
        print self.rstpMsg
        
        
