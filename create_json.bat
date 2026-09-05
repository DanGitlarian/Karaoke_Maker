@echo off
::initiation start 
call C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\activate.bat
C:\Programs\Karaoke_Maker\venv_whisperx\Scripts\python.exe bulk_transcribe.py :: Makes json
pause