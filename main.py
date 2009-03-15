import os
import fnmatch
import sys
import string

from mutagen.id3 import ID3
from mutagen.flac import FLAC
from id3v1 import ID3v1

def main(root):

    print "AudioRenamer - It renames audio files"
    print ""

    mp3s = {}

    for path, dirs, fnames in os.walk(root):
        for fname in fnmatch.filter(fnames, "*.mp3"):
            if path not in mp3s:
                mp3s[path] = []
            mp3s[path].append(fname)

    for path, fnames in mp3s.iteritems():
        print " " * 2 + path

        fnames.sort()
        for fname in fnames:
            print " " * 4 + fname
            full_path = os.path.join(path, fname)

            tags = ID3(full_path)

            unallowed = set(tags.keys()).difference(mp3_allow)

            if unallowed:
                for item in unallowed:
                    print " " * 6 + "Unallowed tag: '" + item + "' - remove"

            t = {} # holds tags info "proper"
            t['artist'] = str(tags['TPE1'])
            t['album']  = str(tags['TALB'])
            t['track']  = str(tags['TRCK'])
            t['title']  = str(tags['TIT2'])
            t['date']   = str(tags['TDRC'])

            if 'TXXX:ALBUM ARTIST' in tags:
                t['album artist'] = tags['TXXX:ALBUM ARTIST']
            else:
                t['album artist'] = None

            # id3v1 check
            v1 = ID3v1(full_path)

            if v1.comment:
                print " " * 6 + "Unallowed tag: 'ID3v1 comment ' - remove"

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
                    print " " * 6 + "Tag mismmatch: 'ID3v1 " + item + "', expected: '" + ptag + "' - change"
                    print t1[item]

            for item in 'track', 'date':
                if t1[item] != t[item]:
                    print " " * 6 + "Tag mismatch: 'ID3v1 " + item + "', expected: '" + t[item] + "' - change"

            # create "proper" filename
            pfname = string.zfill(t['track'], 2) + " - "
            if t['album artist']:
                pfname +=  t['artist'] + " - "
            pfname += t['title'] + ".mp3"

            if fname != pfname:
                print " " * 6 + "Wrong name, expected: '" + pfname + "' - rename"

        # create "proper" dirname
        dname = os.path.basename(path)
        quality = dname[string.rfind(dname, "["):]
        pdname = "["
        if t['album artist']:
            pdname +=  t['album artist'] + " "
        else:
            pdname += t['artist']

        pdname += "] [" + t['album'] + "] " + quality

        if dname != pdname:
            print " " * 4 + "Wrong directory name, expected: '" + pdname + "' - rename"

        print "" # blank space between dirs

    # reclaim memory
    mp3s = None

    flacs = {}

    for path, dirs, fnames in os.walk(root):
        for fname in fnmatch.filter(fnames, "*.flac"):
            if path not in flacs:
                flacs[path] = []
            flacs[path].append(fname)

    for path, fnames in flacs.iteritems():
        print " " * 2 + path

        fnames.sort()
        for fname in fnames:
            print " " * 4 + fname
            full_path = os.path.join(path, fname)

            tags = ID3(full_path)

            unallowed = set(tags.keys()).difference(mp3_allow)

            if unallowed:
                for item in unallowed:
                    print " " * 6 + "Unallowed tag: '" + item + "' - remove"

            t = {} # holds tags info "proper"
            t['artist'] = str(tags['TPE1'])
            t['album']  = str(tags['TALB'])
            t['track']  = str(tags['TRCK'])
            t['title']  = str(tags['TIT2'])
            t['date']   = str(tags['TDRC'])

            if 'TXXX:ALBUM ARTIST' in tags:
                t['album artist'] = tags['TXXX:ALBUM ARTIST']
            else:
                t['album artist'] = None

            # id3v1 check
            v1 = ID3v1(full_path)

            if v1.comment:
                print " " * 6 + "Unallowed tag: 'ID3v1 comment ' - remove"

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
                    print " " * 6 + "Tag mismmatch: 'ID3v1 " + item + "', expected: '" + ptag + "' - change"
                    print t1[item]

            for item in 'track', 'date':
                if t1[item] != t[item]:
                    print " " * 6 + "Tag mismatch: 'ID3v1 " + item + "', expected: '" + t[item] + "' - change"

            # create "proper" filename
            pfname = string.zfill(t['track'], 2) + " - "
            if t['album artist']:
                pfname +=  t['artist'] + " - "
            pfname += t['title'] + ".mp3"

            if fname != pfname:
                print " " * 6 + "Wrong name, expected: '" + pfname + "' - rename"

        # create "proper" dirname
        dname = os.path.basename(path)
        quality = dname[string.rfind(dname, "["):]
        pdname = "["
        if t['album artist']:
            pdname +=  t['album artist'] + " "
        else:
            pdname += t['artist']

        pdname += "] [" + t['album'] + "] " + quality

        if dname != pdname:
            print " " * 4 + "Wrong directory name, expected: '" + pdname + "' - rename"

        print "" # blank space between dirs

        


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

"""
def main():

    root = "Y:\\music\\files"
    exts = ["mp3", "flac"]

    print "loading files... ",
    file_list = load_file_list(root, exts)
    print "done"
    
    print "parsing directories"
    process_file_list(file_list)
    print "done"


def analyze_file(file_path, ext):

    invalid_tags = set(file_tags.keys()).difference(allow_tags)
    if invalid_tags:
        print "Invalid tags on file '" + file_path + "'"
        for item in invalid_tags:
            print "  " + item + ": " + str(file_tags[item][0]).decode(encoding, 'replace')

"""
if __name__ == '__main__':
    #main(sys.argv[1])
    #main("Y:\\music\\collection\\2Pac")
    main("Y:\\music\\files\\[2 Unlimited] [Hits Unlimited] [APS]")
