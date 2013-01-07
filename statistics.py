
class Statistics:
    
    def __init__(self):
        self.playlists = 0 # number of playlists requested
        self.songs = 0 # number of songs requested
        
    def printStats(self):
        print "Number of playlists requested: " + str(self.playlists)
        print "Number of songs requested: " + str(self.songs)
