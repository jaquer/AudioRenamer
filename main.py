import os
import fnmatch
import sys

from file_list import *

# MP3 tags allowed
id3v2_allow = ['TPE1', # performer
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

id3v1_allow = ['artist',
               'album',
               'track',
               'title',
               'year',
               'genre']

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

def main():

    root = "Y:\\music\\files"
    exts = ["mp3", "flac"]

    print "loading files... ",
    file_list = load_file_list(root, exts)
    print "done"
    
    print "parsing dirs... ",
    file_list = parse_file_list(file_list)
    print "done"

    print file_list


def analyze_file(file_path, ext):

    invalid_tags = set(file_tags.keys()).difference(allow_tags)
    if invalid_tags:
        print "Invalid tags on file '" + file_path + "'"
        for item in invalid_tags:
            print "  " + item + ": " + str(file_tags[item][0]).decode(encoding, 'replace')


if __name__ == '__main__':
    main()
