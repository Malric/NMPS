###
#
# LTunez: Playlist generation including MP3 to wav (pcm mu-law) conversion
# Ltunez: Playlist is randomly generated from the songs that were not in the previous playlist (if possible)
# MBox: Playlist is generated from specific client's recordings
#
###

import os
import errno
import random
from ffmpegwrapper import FFmpeg, Input, Output, AudioCodec, options
import eyeD3
import wav

songs = []

class Song: # used in LTunez
    def __init__(self, length, artist, title, path):
        self.length = length
        self.artist = artist
        self.title = title
        self.path = path
        self.in_last_pl = False # determines whether the song was in the last playlist

def initSongs():
    """ This function creates wav files from MP3s and Song objects into 'songs' list. Used in LTunez """
    global songs
    try:
        os.makedirs(os.getcwd() + "/Wavs") # create "Wavs" dir to current working dir
    except OSError as exception:
        if exception.errno != errno.EEXIST: # ignore error if path exists
            raise
    
    mp3_filenames = os.listdir("MP3s")
    
    for mp3_filename in mp3_filenames:
        mp3_path = "MP3s/" + mp3_filename
        wav_filename = os.path.splitext(mp3_filename)[0] + ".wav" # wav filename is the same as mp3 except the extension
        wav_path = "Wavs/" + wav_filename
        
        # construct and run ffmpeg command
        input_mp3 = Input(mp3_path)
        output_wav = Output(wav_path, AudioCodec("pcm_mulaw"))
        opt_dict = dict([("-ar", "8000"), ("-ac", "1"), ("-ab", "64000")]) # sampling rate 8000 Hz, 1 audio channel (mono), bitrate 64kbits/s
        opt = options.Option(opt_dict)
        ffmpeg_command = FFmpeg("ffmpeg", input_mp3, opt, output_wav)
        ffmpeg_command.run()
        print "Playlist Server: File created: '" + wav_filename + "'"
        
        mp3header = eyeD3.Mp3AudioFile(mp3_path)
        length = str(mp3header.getPlayTime())
        tag = eyeD3.Tag()
        tag.link(mp3_path)
        song = Song(length, tag.getArtist(), tag.getTitle(), wav_path)
        songs.append(song)

def getPlaylist(size, ip, port):
    """ This function returns a playlist string in M3U format. Used in LTunez """
    global songs
    
    pl_idxs = [] # songs to playlist (song indexes in 'songs' list)
    i = 0
    
    if size > songs.__len__():
        print "Playlist Server: Requested playlist size is too big"
        return ""
    elif size*2 <= songs.__len__():
        idxs = [] # playlist is randomly chosen from these songs (song indexes in 'songs' list)
        for song in songs:
            if song.in_last_pl is False:
                idxs.append(i)
            else:
                song.in_last_pl = False
            i += 1
        pl_idxs = random.sample(idxs, size)
    else: # songs have to be chosen from the whole 'songs' list
        pl_idxs = random.sample(range(songs.__len__()), size)
    
    playlist = "#EXTM3U\r\n"
    
    for idx in pl_idxs:
        i = songs[idx].path.rfind("/")
        wav_filename = songs[idx].path[i+1:]
        print "Playlist Server: Adding '" + wav_filename + "' to playlist"
        playlist += "#EXTINF:" + str(songs[idx].length) + ", " + songs[idx].artist + " - " + songs[idx].title + "\r\nrtsp://"+ip+":"+str(port)+"/" + wav_filename + "\r\n"
        songs[idx].in_last_pl = True
    return playlist

class Record: # used in MBox
    def __init__(self, length, caller, title, path):
        self.length = length
        self.caller = caller
        self.title = title
        self.path = path

def getRecordList(ip, port, client_name):
    """ This function returns a recordlist string for a client in M3U format. Used in MBox """
    if os.path.isdir(os.getcwd() + "/" + client_name):
        print "Playlist Server: Client folder found"
    else:
        print "Playlist Server: Client folder not found"
        return False
    
    records = []
    
    wav_filenames = os.listdir(client_name)
    for wav_filename in wav_filenames:
        if ".wav" in wav_filename:
            wav_path = client_name + "/" + wav_filename
            temp = wav_filename.split(".",2)
            temp2 = temp[0].split("-",2)  # wav files must be named: <caller>-<title>.wav
            caller = temp2[0]
            title = temp2[1]
            wave = wav.Wave(wav_path)  
            length = wave.getDuration()
            record = Record(length, caller, title, wav_path)
            records.append(record)

    recordlist = "#EXTM3U\r\n"
    for record in records:
        i = record.path.rfind("/")
        wav_filename = record.path[i+1:]
        print "Playlist Server: Adding '" + wav_filename + "' to playlist"
        recordlist += "#EXTINF:" + str(record.length) + ", " + record.caller + " - " + record.title +"\r\nrtsp://"+ip+":"+str(port)+"/"+wav_filename+"\r\n"
    return recordlist
