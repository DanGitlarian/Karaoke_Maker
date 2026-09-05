@echo off


::initiation start 
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\activate.bat
::call C:\Programs\Karaoke_Maker\lyrics-transcriber-venv\Scripts\activate.bat
::C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe preprocess_filenames.py  ::Useful to get rid of (Music video ) Official etc...  

::!!!IMPORTANT FOR SEPARATING
::python "C:\Programs\Karaoke_maker\separator.py"
robocopy "C:\Programs\Karaoke_Maker\vocal-separate-v0.0.4\static\files" "C:\Programs\Karaoke_Maker\Songs\input" /E /MOVE

:: Makes json
::C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe bulk_transcribe.py 

::Makes json with forced lyrics
C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe transcribe_lyrics.py

::We need a song_video.mp4 added to input/songname
C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe organize_songs.py 
::from here you can edit this

C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe generate_vocal_chunks.py :: chunks up vocals.json
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe chunks_to_karaoke.py :: turns chunks to karaoke ass file. These two or the one below.
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe json_to_karaoke.py ::turns json lyrics file into .ass lyric file

C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe make_karaoke_videos.py ::makes a video that is the full music video whith karaoke lyrics using ffmpeg
::C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe finalize_karaoke.py ::creates the music video without vocals

pause