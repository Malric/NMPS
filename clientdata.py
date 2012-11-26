####
# Client datastructure
####

class client():
	
	def __init__(self,ip, rtp_port, rtcp_port):
		self.ip = ip
		self.rtp_port = rtp_port
		self.rtcp_port = rtcp_port
		self.stream = stream
		self.location = 0
