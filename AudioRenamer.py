import os
import fnmatch
import sys
import string

from mutagen.id3 import ID3
from mutagen.flac import FLAC
from id3v1 import ID3v1
from eyeD3 import mp3 as MP3

verbose  = False         # prints paths, dirs as they are checked
encoding = 'iso-8859-1'  # filename/tag encoding

def main(root):

    root = unicode(root, encoding)
    root = os.path.abspath(root)

    for path, dirs, fnames in os.walk(root):

        for ext in 'mp3', 'flac':
            file_list = []
            for fname in fnmatch.filter(fnames, "*." + ext):
                file_list.append(fname)
            if file_list:
                process_dir(path, file_list, ext)

def process_dir(path, file_list, ext):

    log_path = True

    if verbose:
        log("")
        log(path, 2)
        log_path = False

    file_list.sort()

    for fname in file_list:

        log_fname = True

        if verbose:
            log(fname, 4)
            log_fname = False
        full_path = os.path.join(path, fname)

        # tag-checking loop: different based on format
        if ext == 'mp3':
            t, e = check_mp3_tags(full_path)
        elif ext == 'flac':
            t, e = check_flac_tags(full_path)

        # create "proper" filename
        pfname = string.zfill(t['tracknumber'], 2) + " "
        if t['albumartist'] and (t['artist'] != t['albumartist']):
            pfname +=  t['artist'] + " - "
        pfname += t['title']

        pfname = safe_fname(pfname) + "." + ext

        if fname != pfname:
            e.append("Wrong name, expected: '" + pfname + "' - rename")
            full_pfname = os.path.join(os.path.dirname(full_path), pfname)
            os.rename(full_path, full_pfname)

        if e:
            if log_path:
                log("")
                log(path, 2)
                log_path = False
            if log_fname:
                log(fname, 4)
                log_fname = False
            for error in e:
                log(error, 6)

    # determine album "quality"
    t['quality'] = determine_quality(full_path)

    # create "proper" dirname
    dname = os.path.basename(path)
    pdname = safe_dname(t['albumartist'] or t['artist'], t['album'], t['quality'])

    if dname != pdname:
        if log_path:
            log("")
            log(path, 2)
        log("Wrong directory name, expected: '" + pdname + "' - rename", 4)
        full_pdname = os.path.join(os.path.dirname(path), pdname)
        os.rename(path, full_pdname)

def check_mp3_tags(full_path):

    t = {} # "proper" tags
    e = [] # errors

    tags = ID3(full_path)

    unallowed = set(tags.keys()).difference(mp3_allow)

    if unallowed:
        for item in unallowed:
            e.append("Unallowed tag: '" + item[:4] + "' - remove")

    # "minimal" tags
    for frame, item in {'TPE1': 'artist', 'TALB': 'album', 'TRCK': 'tracknumber', 'TIT2': 'title', 'TDRC': 'date'}.items():
        if not frame in tags:
            e.append("Tag missing: '" + item + "' - add")
        else:
            t[item] = tags[frame][0]

    # ID3 date tags are their own distinct type in Mutagen
    t['date'] = unicode(t['date'])

    # "optional" tags
    for frame, item in {'TCON': 'genre', 'TPE2': 'albumartist', 'TPOS': 'discnumber'}.items():
        if frame in tags:
            t[item] = tags[frame][0]
        else:
            t[item] = None

    # split "nn/mm" [track|disc]number tags
    for item in 'track', 'disc':
        if '/' in str(t[item + 'number']):
            t[item + 'number'], t[item + 'total'] = t[item + 'number'].split("/")

    # id3v1 check
    e = clean_id3v1_tags(full_path, t, e)

    # Format multiple artists in single track
    if " / " in t['artist']:
        t['artist'] = t['artist'].replace(" / ", ", ")

    return t, e

def check_flac_tags(full_path):

    t = {} # "proper" tags
    e = [] # errors

    tags = FLAC(full_path)

    unallowed = set(tags.keys()).difference(flac_allow)

    if unallowed:
        for item in unallowed:
            e.append("Unallowed tag: '" + item + "' - remove")

    # "minimal" tags
    for item in 'album', 'tracknumber', 'title', 'date':
        t[item] = tags[item][0]

    # Handle multiple artist tags in single track
    if len(tags['artist']) > 1:
        t['artist'] = ", ".join(tags['artist'])
    else:
        t['artist'] = tags['artist'][0]

    # "optional" tags
    for item in 'tracktotal', 'genre', 'albumartist', 'discnumber', 'disctotal':
        if item in tags:
            t[item] = tags[item][0]
        else:
            t[item] = None

    return t, e

