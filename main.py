import os
import fnmatch
import sys
import string

from mutagen.id3 import ID3
from mutagen.flac import FLAC
from id3v1 import ID3v1

enc = 'iso-8859-1'

def main(root):

    from time import strftime

    log("AudioRenamer - It renames audio files")
    log("")
    log("Starting process: " + strftime("%Y-%m-%d %H:%M:%S"), 2)
    log("")

    log("mp3")

    for path, dirs, fnames in os.walk(root):
        file_list = []
        for fname in fnmatch.filter(fnames, "*.mp3"):
            file_list.append(fname)
        if file_list:
            process_mp3_dir(path, file_list)

    log("flac")

    for path, dirs, fnames in os.walk(root):
        file_list = []
        for fname in fnmatch.filter(fnames, "*.flac"):
            file_list.append(fname)
        if file_list:
            process_flac_dir(path, file_list)

    log("")
    log("Process complete: " + strftime("%Y-%m-%d %H:%M:%S"), 2)

def process_mp3_dir(path, file_list):

    log(path, 2)

    file_list.sort()

    for fname in file_list:

        log(fname, 4)
        full_path = os.path.join(path, fname)

        tags = ID3(full_path)

        unallowed = set(tags.keys()).difference(mp3_allow)

        if unallowed:
            for item in unallowed:
                log("Unallowed tag: '" + item[:4] + "' - remove", 6)

        t = {} # holds tags info "proper"
        t['artist'] = unicode(tags['TPE1'])
        t['album']  = unicode(tags['TALB'])
        t['track']  = str(tags['TRCK'])
        t['title']  = unicode(tags['TIT2'])
        if 'TDRC' in tags:
            t['date']   = str(tags['TDRC'])
        else:
            t['date'] = ''
            #log("Date tag missing - add", 6)

        if 'TCON' in tags:
            t['genre'] = unicode(tags['TCON'])
        else:
            t['genre'] = None

        if 'TXXX:ALBUM ARTIST' in tags:
            t['album artist'] = unicode(tags['TXXX:ALBUM ARTIST'][0])
        else:
            t['album artist'] = None

        # id3v1 check
        v1 = ID3v1(full_path)

        if v1.comment:
            log("Unallowed tag: 'ID3v1 comment ' - remove", 6)
        t1 = {}
        t1['artist'] = unicode(v1.artist, enc)
        t1['album']  = unicode(v1.album, enc)
        t1['track']  = str(v1.track)
        t1['title']  = unicode(v1.title, enc)
        t1['date']   = str(v1.year)

        for item in 'artist', 'album', 'title':
            if len(t[item]) > 30:
                ptag = t[item][:28] + '..'
            else:
                ptag = t[item]

            if t1[item] != ptag:
                log("Tag mismmatch: 'ID3v1 " + item + "', expected: '" + ptag + "' - change", 6)

        for item in 'track', 'date':
            if t1[item] != t[item]:
                log("Tag mismatch: 'ID3v1 " + item + "', expected: '" + t[item] + "' - change", 6)

        # create "proper" filename
        pfname = string.zfill(t['track'], 2) + " - "
        if t['album artist'] == 'Various':
            pfname +=  t['artist'] + " - "
        pfname += t['title']

        pfname = safe_fname(pfname) + ".mp3"

        if unicode(fname, enc) != pfname:
            log("Wrong name, expected: '" + pfname + "' - rename", 6)

        # soundtrack dirs
        if t['genre'] == "Soundtrack":
            t['album artist'] = t['genre']

    # create "proper" dirname
    dname = os.path.basename(path)
    quality = dname[string.rfind(dname, "["):]
    pdname = safe_dname(t['album artist'] or t['artist'], t['album'], quality)

    if unicode(dname, enc) != pdname:
        log("Wrong directory name, expected: '" + pdname + "' - rename", 4)

    log("") # blank space between dirs

