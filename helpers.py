import socket
import datetime

##
# Binding helper
##
def bind(PORT):
    """ Create UDP socket and bind given port with it. """ 
    #HOST = '127.0.0.1'    # Local host
    HOST = socket.gethostbyname(socket.getfqdn())
    s = None
    for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_DGRAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            print 'Streamer: '+str(msg)
            s = None
            continue
        try:
            s.bind(sa)
        except socket.error as msg:
            print 'Streamer: '+str(msg)
            s.close()
            s = None
            continue
        break
    return s

##
# Connects to google dns and gets public ethernet interface ip address of the machine from socket.
##
def tcpLocalIp(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ret = s.getsockname()[0]
    s.close()
    return ret

##
# Creates and binds udp socket. Creates another udp socket and sends to binded socket message. Address information is found in the udp recvfrom function
##
def udpLocalIp():
    server_socket = bind(12345)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto("Ping!",(socket.gethostname(),12345))
    data, address = server_socket.recvfrom(1024)
    ret = address[0]
    sock.close()
    server_socket.close()
    return ret

##
# Gets public ethernet interface ip address of the machine using dns
##
def sockLocalIp():
    ret = socket.gethostbyname(socket.getfqdn())
    return ret

##
# Convinient timestamp function
##
def getTimestamp():
    time = datetime.datetime.today()
    timestamp = str(time.year)+"_"+str(time.month)+"_"+str(time.day)+"_"+str(time.hour)+"_"+str(time.minute)+"_"+str(time.second)
    return timestamp
