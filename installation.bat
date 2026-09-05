setx GENIUS_API_TOKEN "Iy0Ha58dtic6oZiA3IYODuieQmxJjlueugBwFPw9loAhBlUeVr3lTgrirz61fY9M"

cd C:\Programs\Karaoke_Maker

python -m venv lyrics-transcriber-venv --copies
call lyrics-transcriber-venv\Scripts\activate.bat

python -m pip install --upgrade pip setuptools wheel

python -m pip install lyrics-transcriber
python -m spacy download en_core_web_sm

python -m pip install pylrc python-levenshtein

echo ALL DONE
pause
