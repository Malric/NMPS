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
RTP_VERSION = 2
RTP_PAYLOAD = 8

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

#TODO
# Create message creation (timestamp, ssrc, csrc, sequence)
# Check extension bit
# Create RTP Header extension format
# Basic idea is just to concatenate to get the final message.

    
