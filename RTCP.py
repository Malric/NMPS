import ctypes
import time
c_uint8 = ctypes.c_uint8
c_uint16 = ctypes.c_uint16
c_uint32 = ctypes.c_uint32

#RTCP Message Types

RTCP_PT_SR   = 200
RTCP_PT_RR   = 201
RTCP_PT_SDES = 202
RTCP_PT_BYE  = 203
RTCP_PT_APP  = 204

rtcpPTdict = {RTCP_PT_SR:  'SR',
              RTCP_PT_RR:  'RR',
              RTCP_PT_SDES:'SDES',
              RTCP_PT_BYE: 'BYE',
              RTCP_PT_APP: 'APP'}

#RTCP STD headers:
RTCP_Version = 2

class rtcp_header(ctypes.BigEndianStructure):
    _fields_ = [
        ("Version", c_uint8, 2),
        ("Padding", c_uint8, 1),
        ("Count", c_uint8, 5),
        ("Type", c_uint8, 8),
        ("Length", c_uint16, 16),
        ]

##
# RCTP Message protocol
##

class RtcpMessage:
    
    def __init__(self):
        self.messageType = None
        self.header = rtcp_header()
        self.version = None
        self.padding = None
        self.count = None
        self.length = None
        pass

    def parse(self, msg):
        print "Recieved RTCP"

        self.header = rtcp_header()
        if msg == 0:
            print "Faulty message"
            break
        msg.readinto(self.header)
        self.version = self.header.Version
        self.padding = self.header.Padding
        self.count = self.header.Count
        self.type = self.header.Type
        self.length = hdr.Length
        
        if self.version != 2:
            print "Faulty packet: wrong version"
            break
        elif self.type not in rtcpPSDict:
            print "Unknown type: self.type"
            break
        elif self.length == 0 && padding == 0:
            print "Faulty packet: "
            break
        
    
        # SANITY CHECK!
