import datetime
import os
import re
import subprocess
import sys
import string
import struct

from mutagen.id3 import ID3
from mutagen.mp3 import MPEGInfo
from mutagen.flac import FLAC
from mutagen.flac import VCFLACDict
from id3v1 import ID3v1

encoding = 'iso-8859-1'  # filename/tag encoding

def main(root):

    root = unicode(root, encoding)
    root = os.path.abspath(root)

    for path, dirs, fnames in os.walk(root):

        for ext in 'mp3', 'flac':
            file_list = []
            for fname in fnames:
                if fname.lower().endswith('.' + ext):
                    file_list.append(fname)
            if file_list:
                process_dir(path, file_list, ext)

def process_dir(path, file_list, ext):

    log("")
    log(path, 2)

    file_list.sort()

    for fname in file_list:

        full_path = os.path.join(path, fname)
        e = []

        # tag-checking loop: different based on format
        if ext == 'mp3':
            if (reset_tags):
                reset_mp3_tags(full_path)
                e.append("Tags reset")
            t, e = check_mp3_tags(full_path, e)
        elif ext == 'flac':
            if (reset_tags):
                reset_flac_tags(full_path)
                e.append("Tags reset")
            t, e = check_flac_tags(full_path, e)

        for item in 'artist', 'album', 'title', 'albumartist':
            e = check_unallowed_pattern(item, t[item], e)

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
            log(fname, 4)
            for error in e:
                log(error, 6)

    rename_extras(path, t)

    check_cover(path)

    # determine album "quality"
    t['quality'] = determine_quality(path, ext)

    # create "proper" dirname
    dname = os.path.basename(path)
    pdname = safe_dname(t)

    if dname != pdname:
        log("Wrong directory name, expected: '" + pdname + "' - rename", 4)
        full_pdname = os.path.join(os.path.dirname(path), pdname)
        os.rename(path, full_pdname)

def check_mp3_tags(full_path, e):

    t = {} # "proper" tags

    tags = ID3(full_path)

    if tags.version != (2, 3, 0):
        e.append("Incorrect ID3v2 version: '" + ".".join(map(str, tags.version)) + "' - change")

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

    if not 'APIC:' in tags:
        e.append("Cover missing - add")

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
    if clean_id3v1:
        e = clean_id3v1_tags(full_path, t, e)

    # Format multiple artists in single track
    if " / " in t['artist']:
        t['artist'] = t['artist'].replace(" / ", ", ")

    return t, e

def reset_mp3_tags(full_path):

    path = os.path.dirname(full_path)
    fname = os.path.basename(full_path)

    subprocess.call(['id3', '-21d', '-alnty', '%a', '%l', '%n', '%t', '%y', fname.encode('cp1252')], cwd=path.encode('cp1252'))

def reset_flac_tags(full_path):

    f = FLAC(full_path)

    t = f.tags

    # we need to save the 'vendor' string because calling mutagen's delete() removes it too
    for block in list(f.metadata_blocks):
        if isinstance(block, VCFLACDict):
            vendor = block.vendor

    f.clear_pictures()

    f.delete()

    for item in 'artist', 'album', 'tracknumber', 'tracktotal', 'title', 'date':
        if item in t:
            f[item] = t[item]

    for block in list(f.metadata_blocks):
        if isinstance(block, VCFLACDict):
            block.vendor = vendor

    f.save(deleteid3=True)

def check_flac_tags(full_path, e):

    t = {} # "proper" tags

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

def determine_quality(path, ext):

    if ext == 'flac':
        return 'FLAC'

    full_path = find_first(path, 'mp3')

    try:
        info = MPEGInfo(open(full_path, 'rb'))
    except:
        # this means the file is missing its MPEG header!
        return 'ERROR'

    if info.lame_preset:
        # possible presets: '-r3mix' (!), '-ap[msxi]' '-apf[msx]', '-b 320' and '-V[0-9n]'
        # the strip() takes care of all unwanted characters
        return info.lame_preset.strip('-bn ').upper()
    else:
        # TODO: needs testing
        #return str(info.bitrate / 1000) + 'KB'
        return 'UNK'

def check_cover(path):

    cover = find_first(path, 'jpg')

    if not cover:
        log("No cover image found", 4)
        return

    width, height = jpeg_dimensions(cover)

    if (width < 600) and (height < 600):
        log("Cover image too small: "  + str(width) + "x" + str(height), 4)
        return

    if (width > 600) and (height > 600):
        log("Cover image too large: "  + str(width) + "x" + str(height), 4)
        return

