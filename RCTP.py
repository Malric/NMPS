import struct
import time

#RCTP Message Types

RTCP_PT_SR   = 200
RTCP_PT_RR   = 201
RTCP_PT_SDES = 202
RTCP_PT_BYE  = 203
RTCP_PT_APP  = 204

rtcpPTdict = {RTCP_PT_SR:  'SR',
              RTCP_PT_RR:  'RR',
              RTCP_PT_SDES:'SDES',
              RTCP_PT_BYE: 'BYE',
              RCTP_PT_APP: 'APP'}

rctp_header_format ="!"+"BBS" #Version, messagetype, length
rctp_header_format +="!"+"L" #SSRC

##
# RCTP Message protocol

class RctpMessage:

    def __init__(self):
        self.messageType = None
        pass

    def parse(self, bytestring):
        self.ver, self.msg_type, self.length, self.ssrc =\
            struct.unpack(rctp_header_format, bytestring[0:63])
    
