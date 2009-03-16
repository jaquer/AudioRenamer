import os
import fnmatch
import sys
import string

from mutagen.id3 import ID3
from mutagen.flac import FLAC
from id3v1 import ID3v1

def main(root):

    from time import strftime

    log("AudioRenamer - It renames audio files")
    log("")
    log("Starting process: " + strftime("%Y-%m-%d %H:%M:%S"), 2)
    log("")

    mp3s = {}

    for path, dirs, fnames in os.walk(root):
        for fname in fnmatch.filter(fnames, "*.mp3"):
            if path not in mp3s:
                mp3s[path] = []
            mp3s[path].append(fname)

    for path, fnames in mp3s.iteritems():
        log(path, 2)

        fnames.sort()
        for fname in fnames:
            log(fname, 4)
            full_path = os.path.join(path, fname)

            tags = ID3(full_path)

            unallowed = set(tags.keys()).difference(mp3_allow)

            if unallowed:
                for item in unallowed:
                    log("Unallowed tag: '" + item + "' - remove", 6)

            t = {} # holds tags info "proper"
            t['artist'] = str(tags['TPE1'])
            t['album']  = str(tags['TALB'])
            t['track']  = str(tags['TRCK'])
            t['title']  = str(tags['TIT2'])
            t['date']   = str(tags['TDRC'])

            if 'TXXX:ALBUM ARTIST' in tags:
                t['album artist'] = str(tags['TXXX:ALBUM ARTIST'][0])
            else:
                t['album artist'] = None

            # id3v1 check
            v1 = ID3v1(full_path)

            if v1.comment:
                log("Unallowed tag: 'ID3v1 comment ' - remove", 6)

            t1 = {}
            t1['artist'] = str(v1.artist)
            t1['album']  = str(v1.album)
            t1['track']  = str(v1.track)
            t1['title']  = str(v1.title)
            t1['date']   = str(v1.year)

            for item in 'artist', 'album', 'title':
                if len(t[item]) > 28:
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

            if fname != pfname:
                log("Wrong name, expected: '" + pfname + "' - rename", 6)

        # create "proper" dirname
        dname = os.path.basename(path)
        quality = dname[string.rfind(dname, "["):]
        pdname = safe_dname(t['album artist'] or t['artist'], t['album'], quality)

        if dname != pdname:
            log("Wrong directory name, expected: '" + pdname + "' - rename", 4)

        log("") # blank space between dirs

    # reclaim memory
    mp3s = None

    flacs = {}

    for path, dirs, fnames in os.walk(root):
        for fname in fnmatch.filter(fnames, "*.flac"):
            if path not in flacs:
                flacs[path] = []
            flacs[path].append(fname)

    for path, fnames in flacs.iteritems():
        log(path, 2)

        fnames.sort()
        for fname in fnames:
            log(fname, 4)
            full_path = os.path.join(path, fname)

            tags = FLAC(full_path)

            unallowed = set(tags.keys()).difference(flac_allow)

            if unallowed:
                for item in unallowed:
                    log("Unallowed tag: '" + item + "' - remove", 6)

            t = {} # holds tags info "proper"
            for item in 'artist', 'album', 'tracknumber', 'title', 'date':
                t[item] = str(tags[item][0])

            if 'album artist' in tags:
                t['album artist'] = tags['album artist']
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

        # create "proper" dirname
        dname = os.path.basename(path)
        quality = dname[string.rfind(dname, "["):]
        pdname = safe_dname(t['album artist'] or t['artist'], t['album'], quality)
        
        if dname != pdname:
            log("Wrong directory name, expected: '" + pdname + "' - rename", 4)

        log("") # blank space between dirs

    # reclaim memory
    flacs = None


    log("Process complete: " + strftime("%Y-%m-%d %H:%M:%S"), 2)


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

    print " " * lvl + msg
        
    
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
    #main("Y:\\music\\files\\[Boards Of Canada] [The Campfire Headphase] [APX]") # fails with UnicodeEncodeError
    #main("Y:\\music\\files\\[Bacilos] [Caraluna] [APS]") # fails with UnicodeEncodeErro    

