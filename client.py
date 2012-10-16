#!/usr/bin/python

import select 
import socket
import thread
import time
import sys
import struct
import hashlib

own_ip = ""
own_port = 42426
remote_ip = "130.233.43.104"
remote_port = 12100

salt = 1234567890
HEADER_LEN = 16
lock = thread.allocate_lock()

header_format = "!"+"BBBB" # Version, TTL, type, reserve
header_format += "HH"      # Sender port, Payload length
header_format += "I"       # Origian sender IP
header_format += "I"       # Message ID

msg_types = { "ping": 0x00, "pong": 0x01, "bye": 0x02, "join": 0x03, "query": 0x80, "queryhit": 0x81 }

socketlist = {}
knownhosts = []

def makeSocketAndConnection(ip, port):
    global socketlist
    global knownhosts
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    newSocket.connect((ip,int(port)))
    socketlist[newSocket] = (ip,port)
    addToKnownHosts(ip,port)
    return newSocket

#############################################################################
# Main eventloop for the p2p-client

def Client():
    global socketlist
    global knownhosts
    global ownkeypairs
    running = 1
    # Outer loop for broken connections
    while(running > 0):
        print("hit enter to connect client (or 'q' to quit)")
        command = raw_input()
        if(command == 'q'):
            running = 0
            break

        global remote_ip, own_ip
#        remote_ip = own_ip
        serverSocket = makeSocketAndConnection(remote_ip, remote_port)
        local_ip, local_port = serverSocket.getsockname()

        
        print("Connected, sending join request")
        
        #Send HELLO message!
        #serverSocket.send(CreateJoinRequest(local_ip, local_port))
        
        data = serverSocket.recv(1024)
        if(not data):
            print("Server broke connection.")
        elif(invalid_packet(data)):
            print("Client received an invalid packet, breaking connection")
        else:
            # Decode message!
            ver, ttl, msg_type, rsv, sender_port, payload_len, ip, m_id = \
                struct.unpack(header_format, data[0:16])
            a, b = struct.unpack("!BB",data[16:18])
            if(msg_type != msg_types["join"] or
               len(data) < 18):
                print("Server did not reply with a correct join message, breaking")
            else:
                print("Server sent a good join message")
                running = 2
                PrintHelp()

        # Set up select input-list
        while(len(socketlist) > 0):
            input = socketlist.keys()
            input.append(sys.stdin)
            inputready,outputready,exceptready = select.select(input,[],[])
            for s in inputready:
                if (s == sys.stdin):
                    # STDIN Parsering!
                    commands = sys.stdin.readline().strip().split()
                    StdinActions(commands);
                   
                else:
                    # handle all other sockets
                    data = s.recv(1024)
                    if(not data):
                        print("Connection was broken")
                        running = 1
                        break

                    if(invalid_packet(data)):
                        print("Client received an invalid packet, ignoring")
                        continue
    
                    ver, ttl, msg_type, rsv, sender_port, payload_len, ip, m_id = \
                        struct.unpack(header_format, data[0:16])
                    
                    if (msg_type == msg_types["ping"]):
                        if(ttl == 1):
                            print "Ping type A from", s.getpeername()
                        else:
                            print "Ping type B from", s.getpeername()
                        packet = CreatePong(ip, sender_port, ttl, ip)
                        print "Sending Pong to ", s.getpeername()
                        s.send(packet)
                    elif (msg_type == msg_types["pong"]):
                        if(payload_len == 0):
                            print "Pong type A from ", s.getpeername()
                        else:
                            print "Pong type B from ", s.getpeername()
                        ParsePong(data, payload_len)
                    elif (msg_type == msg_types["bye"]):
                        s.close()
                        print "Connection closed to: ", socketlist[s][0], socketlist[s][1]
                        del (socketlist[s])
                        #remove s from input[]
                    elif (msg_type == msg_types["join"]):
                        if (payload_len == 0):
                            print "Join from ", s.getpeername()
                            myip, myport = s.getsockname()
                            packet = CreateJoinResponse()
                            s.send(packet)
                    elif (msg_type == msg_types["query"]):
                        query = ParseQuery(data,payload_len)
                        print "Query: ", query
                        response = {}
                        for key in ownkeypairs.keys():
                            print("Key: ",key)
                            if (key.find(query)):
                                response[key]=ownkeypairs[key]
                        myip, myport = s.getsockname()
                        packet = CreateQueryHit(myip, myport, 5, m_id, response)
                        s.send(packet)
                    elif (msg_type == msg_types["queryhit"]):
                        answers = ParseQueryHit(data[16:])
                        if answers:
                            print("Results are:")
                            for id, value in answers.iteritems():
                                print(id,":",value)
                        else:
                            print("No results were found by with your query.")
                    else:
                        print "hoi"

        PrintHelp()
        serverSocket.close()


