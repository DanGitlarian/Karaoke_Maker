@echo off
::Enable venv
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\activate.bat

::This file requires the .json to be done, and is meant for fixing things afterwards,
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe lyric_align.py
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe diff_engine.py

::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe json_to_karaoke.py ::turns json lyrics file into .ass lyric file

::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe generate_vocal_chunks.py
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe chunks_to_karaoke.py 

::Takes timestamped_lyrics.txt turns it into json
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe timestamped_to_json.py
::Takes json and turns it into .ass
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe chunks_to_karaoke.py 


::Turns timestamped_lyrics.txt to ass file 
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe timestamped_to_ass.py

::Creates a video with a stopwatch as the visual.
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe time_karaoke_videos.py

::C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe make_karaoke_videos.py ::makes a video that is the full music video whith karaoke lyrics using ffmpeg
::C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe finalize_karaoke.py ::creates the music video without vocals

echo all done!  
pause