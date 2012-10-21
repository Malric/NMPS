####
#
# Song classes for client and server
#
####

class ClientSong:

    def __init__(self, artist, song, uri):
        self.artist = artist
        self.song   = song
        self.URI    = uri

class ServerSong:

    def __init__(self, artist, song, path):
        self.artist = artist
        self.song = song
        self.path = path


