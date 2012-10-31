####
#
# Can be tested by putting some MP3 files to "MP3s" directory and connecting to server by e.g. "telnet localhost <PORT>"
# Creates a folder for wav files to be used during runtime of the server
# eyeD3 used for reading MP3 metadata can be downloaded from http://pypi.python.org/pypi/eyeD3-pip/0.6.19
# ffmpegwrapper used for running ffmpeg commands can be downloaded from http://pypi.python.org/pypi/ffmpegwrapper/0.1-dev
#
####

import socket
import sys
import os
import errno
import shutil
from thread import start_new_thread
from song import ServerSong
from ffmpegwrapper import FFmpeg, Input, Output
import eyeD3

songs = []
HOST = ''
PORT = 8888


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
        mp3header = eyeD3.Mp3AudioFile(mp3_path)
        length = str(mp3header.getPlayTime())
        song = ServerSong(length, tag.getArtist(), tag.getTitle(), wav_path)
        songs.append(song)


# Returns playlist string in format:
#
# #EXTM3U
# #EXTINF:<length in sec>, <artist> - <title>
# rtsp://ip:port/<wav filename>
# ...
#
def GetPlaylist():
    global songs
    playlist = "#EXTM3U\n"
    
    for song in songs:
        i = song.path.rfind("/")
        wav_filename = song.path[i+1:]
        print "Adding '" + wav_filename + "' to playlist"
        playlist += "#EXTINF:" + song.length + ", " + song.artist + " - " + song.title + "\nrtsp://ip:port/" + wav_filename + "\n"
        
    return playlist


#Thread for client
def ClientThread(conn):
    conn.send("Welcome to the lTunez Server!\n")
    
    while True:
        data = conn.recv(1024)
        if not data:
            print "No data"
            break
        elif data == "GET PLAYLIST\r\n":
            print "Creating playlist"
            playlist = GetPlaylist()
            reply = "Playlist OK\nLtunez-Server\n" + playlist
            print "Sending playlist"
            conn.sendall(reply)
        else:
            print "Invalid request"
            
    
    conn.close()


#Server actions
def Server():
    InitSongs()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "Socket created"
    
    try:
        s.bind((HOST, PORT))
    except socket.error, msg:
        print "Bind failed. Error Code: " + str(msg[0]) + " Message: " + msg[1]
        sys.exit()
    print "Socket bind complete"
    
    s.listen(10)
    print "Socket now listening"
    
    while 1:
        try:
            conn, addr = s.accept()
            print "Connected with " + addr[0] + ":" + str(addr[1])
            start_new_thread(ClientThread, (conn,))
            # TODO: other server actions
        except KeyboardInterrupt:
            print "\nServer closing..."
            break
    
    s.close()
    
    shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # finally remove "Wavs" dir 

    
#Run the server    
Server()
