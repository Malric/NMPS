####
#
# Playlist/RTSP server
#
####

import sys
import argparse
import socket
import threading
import select
import re
import os
import errno
import shutil
import RTSP
from song import ServerSong
from ffmpegwrapper import FFmpeg, Input, Output
import eyeD3

songs = []

def listen(PORT):
    """ Create listening socket. """
    HOST = None     # Symbolic name meaning all available interfaces
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC,
                              socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            s = None
            continue
        try:
            s.bind(sa)
            s.listen(5)
        except socket.error as msg:
            s.close()
            s = None
            continue
        break
    return s

def read(socket):
    """ Wrapper function to read from socket untill complete message is obtained or timeouts. """
    data = ""    
    inputs = []
    inputs.append(socket)
    while True:
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[],180.0)    
        except: # possible errors
            pass        
        if inputready is None:#timeout 3 min
            return None
        for ins in inputready:
            data = data + ins.recv(1024)
        if re.search('\\r\\n\\r\\n',data):
            break
    return data

####
#
# Can be tested by putting some MP3 files to "MP3s" directory and connecting to server by e.g. "telnet localhost <PORT>"
# Creates a folder for wav files to be used during runtime of the server
# eyeD3 used for reading MP3 metadata can be downloaded from http://pypi.python.org/pypi/eyeD3-pip/0.6.19
# ffmpegwrapper used for running ffmpeg commands can be downloaded from http://pypi.python.org/pypi/ffmpegwrapper/0.1-dev
#
####

# Creates wav files from MP3s
# Creates ServerSong objects based on wav file paths and corresponding MP3 metadata
# Stores ServerSong objects to "songs" list
def initSongs():
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
# #EXTINF:<time>, <artist> - <title>
# rtsp://ip:port/<wav filename>
# ...
#
def getPlaylist():
    global songs
    playlist = "#EXTM3U\r\n"
    
    for song in songs:
        i = song.path.rfind("/")
        wav_filename = song.path[i+1:]
        print "Adding '" + wav_filename + "' to playlist"
        playlist += "#EXTINF:" + song.length + ", " + song.artist + " - " + song.title + "\r\nrtsp://ip:port/" + wav_filename + "\r\n"
        
    return playlist

class Accept_PL(threading.Thread):
    """ Thread class. Each thread handles playlist request/reply for specific connection. """
    def __init__(self,conn,addr):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        """ Override case class run() function. """
        data = read(self.conn)
        if data is None:
            print "Playlist Server: No data"
        elif data == "GET PLAYLIST\r\nLtunez-Client\r\n\r\n":
            print "Playlist Server: Creating playlist"
            playlist = getPlaylist()
            reply = "Playlist OK\r\nLtunez-Server\r\n" + playlist + "\r\n"
            print "Playlist Sever: Sending playlist"
            conn.sendall(reply)
        else:
            print "Playlist Server: Invalid request from client"
        self.conn.close()

class Accept_RTSP(threading.Thread):
    """ Thread class. Each thread handles RTSP message request/reply for specific connection. """
    def __init__(self,conn,addr):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)        
        self.conn = conn
        self.addr = addr  

    def run(self):  
        """ Override base class run() function. """
        while True:
            data = read(self.conn)
            if data is None:
                print 'Error:'
                self.conn.close()
                break
            p = RTSP.RTSPMessage(data)
            p.parse()
            commands = ["DESCRIBE", "SETUP", "TEARDOWN", "PLAY", "PAUSE"]
            if(p.rtspCommand == "OPTIONS"):
                self.conn.sendall(p.createOptionsReplyMessage(p.cseq))
            elif(p.rtspCommand == "DESCRIBE"):
                self.conn.sendall(p.createDescriptionReplyMessage(p.cseq, p.URI,"application/sdp",str(0),""))
            elif(p.rtspCommand == "SETUP"):
                #configuration to do
                self.conn.sendall(p.createSetupReplyMessage(p.cseq, p.transport, "unicast", p.clientport, "9000-90001"))
            elif(p.rtspCommand == "TEARDOWN"):
                self.conn.sendall(p.createTeardownReplyMessage(p.cseq))
            elif(p.rtspCommand == "PLAY"):
                self.conn.sendall(p.createPlayReplyMessage(p.cseq, p.session, p.URI,"", ""))
            elif(p.rtspCommand == "PAUSE"):
                self.conn.sendall(p.createPauseReplyMessage(p.cseq, p.session))
            else:
                print 'Error: Unknown command'
                self.conn.close()
                break         
            
def rtsp(port):
    """ This function waits for RTSP request and starts new thread. """
    sock = listen(port)
    if sock is None:
        print 'Error: Could not open socket.'
        sys.exit(1)
    print 'RTSP Server: Listening on port '+str(port)
    while True:    
        try:
            conn, addr = sock.accept()
        except KeyboardInterrupt:
            sock.close()
            sys.exit(0)     
        print 'Connected by ', addr
        a = Accept_RTSP(conn,addr)
        a.start()

def playlist(port):
    """ This function waits for playlist request and starts new thread. """
    initSongs()
    sock = listen(port)
    if sock is None:
        print 'Playlist Serevr: Error: Could not open socket.'
        sys.exit(1)
    print 'Playlist Server: Listening on port '+str(port)
    while True:
        try:
            conn,addr = sock.accept()
        except KeyboardInterrupt:
            sock.close()
            sys.exit(0)
            shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # finally remove "Wavs" dir 
        print 'Connected by ', addr
        a = Accept_PL(conn,addr)
        a.start()
   
           
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    args = parser.parse_args()
    pid = os.fork()
    if pid < 0:
        print 'Error: fork()'
        sys.exit(1)  
    elif pid == 0:
        playlist(args.playlist)
        sys.exit(0)          
    rtsp(args.rtsp)

