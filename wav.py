##
# Custom wave module,limited support
##

from struct import * 

class Wave():
    """ Custom wave class """
    def __init__(self,filename): 
        self.information = None       
        self.error = False
        self.filename = filename
        f = open(self.filename,'r')
        data = f.read(12)
        riffchunk = unpack('<4sI4s',data) 
        if riffchunk[0] != "RIFF":
            self.error = True
        elif riffchunk[2] != "WAVE":
            self.error = True
        if self.error is False:
            self.chunksize = riffchunk[1]
            while(True):
                data = f.read(8)
                subchunk = unpack('<4sI',data)  
                if subchunk[0] == "fmt ":
                    data = f.read(subchunk[1])
                    self.information = unpack('<HHIIHHH',data)
                elif subchunk[0] == "data":
                    self.nframes = subchunk[1]
                    break
                else:
                    f.seek(subchunk[1],1)
        f.close()

    def getnframes(self):
        if self.error is False:
            return self.nframes
        else:
            return 0

    def getchannels(self):
        if self.error is False:
            return self.information[1]
        else:
            return 0

    def getsamplerate(self):
        if self.error is False:
            return self.information[2]
        else:
            return 0

    def getbitrate(self):
        if self.error is False:
            return self.information[3]
        else:
            return 0

    def getsamplewidth(self):
        if self.error is False:
            return self.information[5]
        else:
            return 0

    def getdata(self):
        data = None
        if self.error is False:
            f = open(self.filename,'r')
            f.seek(self.chunksize + 8 - self.nframes,1)
            data = f.read()
            f.close()
        return data

    def getDuration(self):
        """" Duration of the wav-file in seconds"""
        frames = getnframes()
        framesInSecond = getsamplerate()
        if framesInSecond != 0:
            return frames/(float)framesInSecond
        else
            return 0

