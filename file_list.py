# file_list.py - analyze dirs, looking for files and list them

from os import path
import fnmatch

from tags import *
from constants import *

def load_file_list(root, exts):

    file_list = {}

    for path, dirs, files in os.walk(root):
        for ext in exts:
            if ext not in file_list:
                file_list[ext] = {}
            for fname in fnmatch.filter(files, "*." + ext):
                if path not in file_list[ext]:
                    file_list[ext][path] = []
                #full_path = os.path.join(path, fname)
                #print "Loading into list: '" + full_path + "'"
                file_list[ext][path].append(fname)
        
    return file_list

def process_file_list(file_list):

    for ext, paths in file_list.iteritems():
        for path, fnames in paths.iteritems():
            process_files(path, fnames, ext)

def process_files(path, fnames, ext):

    if ext == 'mp3':
        allow_tags = {'id3v2': id3v2_allow, 'id3v1': id3v1_allow}
    elif ext == 'flac':
        allow_tags = flac_allow

    for fname in fnames:
        full_path = os.path.join(path, fname)
         # read_tags(full_path, ext)

if __name__ == '__main__':

    exts = ["mp3", "flac"]

    root = "Y:\\music\\files\\[2 Unlimited] [Hits Unlimited] [APS]"
    root = "Y:\\music\\collection\\2Pac"
    

    file_list = load_file_list(root, exts)
    file_list = parse_file_list(file_list)

"""
    for path in file_list['mp3'].iterkeys():
        for fname in file_list['mp3'][path].iterkeys():
            print fname
            print file_list['mp3'][path][fname]
"""