############################################################################
# STDIN Actions

def StdinActions(Commands):
    if(len(commands) == 0): 
        PrintHelp()
        continue
    command = commands[0]
    if(len(commands)) > 1:
        socknum = int(commands[1]) - 1
    else:
        socknum = 0
        if(len(socketlist.keys()) <= socknum):
            print("Invalid peer!")
            continue
        serverSocket = socketlist.keys()[socknum]
    if (command == "q"):
        print("quitting")
        packet = CreateBye(local_ip, local_port)
        for sock in socketlist.keys():
            sock.send(packet)
            socketlist = {}
            running = 0
    elif (command == "pa"):
        packet = CreatePingA(local_ip, local_port)
        #Send ping to everybody we have contact to
        for sock in socketlist.keys():
            print "Client sending ping to ",\
                socketlist[sock][0]
            sock.send(packet)
    elif (command == "pb"):
        packet = CreatePingB(local_ip, local_port)
        #Send ping to everybody we have contact to
        for sock in socketlist.keys():
            print "Client sending ping to ", socketlist[sock][0]
            sock.send(packet)
    elif (command == "j"):
        print("Please give id of the host you wish to join")
        j = 0
        for host in knownhosts:
            j += 1
            print j, ":", knownhosts[j-1][0], knownhosts[j-1][1]
            host = sys.stdin.readline().strip()
            hostint = int(host)
            if (hostint > 0 and hostint <j+1):
                if (knownhosts[hostint-1] in socketlist.values()):
                    print("Already open connection!")
                else:
                    print "Hostint: ", hostint
                    print "Address: ", knownhosts[hostint-1][0]
                    print "Port: ", knownhosts[hostint-1][1]
                    newSocket = makeSocketAndConnection(knownhosts[hostint-1][0],
                                                        knownhosts[hostint-1][1])
                    myip, myport = newSocket.getsockname()
                    packet = CreateJoinRequest(myip, myport)
                    newSocket.send(packet)
            else:
                print("Erroneous input:",hostint)
    elif (command == "f"):
        print("Client sending faulty packet")
        serverSocket.send(struct.pack("!BB", 0x02, 0x00))
    elif (command == "b"):
        print("Which connection you wish to terminate?")
        i = 0
        skey ={}
        for sock in socketlist.keys():
            i += 1
            skey[i] = sock
            print i, ":", socketlist[sock][0], socketlist[sock][1]
            key = int(sys.stdin.readline().strip())
            if (key > 0 and key < i+1):
                packet = CreateBye(local_ip, local_port)
                skey[key].send(packet)
                del(socketlist[skey[key]])
            else:
                print "erroneous input"
    elif (command == "query"):
        print("Which connection you wish to send query to?")
        i = 0
        skey ={}
        for sock in socketlist.keys():
            i += 1
            skey[i] = sock
            print i, ":", socketlist[sock][0], socketlist[sock][1]
            key = int(sys.stdin.readline().strip())
            if (key > 0 and key < i+1):
                print("Please give query:")
                query = sys.stdin.readline().strip()
                packet = CreateQuery(local_ip, local_port, 5, query)
                skey[key].send(packet)
            else:
                print "erroneous input"
        else:
            PrintHelp()
            
#############################################################################
# Run the code

# Start the client
Client()
