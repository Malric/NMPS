###
#
# MBox Server
#
###

import RTP
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
import sdp
import helpers
import plp
import io
import writer

server_ip = ""
RTP_PACKET_MAX_SIZE = 1500

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
    HOST = server_ip
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_DGRAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            print 'Binding problem: '+str(msg)
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print 'Binding problem: '+str(msg)
            s.close()
            s = None
            continue
        break
    return s

def startANDconnectStreamer(file_path):
    socket_name = file_path.replace('/', '-')
    if not os.path.isdir("Sockets"):
        os.mkdir("Sockets")
    socket_path = 'Sockets/' + socket_name
    if not os.path.exists(socket_path):
        pid = os.fork()
        if pid < 0:
            return None
        elif pid == 0:
            os.execlp('python','python','streamer.py',"Records/"+file_path,socket_path)
    print 'Server: Forked'
    time.sleep(2)
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
        unixsocket.connect(socket_path)
    except socket.error as msg:
        print 'RTSP thread unix socket connect',msg
        return None
    return unixsocket

class Flow():
    start = True
    stop = False

flows = dict()

class Receiver(threading.Thread):
    """ Receives rtp and rtcp messages """
    def __init__(self, addr, rtp_socket, rtcp_socket, userId, callerId):
        """ Init """
        threading.Thread.__init__(self)
        self.load = ''
        self.addr = addr
        self.rtp_socket = rtp_socket
        self.rtcp_socket = rtcp_socket
        self.rbuf = io.BytesIO()
        self.offset = 0
        self.userId = userId
        self.callerId = callerId

    def run(self):
        print "Starting Receiver"
        """ Main loop """
        inputs = []
        inputs.append(self.rtp_socket)
        inputs.append(self.rtcp_socket)
        rtpmessage = RTP.RTPMessage(24567)
        while True:
            if flows[self.addr].stop == True:
                print "Printing file"
                writer.wavwriter(self.load,len(self.load),self.callerId+"-"+helpers.getTimestamp()+".wav",self.userId)
                flows.pop(self.addr)
                inputs.remove(self.rtp_socket)
                inputs.remove(self.rtcp_socket)
                self.rtp_socket.close()
                self.rtcp_socket.close()
                self.rbuf.close()
                break
            try:
                inputready,outputready,exceptready = select.select(inputs,[],[],0)
            except select.error as msg:
                print 'Receiver: '+str(msg)
            for option in inputready:        
                if option is self.rtcp_socket:
                    data = self.rtcp_socket.recv(1024)
                    pass                 
                    #print data # For now,lets see how it goes
                if option is self.rtp_socket:
                    data, addr = self.rtp_socket.recvfrom(RTP_PACKET_MAX_SIZE)
                    self.rbuf.seek(0, io.SEEK_END)
                    written = self.rbuf.write(data)
                    self.rbuf.seek(-written, io.SEEK_CUR)
                    self.rbuf.readinto(rtpmessage.header)
                    rtpmessage.updateFields()
                    self.offset += rtpmessage.getOffset()
                    self.rbuf.seek(self.offset, io.SEEK_CUR)
                    payloadLen = written-self.offset-12
                    payload = self.rbuf.read(payloadLen)
                    #print "Single packet: " +str(len(payload))
                    self.load += payload
                    #print "Total load: " +str(len(self.load))            


class Accept_PL(threading.Thread):
    """ Thread class. Each thread handles playlist request/reply for specific connection. """
    def __init__(self, conn, addr, port_rtsp):
        """ Initialize with socket and address. """
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.port_rtsp = port_rtsp

    def run(self):
        """ Override base class run() function. """
        data = self.conn.recv(1024)
        if data is None:
            print "Playlist Server: No data"
        else:
            plpmessage = plp.PLPMessage()
            plpmessage.parse(data)
            reply = ""
            if plpmessage.command == "GET PLAYLIST" and plpmessage.program == "MBox-Client":
                print "Playlist Server: Got playlist request for client: " + plpmessage.userid
                pl = playlist.getRecordlist(server_ip, self.port_rtsp, plpmessage.userid)
                if pl:
                    reply = plpmessage.createServerOkResponse("MBox-Server", pl)
                else:
                    reply = plpmessage.createServerFailureResponse("MBox-Server")
            else:
                reply = plpmessage.createServerFailureResponse("MBox-Server")
            print reply
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

