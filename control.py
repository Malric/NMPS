import socket
import thread
import time

own_ip = ""
own_port = 42426

controlmsg_types ={"hello": 0x00}

#############################################################################
# Handle input from a peer, add valid joins to connections, close otherwise
def ControlHandler(clientSocket, clientAddr):
    print ("Server accepted connection from: ", clientAddr)
    print ("My info: ", clientSocket.getsockname())
    print ("Client info: ", clientSocket.getpeername())
    while(clientSocket):
        data = clientSocket.recv(1024)
        if not data:
            # Lost connection
            print "Server lost connection, breaking"
            break
        if (invalid_packet(data)): 
            print("Server received an invalid packet, breaking")
            break

        # Insert here message decoding

        #ver, ttl, msg_type, rsv, sender_port, payload_len, ip, m_id = \
        #    struct.unpack(header_format, data[0:16])
        #print(struct.unpack(header_format, data[0:16]))

        ip, port = clientSocket.getsockname()

        # Insert here logic for managing clients
        if (msg_type == controlmsg_types["hello"]):
            # Valid join, create response
            print "Server got hello message"
            return
        else:
            print "Faulty packet, breaking"
            break

    clientSocket.close()

#############################################################################
# Listen for new connections, spawn threads for every incoming connection
def ControlListener(arg):
    global own_ip, own_port
    own_ip = socket.gethostname()

    print "Accepting incoming connections to ip ",own_ip," port", own_port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    try:
        s.bind((own_ip, own_port))
        s.listen(100)  # Max 100 connections
    except:
        print "ERROR binding to socket!"
        sys.exit(1)

    print("Serving ip ",own_ip," at ",own_port)

    while(1):
        conn, addr = s.accept()
        print "Server connected: ",addr

        # New thread for every new client connection
        try:
            thread.start_new_thread(ControlHandler, (conn, addr))
        except:
            print "Could not start a thread"
            sys.exit(1)
            

    s.close

