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
    """ Create listening TCP socket """
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

def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    HOST = ""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))
    return s

def startANDconnectStreamer(path):
    if not os.path.exists('Sockets/'+path):
        pid = os.fork()
        if pid < 0:
            return None
        elif pid == 0:
            os.execlp('python','python','streamer.py',path,"Records")
    print 'Forked'
    time.sleep(5)
    pathtosocket = 'Sockets/'+path
    print 'server',path
    temp_path = os.tmpnam()
    try:
        unixsocket = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    except socket.error as msg:
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

'''
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
'''
 
class Accept_PL(threading.Thread):
    """ Thread class. Each thread handles playlist request/reply for specific connection. """
    def __init__(self,conn,addr, port_rtsp):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.port_rtsp = port_rtsp

    def run(self):
        """ Override base class run() function. """
        data = self.conn.recv(1024)
        if data is None:
            print "Server: No data"
        elif data == "GET PLAYLIST\r\nLtunez-Client\r\n\r\n":
            print "Server: Creating recordlist"
            pl = playlist.getRecordList(socket.gethostbyname(socket.gethostname()), self.port_rtsp)
            reply = "Playlist OK\r\nLtunez-Server\r\n" + pl + "\r\n"
            print "Server: Sending recordlist"
            self.conn.sendall(reply)
        else:
            print "Server: Invalid request from client"
        self.conn.close()


class Accept_SIP(threading.Thread):
    """ Thread class. Thread handles SIP message request/reply. """
    def __init__(self, sip_socket, buff, addr):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.s = sip_socket
        self.buff = buff
        self.addr = addr

    def run(self):
        """ Override base class run() function. """
        #unixsocket = None
        server_ip = socket.gethostbyname(socket.gethostname())
        while True:
            sip_inst = SIP.SIPMessage(self.buff)
            if sip_inst.parse() is True:
                print sip_inst.SIPMsg
                client_ip = sip_inst.client_ip
                if sip_inst.SIPCommand == "INVITE":
                    #unixsocket = startANDconnectStreamer(p.pathname)            
                    #if unixsocket is None:
                        #break
                    #unixsocket.send(
                    #unitsocket.recv port info...
                    sdp_inst = SDP_sip.SDPMessage("123456", "Talk", client_ip)
                    reply = sip_inst.createInviteReplyMessage(sdp_inst.SDPMsg, client_ip, server_ip)
                    print "Sending invite reply:"
                    print reply
                    sent = self.s.sendto(reply, self.addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, self.addr)
                elif sip_inst.SIPCommand == "OPTIONS":
                    sdp_inst = SDP_sip.SDPMessage("123456", "Talk", client_ip)
                    reply = sip_inst.createOptionsReplyMessage(sdp_inst.SDPMsg, client_ip, server_ip)
                    print "Sending options reply:"
                    print reply
                    sent = self.s.sendto(reply, self.addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, self.addr)
                elif sip_inst.SIPCommand == "BYE":
                    #unitsocket.send(TEARDOWN)
                    reply = sip_inst.createByeReplyMessage(server_ip)
                    print "Sending bye reply:"
                    print reply
                    sent = self.s.sendto(reply, self.addr)
                    print >>sys.stderr, "Sent %s bytes to %s" % (sent, self.addr)
                    break
            self.buff = ''
            self.buff, self.addr = self.s.recvfrom(1024)
            print 'Server: SIP message from ', self.addr, ':'

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

def server(port_rtsp, port_playlist, port_sip):
    """ This function waits for RTSP/Playlist/SIP request and starts new thread. """
    playlist.initSongsWav()  
    inputs = []
    rtsp_socket = listen(port_rtsp) # TCP socket
    if rtsp_socket is None:
        sys.exit(1)
    print "RTSP socket listening"
    playlist_socket = listen(port_playlist) # TCP socket
    if playlist_socket is None:
        rtsp_socket.close()
        sys.exit(1)
    print "Playlist socket listening"
    sip_socket = bind(port_sip) # UDP socket
    if sip_socket is None:
        rtsp_socket.close()
        playlist_socket.close()
        sys.exit(1)
    print "SIP socket ready"
    inputs.append(rtsp_socket)
    inputs.append(playlist_socket)
    inputs.append(sip_socket)
    SIP_once = False # only one SIP thread for now   
    while True:
        try:
            inputready,outputready,exceptready = select.select(inputs, [], [])
        except KeyboardInterrupt:
            print 'Interrupted by user,exiting'
            inputs.remove(rtsp_socket)
            inputs.remove(playlist_socket)
            inputs.remove(sip_socket)
            rtsp_socket.close()
            playlist_socket.close()
            sip_socket.close()
            #shutil.rmtree(os.getcwd() + "/Wavs", ignore_errors=True) # remove "Wavs" dir
            break
        for option in inputready:
            if option is rtsp_socket:
                try:            
                    conn, addr = rtsp_socket.accept()
                except socket.error as msg:
                    print 'Server: RTSP ',msg
                    continue
                print 'Server: RTSP connection from ', addr
                
                r = Accept_RTSP(conn, addr)
                r.start()
                
            elif option is playlist_socket:
                try:
                    conn,addr = playlist_socket.accept()
                except socket.error as msg:
                    print 'Server: Recordlist ', msg
                    continue
                print 'Server: Recordlist request from ', addr
                p = Accept_PL(conn, addr, port_rtsp)
                p.start()
                
            elif option is sip_socket and not SIP_once:
                SIP_once = True
                buff = ''
                try:
                    buff, addr = sip_socket.recvfrom(1024)
                except socket.error as msg:
                    print 'Server: SIP ', msg
                    continue
                print 'Server: Starting SIP thread, SIP message from ', addr, ':'
                s = Accept_SIP(sip_socket, buff, addr)
                s.start()
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    parser.add_argument("-s", "--sip", help="SIP server port", type=int)
    args = parser.parse_args()       
    server(args.rtsp,args.playlist,args.sip)

