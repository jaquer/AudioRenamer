# file_list.py - analyze dirs, looking for files and list them

from os import path
import fnmatch

from tags import *


def load_file_list(root, exts):

    file_list = {}

    for path, dirs, files in os.walk(root):
        for ext in exts:
            if ext not in file_list:
                file_list[ext] = {}
            for fname in fnmatch.filter(files, "*." + ext):
                if path not in file_list[ext]:
                    file_list[ext][path] = {}
                full_path = os.path.join(path, fname)
                #print "Loading into list: '" + full_path + "'"
                file_list[ext][path][fname] = {}
        
    return file_list

def parse_file_list(file_list):

    for ext in file_list.iterkeys():
        for path in file_list[ext].iterkeys():
            for fname in file_list[ext][path].iterkeys():
                full_path = os.path.join(path, fname)
                #print "Reading tags from: '" + full_path + "'"
                file_list[ext][path][fname] = read_tags(full_path, ext)

    return file_list

if __name__ == '__main__':

    exts = ["mp3", "flac"]

    root = "Y:\\music\\files\\[2 Unlimited] [Hits Unlimited] [APS]"
    root = "Y:\\music\\collection\\2Pac"
    

    file_list = load_file_list(root, exts)
    print parse_file_list(file_list)

"""
    for path in file_list['mp3'].iterkeys():
        for fname in file_list['mp3'][path].iterkeys():
            print fname
            print file_list['mp3'][path][fname]
"""
