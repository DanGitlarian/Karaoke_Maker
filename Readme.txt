This is a combination of multiple apps,
To use it, put a song in Songs\input.
If this readme file isn't in C:\Programs\Karaoke_Maker you'll have to change either the directory or change the path in multiple batch/python files.
If you want to transcribe non-english songs, whisper is set up for understanding english words in lyric_syncer.py

INITIALIZATION
0. To begin use the installation.bat file 
Once this is done it never has to be done again.

1. To launch the necessary applications:
start.exe

Song -> karaoke automation
1. put songs into Songs\input 
2. Press Karaoke_Maker.bat
3. Currently have to put the song into the subfolder named song_video.mp4 After this Adjustments can be used for the next step.


ADJUSTMENTS
To make adjustments after the fact, use 
post_adjustment.bat			transcribe_all is an even more barebones editor thingy.
This requires manual editing of the .json file
To change the subtitle track properties such as letter color change the lyrics properties in:
json_to_karaoke.py 





