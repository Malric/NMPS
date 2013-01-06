from struct import *
import os

# Takes actual data, total data size i.e. total frames, name of file
# Writes file to "Record" folder
def wavwriter(data, size, filename, folder):
    riffheader = pack('<4sI4s', 'RIFF', size + 38, 'WAVE')
    fmtheader = pack('<4sIHHIIHHH','fmt ', 18, 7, 1, 8000, 8000, 1, 8 ,0)
    dataheader = pack('<4sI', 'data',size)
    wavefile = riffheader +fmtheader + dataheader + data
    if os.path.isdir("Records") is False:
    	os.mkdir("Records")
    if os.path.isdir("Records/"+folder) is False:
    	os.mkdir("Records/"+folder)
    f = open("Records/"+folder+"/"+filename,'w')
    f.write(wavefile)
    f.close()
