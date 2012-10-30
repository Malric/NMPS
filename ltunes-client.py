import select
import socket
import curses
import re
import sys
import os

def connect(host,port):
    """ Connect to server and return socket. """
    sock = None
    for res in socket.getaddrinfo(host,int(port), socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            sock = socket.socket(af, socktype, proto)
        except socket.error, msg:
            sock = None
            continue
        try:
            sock.connect(sa)
        except socket.error, msg:
            sock.close()
            sock = None
            continue
        break
    return sock

class Playlist:
    """ Stores and manage playlist """
    cursor = -1
    START = 0 
    END = 19   
    def __init__(self,winH,winPL,winNPL):
        self.winH = winH        
        self.winPL = winPL         
        self.playlist = dict()
        self.winNPL = winNPL
 
    def parse(self,data):
        """ Parse m3u playlist. """
        try:
            lines = data.splitlines()
        except:#be more explicit
            print 'data.splitlines()'    
        for index in range(len(lines) - 3):
            if index%2 != 0:
                continue
            try:        
                lst = re.split('#EXTINF:|,|-',lines[index + 2])
            except:#be more explicit
                print 're.split()'
            self.playlist[index/2] = [int(lst[1]),lst[2],lst[3],lines[index + 3]]
        self.draw()

    def next(self):
        """ Next song. """
        if self.cursor < len(self.playlist) - 1:
            self.cursor += 1
            if self.cursor > self.END:
                self.START += 1
                self.END += 1
        self.draw()

    def previous(self):
        """ Previous song """
        if self.cursor > 0:
            self.cursor -= 1
            if self.cursor < self.START:
                self.START -= 1
                self.END -= 1
        self.draw()

    def play(self):
        pid = os.fork()
        if pid == 0:
            os.system("vlc --quiet")
            sys.exit()
        
    def draw(self):
        self.winH.border()
        self.winH.addstr(1, 35, "***** LTUNES CLIENT *****",curses.A_DIM)
        self.winH.noutrefresh()
        self.winPL.clear()
        self.winPL.border()
        self.winPL.addstr(1,5,"INDEX",curses.A_BOLD)
        self.winPL.addstr(1,15,"ARTIST",curses.A_BOLD)
        self.winPL.addstr(1,35,"SONG",curses.A_BOLD)
        self.winPL.addstr(1,65,"LENGTH",curses.A_BOLD)
        if len(self.playlist) ==  0:
            self.winPL.addstr(10,25,"Please wait,playlist is being downloaded.")
        else:
            for song in self.playlist:
                if song >= self.START and song <= self.END:
                    if song == self.cursor:
                        EFFECT = curses.A_BOLD
                    else:
                        EFFECT = curses.A_DIM
                    self.winPL.addstr(song - self.START + 3, 5, str(song),EFFECT)
                    self.winPL.addstr(song - self.START + 3, 15, self.playlist[song][1],EFFECT)
                    self.winPL.addstr(song - self.START + 3, 35, self.playlist[song][2],EFFECT)
                    self.winPL.addstr(song - self.START + 3, 65, str(self.playlist[song][0])+' sec',EFFECT)
        self.winPL.noutrefresh()
        self.winNPL.clear()
        self.winNPL.border()
        self.winNPL.addstr(1,5,"NOW PLAYING:",curses.A_BOLD) 
        if self.cursor != -1:
            self.winNPL.addstr(1,18,self.playlist[self.cursor][2])
        self.winNPL.noutrefresh()
        
      
def main(host,port):
    """ Handle all events. """
    #Initialize curses,terminal graphics
    stdscr = curses.initscr()
    curses.noecho() 
    curses.cbreak()
    stdscr.keypad(1)
    #Header window
    x_axis = 0
    y_axis = 0
    height = 3
    width = 100 
    winH = curses.newwin(height, width, y_axis, x_axis)
    #Playlist window
    x_axis = 0
    y_axis = 3
    height = 25
    width = 100
    winPL = curses.newwin(height, width, y_axis, x_axis)  
    #Now playing window
    x_axis = 0
    y_axis = 28
    height = 3
    width = 100
    winNPL = curses.newwin(height, width,y_axis, x_axis)
    #Playlist object
    playlist = Playlist(winH,winPL,winNPL)
    playlist.draw
    curses.doupdate()
    #Possible inputs
    inputs = []
    inputs.append(sys.stdin)
    #Send request to playlist server
    sock = connect(host,port)
    if(sock != None):
        req = "GET PLAYLIST\r\n"
        sock.send(req)
        inputs.append(sock)
    quit = False;
    data = ''
    #Loop to select user inputs
    while True:
        try:
            inputready,outputready,exceptready = select.select(inputs,[],[])
        except:
            inputready = []
        for ins in inputready:
            if(ins == sys.stdin):
                ch = stdscr.getch()
                if ch == 113 or ch == 81:
                    quit = True
                elif ch == 112 or ch == 80:
                    playlist.play()
                elif ch == curses.KEY_RIGHT:
                    playlist.next()  
                elif ch == curses.KEY_LEFT:
                    playlist.previous()  
            else:
                data = data + ins.recv(1024)
                #print data
                if re.search('\\r\\n\\r\\n',data):
                    playlist.parse(data)
                    data = ''
            curses.doupdate()
        if quit:
            break
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

if __name__ == "__main__":
    if(len(sys.argv) == 1):
        print 'Ltunes server address & port missing'
        sys.exit(0)
    elif(len(sys.argv) != 2):
        print 'Extra parameters'
        sys.exit(0)
    else:
        inf = sys.argv[1].split(':')
    main(inf[0],inf[1])
