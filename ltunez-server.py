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
import scp
import tempfile

def listen(PORT):
    """ Create listening socket """
    HOST = None     # Symbolic name meaning all available interfaces
    PORT = PORT     
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC,socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            print 'Server: ',msg
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print 'Server: ',msg                
            s.close()
            s = None
            continue
        try:
            s.listen(5)
        except socket.error as msg:
            print 'Server: ',msg
            s.close()
            s = None
            continue
        break
    return s

def startANDconnect(path):
    if not os.path.exists('Sockets/'+path):
        pid = os.fork()
        if pid < 0:
            return None
        elif pid == 0:
            os.execlp('python','python','streamer.py',path)
    print 'Forked'
    time.sleep(5)
    pathtosocket = 'Sockets/'+path
    print 'server',path
    #temp_path = os.tmpnam()
    #temp,temp_path = tempfile.mkstemp()
    #os.close(temp)
    temp_path ='/tmp/kjlkjl'
    print temp_path
    #print temp,temp_path
    try:
        unixsocket = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    except socekt.error as msg:
        print 'RTSP thread unix socket creation',msg
        return None
    try: 
        unixsocket.bind(temp_path)
    except socket.error as msg:
        print 'RTSP thread unix socket bind',msg
        return None
    try:
        unixsocket.connect(pathtosocket)
    except socket.error as msg:
        print 'RTSP thread unix socket connect',msg
        return None
    return unixsocket
                 
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
        data = ''
        unixsocket = None
        p = RTSP.RTSPMessage(None)
        funcPointer = dict()
        funcPointer["OPTIONS"] = p.createOptionsReplyMessage
        funcPointer["DESCRIBE"] = p.createDescriptionReplyMessage
        funcPointer["SETUP"] = p.createSetupReplyMessage
        funcPointer["TEARDOWN"] = p.createTeardownReplyMessage
        funcPointer["PLAY"] = p.createPlayReplyMessage
        funcPointer["PAUSE"] = p.createPauseReplyMessage
        s = sdp.SDPMessage("Test","23544",0)
        u = scp.SCPMessage()
        ffuncPointer = dict()
        ffuncPointer["SETUP"] = u.createSetup
        ffuncPointer["TEARDOWN"] = u.createTeardown
        ffuncPointer["PLAY"] = u.createPlay
        ffuncPointer["PAUSE"] = u.createPause
        while True:
            data = self.conn.recv(1024)
            p.fromstring(data)       
            p.dumpMessage()  
            if p.parse() is False:
                self.conn.close()
                break
            else:
                if p.rtspCommand == "SETUP":
                    unixsocket = startANDconnect('jayate.wav')#For now
                    print unixsocket                    
                    if unixsocket is None:
                        self.conn.close()
                        break    
                if p.rtspCommand != "DESCRIBE" and p.rtspCommand != "OPTIONS":
                    try:
                        r1,r2 = p.clientport.split('-')
                        unixsocket.send(ffuncPointer[p.rtspCommand](self.addr[0],r1,r2))#change rtp and rtcp to variable
                    except socket.error as msg:
                        print 'IPC: ',msg
                print p.rtspCommand
                try:
                    self.conn.sendall(funcPointer[p.rtspCommand](p.cseq,p.URI,s.getMessage(),p.transport,p.clientport,"9000-90001","23544","4566","0"))
                except socket.error as msg:
                    print 'RTSP thread ',msg
                p.dumpMessage()
      

def server(port_rtsp,port_playlist):
    """ This function waits for RTSP/Playlist request and starts new thread. """
    playlist.initSongs()    
    inputs = []
    rtspsocket = listen(port_rtsp)
    if rtspsocket is None:
        sys.exit(1)
    playlistsocket = listen(port_playlist)
    if playlistsocket is None:
        rtspsocket.close()
        sys.exit(1)
    inputs.append(rtspsocket)
    inputs.append(playlistsocket)    
    while True:    
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[])
        except KeyboardInterrupt:
            print 'Interrupted by user,exiting'
            inputs.remove(rtspsocket)
            inputs.remove(playlistsocket)
            rtspsocket.close()
            playlistsocket.close()
            #shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # remove "Wavs" dir
            break
        for option in inputready:
            if option is rtspsocket:
                try:            
                    conn, addr = rtspsocket.accept()
                except socket.error as msg:
                    print 'Server: RTSP ',msg
                    continue
                print 'Server: RTSP connection from ', addr
                r = Accept_RTSP(conn,addr)
                r.start()
            elif option is playlistsocket:
                try:
                    conn,addr = playlistsocket.accept()
                except socket.error as msg:
                    print 'Server: Playlist ',msg
                    continue
                print 'Server: Playlist request from ', addr
                p = Accept_PL(conn,addr)
                p.start()
   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    args = parser.parse_args()       
    server(args.rtsp,args.playlist)

