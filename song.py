####
#
# Artist, Song, Url, path classes
#
####

class clientSong:

    def __init__(self, artist, song, uri):
        self.artist = artist
        self.song   = song
        self.URI    = uri

class serverSong:

    def __init__(self, artist, song, path):
        self.artist = artist
        self.song = song
        self.path = path


