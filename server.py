####
#
# Just initial testing of playlist (string) message generation without any ip or port numbers
# Can be tested by putting some MP3 files to "MP3s" directory
# eyeD3 used for reading MP3 metadata can be downloaded from http://pypi.python.org/pypi/eyeD3-pip/0.6.19
#
# playlist message format:
#
# <artist> - <title>
# rtsp://ip:port/filename.wav
# ...
#
####

import os
import eyeD3

def GetPlaylist():
    mp3filenames = os.listdir("MP3s")
    playlist = ""
    
    for fname in mp3filenames:
        tag = eyeD3.Tag()
        tag.link("MP3s/" + fname)
        wavfname = os.path.splitext(fname)[0] + ".wav" # wav filename is the same as mp3 except the extension
        playlist += tag.getArtist() + " - " + tag.getTitle() + "\nrtsp://ip:port/" + wavfname + "\n"
        
    return playlist

def Server():
    print GetPlaylist() # TODO: send this string (playlist) to the client
    
Server()

    
    
