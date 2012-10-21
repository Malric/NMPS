####
#
# Just initial testing of wav file and playlist generation without any ip or port numbers
# Can be tested by putting some MP3 files to "MP3s" directory
# Creates a folder for wav files to be used during runtime of the server
# eyeD3 used for reading MP3 metadata can be downloaded from http://pypi.python.org/pypi/eyeD3-pip/0.6.19
# ffmpegwrapper used for running ffmpeg commands can be downloaded from http://pypi.python.org/pypi/ffmpegwrapper/0.1-dev
#
####

import os
import errno
import shutil
from song import ServerSong
from ffmpegwrapper import FFmpeg, Input, Output
import eyeD3

songs = []


# Creates wav files from MP3s
# Creates ServerSong objects based on wav file paths and corresponding MP3 metadata
# Stores ServerSong objects to "songs" list
def InitSongs():
    global songs
    
    try:
        os.makedirs(os.getcwd() + "/Wavs") # create "Wavs" dir to current working dir
    except OSError as exception:
        if exception.errno != errno.EEXIST: # ignore error if path exists
            raise    
    
    mp3_filenames = os.listdir("MP3s")
    
    for fname in mp3_filenames:
        mp3_path = "MP3s/" + fname
        wav_path = "Wavs/" + os.path.splitext(fname)[0] + ".wav" # wav filename is the same as mp3 except the extension
        input_mp3 = Input(mp3_path)
        output_wav = Output(wav_path)
        ffmpeg_command = FFmpeg("ffmpeg", input_mp3, output_wav)
        ffmpeg_command.run()
        tag = eyeD3.Tag()
        tag.link(mp3_path)
        song = ServerSong(tag.getArtist(), tag.getTitle(), wav_path)
        songs.append(song)


# Returns playlist string in format:
#
# <artist> - <title>
# rtsp://ip:port/<wav filename>
# ...
#
def GetPlaylist():
    global songs
    playlist = ""
    first = True
    
    for song in songs:
        i = song.path.rfind("/")
        wav_filename = song.path[i+1:]
        print "Adding '" + wav_filename + "' to playlist"
        if not first:
            playlist += "\n"
        first = False
        playlist += song.artist + " - " + song.song + "\nrtsp://ip:port/" + wav_filename
        
    return playlist


#Server actions
def Server():
    InitSongs()
    print "Playlist:\n" + GetPlaylist()
    # TODO: send playlist to the client
    
    # TODO: other server actions
    
    shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # finally remove "Wavs" dir 
    
    
Server()