def process_flac_dir(path, file_list):

    log(path, 2)

    file_list.sort()

    for fname in file_list:
        
        log(fname, 4)
        full_path = os.path.join(path, fname)

        tags = FLAC(full_path)

        unallowed = set(tags.keys()).difference(flac_allow)

        if unallowed:
            for item in unallowed:
                log("Unallowed tag: '" + item + "' - remove", 6)

        t = {} # holds tags info "proper"
        for item in 'artist', 'album', 'tracknumber', 'title', 'date', 'genre':
            t[item] = str(tags[item][0].encode('utf-8'))

        if 'va' in tags:
            t['album artist'] = "Various"
        else:
            t['album artist'] = None

        # create "proper" filename
        pfname = string.zfill(t['tracknumber'], 2) + " - "
        if t['album artist'] == 'Various':
            pfname +=  t['artist'] + " - "
        pfname += t['title']

        pfname = safe_fname(pfname) + ".flac"

        if fname != pfname:
            log("Wrong name, expected: '" + pfname + "' - rename", 6)

        # soundtrack dirs
        if t['genre'] == "Soundtrack":
            t['album artist'] = t['genre']

    # create "proper" dirname
    dname = os.path.basename(path)
    quality = dname[string.rfind(dname, "["):]
    pdname = safe_dname(t['album artist'] or t['artist'], t['album'], quality)

    if dname != pdname:
        log("Wrong directory name, expected: '" + pdname + "' - rename", 4)

    log("") # blank space between dirs

def safe_fname(fname):

    for char in illegal_chars:
        fname = string.replace(fname, char, ' ')

    return string.strip(fname)

def safe_dname(artist, album, quality):

    for article in articles:
        index = string.find(artist, article)
        if index == 0:
            artist = string.replace(artist, article, "", 1) + ", " + article

    index = string.find(album, " (OST)")
    if index != -1:
        album = string.replace(album, " (OST)", "", 1)

    return "[" + safe_fname(artist) + "] [" + safe_fname(album) + "] " + quality

def log(msg, lvl=0):

    try:
        print " " * lvl + msg
    except:
        pass
        
    
# MP3 tags allowed
mp3_allow = ['TPE1', # performer
             'TALB', # album
             'TRCK', # track number
             'TIT2', # title
             'TDRC', # date
             'TCON', # genre
             'TENC', # 'encoded by'
             'TXXX:replaygain_album_gain',
             'TXXX:replaygain_track_gain',
             'TXXX:replaygain_album_peak',
             'TXXX:replaygain_track_peak',
             'TXXX:ALBUM ARTIST']

# FLAC tags allowed
flac_allow = ['artist',
              'album',
              'tracknumber',
              'title',
              'date',
              'genre',
              'encoder',
              'discid',
              'va', # various artists
              'replaygain_album_gain',
              'replaygain_track_gain',
              'replaygain_album_peak',
              'replaygain_track_peak']

# illegal characters mapping
"""
char_map = {':': ';',
            '*': ' ',
            '<': '[',
            '>': ']',
            '|': '!',
            '?': ' ',
            '/': ',',
            '\\': ',',
            '-': ','}


"""

illegal_chars = [':', '*', '<', '>', '|', '?', '\\', '/', '"', '$', '  ']
articles = ['The ', 'El ', 'La ', 'Los ', 'Las ']

if __name__ == '__main__':
    main("Y:\\music\\files")
    #main(sys.argv[1])
    #main("Y:\\music\\collection\\2Pac")
    #main("Y:\\music\\files\\[2 Unlimited] [Hits Unlimited] [APS]")
    #main("Y:\\music\\flac\\rips a\\Anathallo")
    #main("Y:\\music\\files\\[Alarm Will Sound] [Acoustica Alarm Will Sound Performs Aphex Twin] [FLAC]")
    #main("Y:\\music\\files\\[Soundtrack] [Akira] [APX]")
    #main("Y:\\music\\files\\[Bacilos] [Caraluna] [APS]") # fails with UnicodeEncodeErrror
    #main("/tank/music/files/[Bacilos] [Caraluna] [APS]")
    #main("/tank/music/files/[2 Unlimited] [Hits Unlimited] [APS]")
    #main("/tank/music/files")
    #main("Y:\\music\\files\\[Jaguares] [El Equilibrio De Los Jaguares] [FLAC]")

