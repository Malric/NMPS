##
#
# NTP Calculation
#
##

from datetime import datetime
import math

def timestamp():
	timestamp = (datetime.utcnow() - datetime(1900,1,1)).total_seconds()
	return str(math.trunc(timestamp))