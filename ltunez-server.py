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
import random
import helpers
import plp

server_ip = ""

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

def startANDconnect(file_name):
    file_path = 'Wavs/' + file_name
    socket_path = 'Sockets/' + file_name
    if not os.path.exists(socket_path):
        pid = os.fork()
        if pid < 0:
            return None
        elif pid == 0:
            os.execlp('python','python','streamer.py',file_path,socket_path)
    print 'Server: Forked'
    time.sleep(2)
    temp_path = os.tmpnam()
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
        unixsocket.connect(socket_path)
    except socket.error as msg:
        print 'RTSP thread unix socket connect',msg
        return None
    return unixsocket

class Accept_PL(threading.Thread):
    """ Thread class. Each thread handles playlist request/reply for specific connection. """
    def __init__(self, conn, addr, port_rtsp, playlistLen):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.port_rtsp = port_rtsp
        self.playlistLen = playlistLen

    def run(self):
        """ Override base class run() function. """
        data = self.conn.recv(1024)
        if data is None:
            print "Playlist Server: No data"
        plpmessage = plp.PLPMessage()
        plpmessage.parse(data)
        if plpmessage.command == "GET PLAYLIST" and plpmessage.program =="LTunez-Client":
            #print "Playlist Server: Creating playlist"
            pl = playlist.getPlaylist(self.playlistLen, server_ip, self.port_rtsp)
            reply = plpmessage.createServerOkResponse("LTunez-Server", pl)
            print "Playlist Server: Sending playlist reply:\r\n" + reply 
            self.conn.sendall(reply)
        else:
            #print "Playlist Server: Invalid request from client"
            reply = plpmessage.createServerFailureResponse("LTunez-Server")
            self.conn.sendall(reply)
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
        
        # RTSP Commands:
        funcPointer = dict()
        funcPointer["OPTIONS"] = p.createOptionsReplyMessage
        funcPointer["DESCRIBE"] = p.createDescriptionReplyMessage
        funcPointer["SETUP"] = p.createSetupReplyMessage
        funcPointer["TEARDOWN"] = p.createTeardownReplyMessage
        funcPointer["PLAY"] = p.createPlayReplyMessage
        funcPointer["PAUSE"] = p.createPauseReplyMessage
        session = random.randint(0,1000)
        s = sdp.SDPMessage("LTunez", "LTunez", session)

        # SCP Commands:
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
                    unixsocket = startANDconnect(p.pathname)            
                    if unixsocket is None:
                        self.conn.close()
                        break    
                if p.rtspCommand != "DESCRIBE" and p.rtspCommand != "OPTIONS":
                    try:
                        """ Controlling the streamers is basically done as converting RTSP requests to SCP requests."""
                        r1,r2 = p.clientport.split('-')
                        unixsocket.send(ffuncPointer[p.rtspCommand](self.addr[0],r1,r2))
                    except socket.error as msg:
                        print 'IPC: ',msg
                    if p.rtspCommand == "SETUP" or "PLAY":
                        reply = unixsocket.recv(1024)
                        u.parse(reply)
                        if p.rtspCommand == "SETUP":
                            s.setPort(u.clientRtpPort)
                            s.setRtpmap()
                            s.setMode("sendonly")
                if p.rtspCommand == "DESCRIBE":
                    s.setPort(0)
                    s.setRtpmap()
                    s.setMode("sendonly")
                try:
                    """ Sending RTSP replies to clients"""
                    self.conn.sendall(funcPointer[p.rtspCommand](p.cseq,p.URI,s.getMessage(),p.transport,p.clientport,u.clientRtpPort+'-'+u.clientRtcpPort,str(session), u.sequence, u.rtptime))
                except socket.error as msg:
                    print 'RTSP thread ',msg
                p.dumpMessage()
            if p.rtspCommand == "TEARDOWN":
                self.conn.close()
                break 
      

def server(port_rtsp, port_playlist, playlistLen):
    """ This function waits for RTSP/Playlist request and starts new thread. """
    global server_ip
    playlistLen = playlistLen
    server_ip = helpers.tcpLocalIp()
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
            shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # remove "Wavs" dir
            sys.exit(0)
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
                p = Accept_PL(conn,addr,port_rtsp, playlistLen)
                p.start()
   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    parser.add_argument("-pl", "--playlistLen", help="Amount of items in playlist messages", type=int)
    args = parser.parse_args()
    playlistLen = 3
    if args.playlistLen is not None:
        if args.playlistLen >0 and args.playlistLen <sys.maxint:
            playlistLen = args.playlistLen
    else:
        playlistLen = 3
    server_ip = helpers.sockLocalIp()   
    server(args.rtsp,args.playlist, playlistLen)

