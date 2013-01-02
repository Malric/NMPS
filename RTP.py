####
#
# RTP Message
#
###

import ctypes
import time
import sys

c_uint8 = ctypes.c_uint8
c_uint16 = ctypes.c_uint16
c_uint32 = ctypes.c_uint32

#RTP STD Headers:
RTP_Version = 2
RTP_Payload = 8

class rtp_header(ctypes.BigEndianStructure):
    _fields_ = [
        ("Version", c_uint8, 2),
        ("Padding", c_uint8, 1),
        ("Extension", c_uint8, 1),
        ("CSRC_Count", c_uint8, 4),
        ("Marker", c_uint8, 1),
        ("Payload", c_uint8, 7),
        ("Sequence", c_uint16, 16),
        ("Timestamp", c_uint32, 32),
        ("SSRC", c_uint32, 32),
        ("CSRC", c_uint32, 32),
        ]


class RTPMessage(ctypes.BigEndianStructure):
    
    ##
    #   Initialization, requires ssrc
    ##
    def __init__(self, ssrc):
        self.header = rtp_header()
        self.version = 2
        self.padding = 0
        self.extension = 0
        self.csrc_count = 0
        self.marker = 0
        self.payload = 0
        self.sequence = 0
        self.timestamp = 0
        self.ssrc = ssrc
        self.csrc = 0
        
        # Setting up header
        self.updateHeader()
        pass

    ##
    # Helper function for updating headers.
    ##
    def updateHeader(self):
        self.header.Version = self.version
        self.header.Padding = self.padding
        self.header.CSRC_Count = self.csrc_count
        self.header.Marker = self.marker
        self.header.Sequence = self.sequence
        self.header.Timestamp = self.timestamp
        self.header.SSRC = self.ssrc

    def updateFields(self):
        self.version = self.header.Version
        self.padding = self.header.Padding
        self.extension = self.header.Extension
        self.csrc_count = self.header.CSRC_Count
        self.marker = self.header.Marker
        self.payload = self.header.Payload
        self.sequence = self.header.Sequence
        self.timestamp = self.header.Timestamp
        self.ssrc = self.header.SSRC
        self.csrc = self.header.CSRC

    ##
    #   Message creation, returns the packet
    ##
    def createMessage(self, sequence, timestamp, payload):
        self.sequence = sequence
        self.timestamp = timestamp
        self.payload = payload
        self.updateHeader()
        self.printFields()
        return self.header

    ##
    # Sanity-checker
    ##
    def parse(self):

        if self.version != 2:
            print "Faulty packet: wrong version"
            return 0
        if self.payload != 0:
            print "Wrong payload type, Only accepts PCM-U"
            return 0
        if self.extension != 0:
            print "We don't support any extension headers."
            return 0

    ##
    # Start of payload
    ##
    def getOffset(self):
        if self.csrc_count == 0:
            return sys.getsizeof(self.header)
        else:
            return sys.getsizeof(self.header) + self.csrc_count*sys.getsizeof(c_uint32)

    def printFields(self):
        string  ="Version: "+str(self.version) + "\r\n"
        string +="Padding: "+str(self.padding) + "\r\n"
        string +="Extension: "+str(self.extension) + "\r\n"
        string +="CRSC_Count: "+str(self.csrc_count) + "\r\n"
        string +="Marker: "+str(self.marker) + "\r\n"
        string +="Payload: "+str(self.payload) + "\r\n"
        string +="Sequence: "+str(self.sequence) + "\r\n"
        string +="Timestamp: "+str(self.timestamp) + "\r\n"
        string +="SSRC: "+str(self.ssrc) + "\r\n"
        string +="CSRC: "+str(self.csrc) + "\r\n"
        print string

    def printHeader(self):
        string  ="Version: "+str(self.header.Version) + "\r\n"
        string +="Padding: "+str(self.header.Padding) + "\r\n"
        string +="Extension: "+str(self.header.Extension) + "\r\n"
        string +="CRSC_Count: "+str(self.header.CSRC_Count) + "\r\n"
        string +="Marker: "+str(self.header.Marker) + "\r\n"
        string +="Payload: "+str(self.header.Payload) + "\r\n"
        string +="Sequence: "+str(self.header.Sequence) + "\r\n"
        string +="Timestamp: "+str(self.header.Timestamp) + "\r\n"
        string +="SSRC: "+str(self.header.SSRC) + "\r\n"
        string +="CSRC: "+str(self.header.CSRC) + "\r\n"
        print string
#TODO
# Create message creation (timestamp, ssrc, csrc, sequence)
# Check extension bit
# Create RTP Header extension format
# Basic idea is just to concatenate to get the final message.

    
