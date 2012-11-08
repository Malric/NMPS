####
# Playlist/RTSP server
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
import sdp
from song import ServerSong
from ffmpegwrapper import FFmpeg, Input, Output, AudioCodec, options
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
            print 'RTSP Server: '+str(msg)
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print 'RTSP Server: '+str(msg)
            s.close()
            s = None
            continue
        try:
            s.listen(5)
        except socket.error as msg:
            print 'RTSP Server: '+str(msg)
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
        except select.error as msg:
            print 'RTSP Server: '+str(msg)
        if inputready is None:
            print 'RTSP Server: timeout 3 min'
            return None
        for ins in inputready:
            try:
                temp = ins.recv(1024)
                if temp is None:
                    raise IOError(errno.ECONNRESET,os.strerr(errno.ECONNRESET))
            except IOError as msg:                
                print 'RTSP Server: '+str(msg)    
                return None
            data += temp
        if re.search('\\r\\n\\r\\n',data):
            break
    return data

def initSongs():
    """ This function creates wav files from MP3s and ServerSong objects into 'songs' list. """
    global songs
    
    try:
        os.makedirs(os.getcwd() + "/Wavs") # create "Wavs" dir to current working dir
    except OSError as exception:
        if exception.errno != errno.EEXIST: # ignore error if path exists
            raise
    
    mp3_filenames = os.listdir("MP3s")
    
    for mp3_filename in mp3_filenames:
        mp3_path = "MP3s/" + mp3_filename
        wav_filename = os.path.splitext(mp3_filename)[0] + ".wav" # wav filename is the same as mp3 except the extension
        wav_path = "Wavs/" + wav_filename
        
        # construct and run ffmpeg command
        input_mp3 = Input(mp3_path)
        output_wav = Output(wav_path, AudioCodec("pcm_mulaw"))
        opt_dict = dict([("-ar", "8000"), ("-ac", "1"), ("-ab", "64000")]) # sampling rate 8000 Hz, 1 audio channel (mono), bitrate 64kbits/s
        opt = options.Option(opt_dict)
        ffmpeg_command = FFmpeg("ffmpeg", input_mp3, opt, output_wav)
        ffmpeg_command.run()
        print "Playlist Server: File created: '" + wav_filename + "'"
        
        mp3header = eyeD3.Mp3AudioFile(mp3_path)
        length = str(mp3header.getPlayTime())
        tag = eyeD3.Tag()
        tag.link(mp3_path)
        song = ServerSong(length, tag.getArtist(), tag.getTitle(), wav_path)
        songs.append(song)

def getPlaylist():
    """ This function returns a playlist string in M3U format. """
    global songs
    playlist = "#EXTM3U\r\n"
    
    for song in songs:
        i = song.path.rfind("/")
        wav_filename = song.path[i+1:]
        print "Playlist Server: Adding '" + wav_filename + "' to playlist"
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
        """ Override base class run() function. """
        data = read(self.conn)
        if data is None:
            print "Playlist Server: No data"
        elif data == "GET PLAYLIST\r\nLtunez-Client\r\n\r\n":
            print "Playlist Server: Creating playlist"
            playlist = getPlaylist()
            reply = "Playlist OK\r\nLtunez-Server\r\n" + playlist + "\r\n"
            print "Playlist Server: Sending playlist"
            self.conn.sendall(reply)
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
                self.conn.close()
                break
            p = RTSP.RTSPMessage(data)
            if p.parse() is False:
                self.conn.close()
                break
            p.dumpMessage() # Remove,debug
            if(p.rtspCommand == "OPTIONS"):
                self.conn.sendall(p.createOptionsReplyMessage(p.cseq))
                p.dumpMessage() # Remove,debug
            elif(p.rtspCommand == "DESCRIBE"):
                s = sdp.SDPMessage("Test","23544",7000)
                self.conn.sendall(p.createDescriptionReplyMessage(p.cseq, p.URI,s.getMessage()))
                p.dumpMessage() # Remove,debug
            elif(p.rtspCommand == "SETUP"):
                self.conn.sendall(p.createSetupReplyMessage(p.cseq, p.transport, p.clientport, "9000-90001",458959))
                p.dumpMessage() # Remove,debug
            elif(p.rtspCommand == "TEARDOWN"):
                self.conn.sendall(p.createTeardownReplyMessage(p.cseq))
                p.dumpMessage() # Remove,debug
                self.conn.close()
                break
            elif(p.rtspCommand == "PLAY"):
                self.conn.sendall(p.createPlayReplyMessage(p.cseq, p.session, p.URI,"", ""))
                p.dumpMessage() # Remove,debug
            elif(p.rtspCommand == "PAUSE"):
                self.conn.sendall(p.createPauseReplyMessage(p.cseq, p.session))
                p.dumpMessage() # Remove,debug
            else:
                print 'Error: RTSP Server,Unknown command'  # create faulty reply
                self.conn.close()
                break         
            
def rtsp(port):
    """ This function waits for RTSP request and starts new thread. """
    sock = listen(port)
    if sock is None:
        sys.exit(1)
    print 'RTSP Server: Listening on port '+str(port)
    while True:    
        try:
            conn, addr = sock.accept()
        except KeyboardInterrupt:
            sock.close()
            sys.exit(0)     
        except socket.error as msg:
            print 'RTSP Server: '+str(msg)
            continue
        print 'RTSP Server: Connected by ', addr
        a = Accept_RTSP(conn,addr)
        a.start()

def playlist(port):
    """ This function waits for playlist request and starts new thread. """
    initSongs()
    sock = listen(port)
    if sock is None:
        print "Playlist Server: Error: Could not open socket."
        sys.exit(1)
    print "Playlist Server: Listening on port "+str(port)
    while True:
        try:
            conn,addr = sock.accept()
        except KeyboardInterrupt:
            sock.close()
            print "Playlist Server: Deleting 'Wavs' directory..."
            shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # remove "Wavs" dir
            print "Playlist Server: Exiting..."
            sys.exit(0)
        print "Playlist Server: Connected by ", addr
        a = Accept_PL(conn,addr)
        a.start()
     
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    args = parser.parse_args()       
    pid = os.fork()
    if pid < 0:
        print "Error: fork()"
        sys.exit(1)  
    elif pid == 0:
        playlist(args.playlist)
        sys.exit(0)   
    rtsp(args.rtsp)

