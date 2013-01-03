from struct import *

# Takes actual data, total data size i.e. total frames, name of file
# Writes file to "Record" folder
def wavwriter(data,size,filename):
    riffheader = pack('<4sI4s', 'RIFF', size + 38, 'WAVE')
    fmtheader = pack('<4sIHHIIHHH','fmt ', 18, 7, 1, 8000, 8000, 1, 8 ,0)
    dataheader = pack('<4sI', 'data',size)
    wavefile = riffheader +fmtheader + dataheader + data
    f = open('Record/'+filename,'w')
    f.write(wavefile)
    f.close()
    
