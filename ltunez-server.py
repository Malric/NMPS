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
import shutil
import RTSP
import sdp
import playlist
import time

class listen():
    """ Create listening socket, compatible with 'with' method """
    def __init__(self,PORT):
        self.PORT = PORT    
    def __enter__(self):
        HOST = '127.0.0.1'     # Symbolic name meaning all available interfaces
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

def setup(song):
    path = 'Sockets/'+song
    path_c = 'Sockets/temp'
    unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    unix_socket.bind(path_c)    
    unix_socket.connect(path)
    unix_socket.send('Setup,7000,7001')
    data = unix_socket.recv(1024)
    print data
    unix_socket.close()
    msg = data.split(',')
    #if msg[0] is 'Ok':
    return msg[1],msg[2]

class Accept_PL(threading.Thread):
    """ Thread class. Each thread handles playlist request/reply for specific connection. """
    def __init__(self,conn,addr):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        """ Override base class run() function. """
        data = self.conn.recv(1024)
        if data is None:
            print "Playlist Server: No data"
        elif data == "GET PLAYLIST\r\nLtunez-Client\r\n\r\n":
            print "Playlist Server: Creating playlist"
            pl = playlist.getPlaylist(5)
            reply = "Playlist OK\r\nLtunez-Server\r\n" + pl + "\r\n"
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
        inputs = []
        inputs.append(self.conn)
        while UP:
            try:
                inputready,outputready,exceptready = select.select(inputs,[],[])#timeouts
            except select.error as msg:
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
                        # Exec streamer if not exec-ed previously
                        if not os.path.exists('Sockets/'+'song.wav'): #name of song must be variable
                            pid = os.fork()
                            if pid < 0:
                                print  'Err'
                            elif pid == 0:
                                os.execlp('python','python','streamer.py','song.wav') # song argument must be variable
                        time.sleep(5)
                        rtp,rtcp = setup('song.wav') # song argument must be variable
                        self.conn.sendall(p.createSetupReplyMessage(p.cseq, p.transport, p.clientport,rtp + rtcp,458959))
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

def server(port_rtsp,port_playlist):
    """ This function waits for RTSP/Playlist request and starts new thread. """
    playlist.initSongs()    
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

