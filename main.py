import os
import fnmatch
import sys

from file_list import *

def main():

    root = "Y:\\music\\files"
    exts = ["mp3", "flac"]

    print "loading files... ",
    file_list = load_file_list(root, exts)
    print "done"
    
    print "parsing files... ",
    process_file_list(file_list)
    print "done"


def analyze_file(file_path, ext):

    invalid_tags = set(file_tags.keys()).difference(allow_tags)
    if invalid_tags:
        print "Invalid tags on file '" + file_path + "'"
        for item in invalid_tags:
            print "  " + item + ": " + str(file_tags[item][0]).decode(encoding, 'replace')


if __name__ == '__main__':
    main()