def clean_id3v1_tags(full_path, t, e):

    v1 = ID3v1(full_path)

    if v1.comment:
        e.append("Unallowed tag: 'ID3v1 comment ' - remove")

    t1 = {} # temp dict for id3v1 tags
    t1['artist']       = unicode(v1.artist, encoding)
    t1['album']        = unicode(v1.album, encoding)
    t1['tracknumber']  = unicode(str(v1.track), encoding)
    t1['title']        = unicode(v1.title, encoding)
    t1['date']         = unicode(str(v1.year), encoding)

    for item in 'artist', 'album', 'title':
        if len(t[item]) > 30:
            ptag = t[item][:28] + '..'
        else:
            ptag = t[item]

        if t1[item] != ptag:
            e.append("Tag mismmatch: 'ID3v1 " + item + "', expected: '" + ptag + "' - change")
            ptag = ptag.encode(encoding)
            if item == 'artist':
                v1.artist = ptag
            elif item == 'album':
                v1.album = ptag
            elif item == 'title':
                v1.title = ptag
            v1.commit()

    for item in 'tracknumber', 'date':
        if t1[item] != t[item]:
            e.append("Tag mismatch: 'ID3v1 " + item + "', expected: '" + t[item] + "' - change")
            if item == 'tracknumber':
                v1.track = int(t[item])
            elif item == 'date':
                v1.year = str(t[item])
            v1.commit()

    return e

def determine_quality(full_path):

    if full_path.lower().endswith('.flac'):
        return 'FLAC'

    # this is all very hackish, but it works for me...
    f = open(full_path, 'rb')
    pos, header, bytes = MP3.find_header(f, ID3(full_path).size)

    if header:
        header = MP3.Header(header)
    else:
        return 'UNK'

    f.seek(pos)
    frame = f.read(header.frameLength)
    f.close()

    lametag = MP3.LameTag(frame)

    if lametag:
        return lametag['preset']
    else:
        return 'UNK'

def safe_fname(fname):

    import re
    fname, subs = re.subn(r':|\*|<|>|\||\?|\\|/|"|\$|  ', ' ', fname)
    while subs != 0:
        fname, subs = re.subn(r':|\*|<|>|\||\?|\\|/|"|\$|  ', ' ', fname)

    return string.strip(fname)

def safe_dname(artist, album, quality):

    for article in articles:
        index = string.find(artist, article)
        if index == 0:
            artist = string.replace(artist, article, "", 1) + ", " + article

    return "[" + safe_fname(artist) + "] [" + safe_fname(album) + "] [" + quality + "]"

def log(msg, lvl=0):

    print " " * lvl + msg.encode(encoding, 'replace')

# MP3 tags allowed
mp3_allow = ['TPE1', # artist
             'TALB', # album
             'TPOS', # discnumber/disctotal
             'TRCK', # tracknumber/tracktotal
             'TIT2', # title
             'TDRC', # date
             'TCON', # genre
             'TPE2', # albumartist
             'TXXX:replaygain_album_gain',
             'TXXX:replaygain_track_gain',
             'TXXX:replaygain_album_peak',
             'TXXX:replaygain_track_peak']

# FLAC tags allowed
flac_allow = ['artist',
              'album',
              'discnumber',
              'disctotal',
              'tracknumber',
              'tracktotal',
              'title',
              'date',
              'genre',
              'encoder',
              'albumartist',
              'replaygain_album_gain',
              'replaygain_track_gain',
              'replaygain_album_peak',
              'replaygain_track_peak']

articles = ['The ', 'El ', 'La ', 'Los ', 'Las ']

if __name__ == '__main__':

    from time import strftime

    log("AudioRenamer - It renames audio files")
    log("")

    if len(sys.argv) == 1:
        log("Usage: " + os.path.basename(sys.argv[0]) + " <directories>")
        sys.exit(0)

    log("Starting process: " + strftime("%Y-%m-%d %H:%M:%S"), 2)
    log("")

    for arg in sys.argv[1:]:
        main(arg)

    log("")
    log("Process complete: " + strftime("%Y-%m-%d %H:%M:%S"), 2)
    log("")
    raw_input("Press ENTER to exit ")
