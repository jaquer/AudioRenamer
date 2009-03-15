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
