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

class listen():
    """ Create listening socket, compatible with 'with' method """
    def __init__(self,PORT):
        self.PORT = PORT    
    def __enter__(self):
        HOST = None     # Symbolic name meaning all available interfaces
        self.s = None
        for res in socket.getaddrinfo(HOST, self.PORT, socket.AF_UNSPEC,socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                self.s = socket.socket(af, socktype, proto)
            except socket.error as msg:
                print msg
                self.s = None
                continue
            try:
                self.s.bind(sa)
            except socket.error as msg:
                print msg                
                self.s.close()
                self.s = None
                continue
            try:
                self.s.listen(5)
            except socket.error as msg:
                print msg
                self.s.close()
                self.s = None
                continue
            break
        return self.s

    def __exit__(self,type,value,traceback):
        if self.s is not None:
            self.s.close()
        # Error processing 

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
        UP = True
        data = ""
        this,that = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        inputs = []
        inputs.append(self.conn)
        inputs.append(this)
        while UP:
            try:
                inputready,outputready,exceptready = select.select(inputs,[],[])#timeouts
            except seelct.error as msg:
                print 'RTSP Server: '+str(msg)
            for option in inputready:
                if option is self.conn:
                    data = self.conn.recv(1024)
                    p = RTSP.RTSPMessage(data)
                    if p.parse() is False:
                        inputs.remove(self.conn)
                        self.conn.close()
                        UP = False                
                    p.dumpMessage() # Remove,debug
                    if(p.rtspCommand == "OPTIONS"):
                        # Check if same song is already being streamed.If not,create new streamer.       
                        self.conn.sendall(p.createOptionsReplyMessage(p.cseq))
                        p.dumpMessage() # Remove,debug
                    elif(p.rtspCommand == "DESCRIBE"):
                        s = sdp.SDPMessage("Test","23544",7000)
                        self.conn.sendall(p.createDescriptionReplyMessage(p.cseq, p.URI,s.getMessage()))
                        p.dumpMessage() # Remove,debug
                    elif(p.rtspCommand == "SETUP"):
                        # Exec streamer
                        pid = os.fork()
                        if pid < 0:
                            print  'Err'
                        elif pid == 0:
                            os.execlp('python','python','streamer.py',str(that.fileno()))
                        self.conn.sendall(p.createSetupReplyMessage(p.cseq, p.transport, p.clientport, "9000-9001",458959))
                        p.dumpMessage() # Remove,debug
                    elif(p.rtspCommand == "TEARDOWN"):
                        self.conn.sendall(p.createTeardownReplyMessage(p.cseq))
                        p.dumpMessage() # Remove,debug
                        inputs.remove(self.conn)
                        self.conn.close()
                        UP = False
                    elif(p.rtspCommand == "PLAY"):
                        self.conn.sendall(p.createPlayReplyMessage(p.cseq, p.session, p.URI,"", ""))
                        p.dumpMessage() # Remove,debug
                    elif(p.rtspCommand == "PAUSE"):
                        self.conn.sendall(p.createPauseReplyMessage(p.cseq, p.session))
                        p.dumpMessage() # Remove,debug
                    else:
                        print 'Error: RTSP Server,Unknown command'  # create faulty reply
                        inputs.remove(self.conn)         
                        self.conn.close()
                        UP = False
                if option is this:
                    pass

def server(port_rtsp,port_playlist):
    """ This function waits for RTSP/Playlist request and starts new thread. """
    initSongs()    
    inputs = []
    with listen(port_playlist) as playlist_sock:
        with listen(port_rtsp) as rtsp_sock:
            inputs.append(rtsp_sock)
            inputs.append(playlist_sock)    
            while True:    
                try:
                    inputready,outputready,exceptready = select.select(inputs,[],[])
                except select.error as msg:
                    print 'Error '
                for option in inputready:
                    if option is rtsp_sock:
                        try:            
                            conn, addr = rtsp_sock.accept()
                        except socket.error as msg:
                            print 'Server: RTSP '+str(msg)
                            continue
                        print 'Server: RTSP connection from ', addr
                        r = Accept_RTSP(conn,addr)
                        r.start()
                    if option is playlist_sock:
                        try:
                            conn,addr = playlist_sock.accept()
                        except socket.error as msg:
                            print 'Server: Playlist '+str(msg)
                            continue
                        print 'Server: Playlist request from ', addr
                        p = Accept_PL(conn,addr)
                        p.start()

    shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # remove "Wavs" dir
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    args = parser.parse_args()       
    server(args.rtsp,args.playlist)