def server(port_rtsp, port_playlist, port_sip):
    """ This function waits for RTSP/Playlist/SIP request and starts new thread. """  
    global server_ip 
    server_ip = helpers.tcpLocalIp()
    print "Server: My IP: " + server_ip
    helpers.createDir("Records")
    helpers.createDir("Sockets")
    inputs = []
    rtsp_socket = listen(port_rtsp) # TCP socket
    if rtsp_socket is None:
        sys.exit(1)
    print "Server: RTSP socket listening"
    playlist_socket = listen(port_playlist) # TCP socket
    if playlist_socket is None:
        rtsp_socket.close()
        sys.exit(1)
    print "Server: Playlist socket listening"
    
    sip_socket = bind(port_sip) # UDP socket
    if sip_socket is None:
        rtsp_socket.close()
        playlist_socket.close()
        sys.exit(1)
    print "Server: SIP socket ready"
    
    inputs.append(rtsp_socket)
    inputs.append(playlist_socket)
    inputs.append(sip_socket)

    session = random.randint(1,10000)
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
            shutil.rmtree(os.getcwd() + "/Sockets", ignore_errors=True) # remove "Sockets" dir
            shutil.rmtree(os.getcwd() + "/Records", ignore_errors=True) # remove "Records" dir
            sys.exit(0)
        for option in inputready:
            if option is rtsp_socket:
                try:            
                    conn, addr = rtsp_socket.accept()
                except socket.error as msg:
                    print 'Server: RTSP ',msg
                    continue
                print 'Server: RTSP request from ',addr
                
                r = Accept_RTSP(conn, addr)
                r.start()
            elif option is playlist_socket:
                try:
                    conn,addr = playlist_socket.accept()
                except socket.error as msg:
                    print 'Server: Playlist ', msg
                    continue
                print 'Server: Playlist request from ',addr
                p = Accept_PL(conn, addr, port_rtsp)
                p.start()   
            elif option is sip_socket:
                buff = ''
                try:
                    buff, addr = sip_socket.recvfrom(1024)
                except socket.error as msg:
                    print 'Server: SIP ', msg
                    continue
                print 'Server: SIP message from ', addr, ':'
                sip_inst = SIP.SIPMessage(buff)
                if sip_inst.parse() is True:
                    print sip_inst.SIPMsg
                    client_ip = sip_inst.client_ip
                    if sip_inst.SIPCommand == "INVITE":
                        #Start receiving
                        f = Flow()
                        flows[addr] = f # Use port of remote end too
                        # Create rtp and rtcp socket
                        while True:
                            while True:
                                port = random.randint(10000,65000)
                                rtp_socket = bind(port)
                                if rtp_socket is None:
                                    continue
                                else:
                                    break
                            rtcp_socket = bind(port + 1)
                            if rtcp_socket is None:
                                rtp_socket.close()
                            else:
                                break
                        r = Receiver(addr,rtp_socket,rtcp_socket, sip_inst.userId, sip_inst.callerId)
                        r.start()
                        sdp_inst = sdp.SDPMessage("MBox", "Talk", session)
                        sdp_inst.setPort(port)
                        sdp_inst.setRtpmap()
                        sdp_inst.setC()
                        sdp_inst.setT()
                        reply = sip_inst.createInviteReplyMessage(sdp_inst.getMessage(), client_ip, server_ip, port_sip, sip_inst.userId)
                        print "Sending invite reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                    elif sip_inst.SIPCommand == "OPTIONS":
                        sdp_inst = sdp.SDPMessage("MBox", "Talk", session)
                        #sdp_inst.setPort(8078)
                        sdp_inst.sip_port = port_sip
                        sdp_inst.setRtpmap()
                        sdp_inst.setC()
                        sdp_inst.setT()
                        reply = sip_inst.createOptionsReplyMessage(sdp_inst.getMessage(), client_ip, server_ip, port_sip, sip_inst.userId)
                        print "Sending options reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                    elif sip_inst.SIPCommand == "BYE":
                        #Leave
                        flows[addr].stop = True
                        reply = sip_inst.createByeReplyMessage(server_ip, port_sip, sip_inst.userId)
                        print "Sending bye reply:"
                        print reply
                        sent = sip_socket.sendto(reply, addr)
                        print >>sys.stderr, "Sent %s bytes to %s" % (sent, addr)
                        break
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--playlist", help="playlist server port", type=int)
    parser.add_argument("-r", "--rtsp", help="rtsp server port", type=int)
    parser.add_argument("-s", "--sip", help="SIP server port", type=int)
    args = parser.parse_args()       
    server(args.rtsp,args.playlist,args.sip)

