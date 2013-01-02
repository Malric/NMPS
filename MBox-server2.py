####
# Playlist/RTSP/SIP server
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
import SIP
import SDP_sip

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

def startANDconnectStreamer(path):
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
        unixsocket.connect(pathtosocket)
    except socket.error as msg:
        print 'RTSP thread unix socket connect',msg
        return None
    return unixsocket

    def startANDconnectReciever(path):
    if not os.path.exists('Sockets/'+path):
        pid = os.fork()
        if pid < 0:
            return None
        elif pid == 0:
           # os.execlp('python','python','reciever.py',path)
    print 'Forked'
    time.sleep(5)
    pathtosocket = 'Sockets/'+path
    print 'server',path
    temp_path = os.tmpnam()
    try:
        unixsocket = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    except socket.error as msg:
        print 'SIP thread unix socket creation',msg
        return None
    try: 
        unixsocket.bind(temp_path)
    except socket.error as msg:
        print 'SIP thread unix socket bind',msg
        return None
    try:
        unixsocket.connect(pathtosocket)
    except socket.error as msg:
        print 'SIP thread unix socket connect',msg
        return None
    return unixsocket

                 
class Accept_PL(threading.Thread):
    """ Thread class. Each thread handles playlist request/reply for specific connection. """
    def __init__(self,conn,addr, port_rtsp):
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
            pl = playlist.getPlaylist(5, socket.gethostbyname(socket.gethostname()), port_rtsp)
            reply = "Playlist OK\r\nLtunez-Server\r\n" + pl + "\r\n"
            print "Playlist Server: Sending playlist"
            self.conn.sendall(reply)
        else:
            print "Playlist Server: Invalid request from client"
        self.conn.close()

class Accept_SIP(threading.Thread):
    """ Thread class. Each thread handles SIP message request/reply for specific connection. """
    def __init__(self,conn,addr, port_sip):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        """ Override base class run() function. """
        data = ''
        unixsocket = None
        server_ip = socket.gethostbyname(socket.gethostname())
        s = SIP.SIPMessage(None)
        while True:
            try:
                data = self.conn.recv(1024)
                s.SIPMsg = data
                if s.parse() is False:
                    self.conn.close()
                else:
                    if s.SIPCommand == "INVITE":
                    sdp_inst = SDP_sip.SDPMessage("MBox", "Talk" ,"123456", self.addr, 8000)
                    reply = s.createInviteReplyMessage(sdp_inst.SDPMsg, self.addr, server_ip)
                    print "Sending invite reply:"
                    print reply
                    self.conn.sendall(reply)
                elif s.SIPCommand == "OPTIONS":
                    sdp_inst = SDP_sip.SDPMessage("MBox", "Talk" ,"123456", self.addr, 8000)
                    reply = s.createOptionsReplyMessage(sdp_inst.SDPMsg, self.addr, server_ip)
                    print "Sending options reply:"
                    print reply
                    self.conn.sendall(reply)
                elif s.SIPCommand == "BYE":
                    reply = s.createByeReplyMessage(server_ip)
                    print "Sending bye reply:"
                    print reply
                    self.conn.sendall(reply)
                    self.conn.close()
                    break

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
        s = sdp.SDPMessage("LTunez", session)

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
                    unixsocket = startANDconnectStreamer(p.pathname)            
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
                try:
                    """ Sending RTSP replies to clients"""
                    self.conn.sendall(funcPointer[p.rtspCommand](p.cseq,p.URI,s.getMessage(),p.transport,p.clientport,u.clientRtpPort+'-'+u.clientRtcpPort,str(session), u.sequence, u.rtptime))
                except socket.error as msg:
                    print 'RTSP thread ',msg
                p.dumpMessage()
            if p.rtspCommand == "TEARDOWN":
                self.conn.close()
                break 
      

def server(port_rtsp,port_playlist, port_sip):
    """ This function waits for RTSP/Playlist request and starts new thread. """
    #playlist.initSongs()    
    inputs = []
    rtspsocket = listen(port_rtsp)
    if rtspsocket is None:
        sys.exit(1)
    playlistsocket = listen(port_playlist)
    if playlistsocket is None:
        rtspsocket.close()
        sys.exit(1)
    sipsocket = listen(port_sip)
    if playlistsocket is None:
        rtspsocket.close()
        playlistsocket.close()
        sys.exit(1)
    inputs.append(rtspsocket)
    inputs.append(playlistsocket)
    inputs.append(sipsocket)    
    while True:    
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[])
        except KeyboardInterrupt:
            print 'Interrupted by user,exiting'
            inputs.remove(rtspsocket)
            inputs.remove(playlistsocket)
            rtspsocket.close()
            playlistsocket.close()
            sipsocket.close()
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
                p = Accept_PL(conn,addr,port_rtsp)
                p.start()
            elif option is sipsocket:
                try:
                    conn,addr = sipsocket.accept()
                except socket.error as msg:
                    print 'Server: SIP ',msg
                    continue
                print 'Server: SIP request from ', addr
                s = Accept_SIP(conn,addr, port_sip)
                s.start()

   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    parser.add_argument("-s", "--sip", help="SIP server port", type=int)
    args = parser.parse_args()       
    server(args.rtsp,args.playlist,args.sip)