def jpeg_dimensions(jpeg):

    # adapted from
    # https://code.google.com/p/bfg-pages/source/browse/trunk/pages/getimageinfo.py

    width = -1
    height = -1

    jpeg = open(jpeg, 'rb')

    if jpeg.read(2) == '\377\330':

        b = jpeg.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = jpeg.read(1)
                while (ord(b) == 0xFF): b = jpeg.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    jpeg.read(3)
                    h, w = struct.unpack(">HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
                b = jpeg.read(1)
            width = int(w)
            height = int(h)
        except struct.error:
            pass
        except ValueError:
            pass

    return width, height

def find_first(path, ext):

    for filename in os.listdir(path):
        if filename.lower().endswith('.' + ext):
            return os.path.join(path, filename)

def rename_extras(path, t):

    base = os.path.join(path, safe_fname("00 " + (t['albumartist'] or t['artist']) + " - " + t['album']))

    for item, ext in {'cover': 'jpg', 'cuesheet': 'cue', 'log file': 'log'}.items():
        fname = find_first(path, ext)
        pname = base + "." + ext
        if fname and fname != pname:
            log("Wrong " + item + " name, expected: '" + os.path.basename(pname) + "' - rename", 4)
            try:
                os.rename(fname, pname)
            except:
                # TODO: better error message
                log("An error ocurred during renaming", 8)

def safe_fname(fname):

    fname, subs = invalid_chars.subn(' ', fname)
    while subs != 0:
        fname, subs = invalid_chars.subn(' ', fname)

    return string.strip(fname)

def safe_dname(t):

    artist  = t['albumartist'] or t['artist']
    album   = t['album']
    if t['discnumber']:
        album += " (Disc " + t['discnumber'] + ")"
    quality = t['quality']

    for article in articles:
        index = string.find(artist, article)
        if index == 0:
            artist = string.replace(artist, article, "", 1) + ", " + article

    return "[" + safe_fname(artist) + "] [" + safe_fname(album) + "] [" + quality + "]"

def check_unallowed_pattern(item, value, e):

    if value == None:
        return e

    pos = 0
    for desc, pat in unallowed_patterns.items():
        match = pat.search(value, pos)
        while match != None:
            pos = match.start() + 1
            e.append("Unallowed pattern in '" + item + "': " + desc + " at/near position " + str(pos) + " - correct")
            match = pat.search(value, pos)

    return e

def log(msg, lvl=0):

    print " " * lvl + msg.encode(encoding, 'replace')

# MP3 tags allowed
mp3_allow = ['TPE1', # artist
             'TALB', # album
             'TPOS', # discnumber/disctotal
             'TRCK', # tracknumber/tracktotal
             'TIT2', # title
             'TDRC', # date
             'TPE2', # albumartist
             'APIC:',# cover
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
              'albumartist',
              'replaygain_album_gain',
              'replaygain_track_gain',
              'replaygain_album_peak',
              'replaygain_track_peak']

articles = ['The ', 'El ', 'La ', 'Los ', 'Las ']

invalid_chars = re.compile(r':|\*|<|>|\||\?|\\|/|"|\$|  ')

unallowed_patterns = {"leading space": re.compile(r'^\s+'),
                      "two or more contiguous spaces": re.compile(r'\s{2,}'),
                      "initial lowercase letter": re.compile(r'^[a-z]|\s[a-z]')}

reset_tags = False
clean_id3v1 = False

if __name__ == '__main__':

    log("AudioRenamer - It renames audio files")
    log("")

    if '--reset' in sys.argv:
        if raw_input("Are you sure you want to reset tags? Press ENTER to confirm ") != "":
            sys.exit(0)
        reset_tags = True
        sys.argv.remove('--reset')

    if '--clean-id3v1' in sys.argv:
        clean_id3v1 = True
        sys.argv.remove('--clean-id3v1')

    if len(sys.argv) == 1:
        log("Usage: " + os.path.basename(sys.argv[0]) + "[--reset] <directories>")
        sys.exit(0)

    start = datetime.datetime.now()

    for arg in sys.argv[1:]:
        main(arg)

    log("")
    log("Process complete. Excecution time: " + str(datetime.datetime.now() - start), 2)
    log("")
    raw_input("Press ENTER to exit ")
