@echo off
::Enable venv
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\activate.bat

::This file makes the .json file better using the official lyrics in a lyrics.txt file 
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe lyric_align.py
:: I think this one is bad



::timestamp_starter will create a bunch of lyrics + empty timestamps in empty_lyrics.txt
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe timestamp_starter.py
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe timestamp_filler.py

::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe diff_engine.py
::C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe words_in_vocals.py
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe diff_engine.py

::!!!! assign_lyrics will create timestamped_lyrics.txt using previous methods !!!!
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe assign_lyrics.py




::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe generate_genius_json.py
::call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe generate_vocal_chunks.py
echo all done!  
pause