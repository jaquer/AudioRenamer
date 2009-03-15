# tags.py - read ID3v1/2 and FLAC tags

import os.path
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from id3v1 import ID3v1

def read_tags(fname, ext=''):

    tags = {}

    if not ext:
        name, ext = os.path.splitext(fname)
        ext = ext[1:]

    if ext == 'mp3':
        return read_tags_mp3(fname)
    elif ext == 'flac':
        return read_tags_flac(fname)

def read_tags_mp3(fname):

    tags = {}

    id3v2_tags = ID3(fname)

    if id3v2_tags:
        tags['id3v2'] = {}

        for tag, values in id3v2_tags.iteritems():
            tags['id3v2'][tag] = str(values)

    id3v1_tags = ID3v1(fname)

    if id3v1_tags:
        tags['id3v1'] = {}

        # i don't know how else to do this
        tags['id3v1']['artist']  = id3v1_tags.artist
        tags['id3v1']['album']   = id3v1_tags.album
        tags['id3v1']['track']   = id3v1_tags.track
        tags['id3v1']['title']   = id3v1_tags.title
        tags['id3v1']['year']    = id3v1_tags.year
        tags['id3v1']['genre']   = id3v1_tags.genre
        tags['id3v1']['comment'] = id3v1_tags.comment

    return tags

def read_tags_flac(fname):

    tags = {}

    flac_tags = FLAC(fname)

    if flac_tags:
        tags = {}

        for tag, values in flac_tags.iteritems():
            tags['flac'][tag] = values[0]

    return tags

if __name__ == '__main__':

    print read_tags("Y:\\music\\files\\[2 Unlimited] [Hits Unlimited] [APS]\\01 - Do What's Good For Me.mp3")
    print read_tags("Y:\\music\\files\\[Alarm Will Sound] [Acoustica Alarm Will Sound Performs Aphex Twin] [FLAC]\\01 - Cock-Ver 10.flac")
