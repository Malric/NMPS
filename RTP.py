####
#
# RTP Message
#
###

import ctypes
import time

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
        ("CSRC", c_uint8, 4),
        ("Marker", c_uint8, 1),
        ("Payload", c_uint8, 7),
        ("Sequence", c_uint16, 16),
        ("Timestamp" c_uint32, 32),
        ("SSRC", c_uint32, 32),
        ("CSRC", c_uint32, 32),
        ]


class RTPMessage(ctypes.BigEndianStructure):
    
    def __init__(self):
        self.header = None
        self.version = 2
        self.padding = None
        self.extension = None
        self.csrc = None
        self.marker = None
        self.payload = None
        self.sequence = None
        self.timestamp = None
        self.ssrc = None
        self.csrc = None
        pass

    def parse(self, bytestring):
        print "Received RTP"

        if bytestring == 0:
            print "Faulty message"
            break
        msg.readinto(self.header)
        self.version = self.header.Version
        self.padding = self.header.Padding
        self.extension = self.header.Extension
        self.csrc = self.header.CSRC
        self.marker = self.header.Marker
        self.payload = self.header.Payload
        self.sequence = self.header.Sequence
        self.timestamp = self.header.Timestamp
        self.ssrc = self.header.SSRC
        self.csrc = self.header.CSRC

        if self.version != 2:
            print "Faulty packet: wrong version"
            break
        
        
        
    
#TODO
# Create message creation (timestamp, ssrc, csrc, sequence)
# Check extension bit
# Create RTP Header extension format
# Basic idea is just to concatenate to get the final message.

    
