import os
# Force PyTorch to bypass the strict 'weights_only' security block on load
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

import torch
import numpy as np
import torchaudio
import json
import gc
import whisperx

# --- COMPATIBILITY HACKS ---
np.NaN = np.nan 
if not hasattr(torchaudio, 'AudioMetaData'):
    import torchaudio.backend.common
    torchaudio.AudioMetaData = torchaudio.backend.common.AudioMetaData

# Overwrite torch.load globally to force-disable weights_only (fixes pyannote / omegaconf issues)
_original_load = torch.load
torch.load = lambda *args, **kwargs: _original_load(*args, {**kwargs, "weights_only": False})

# --- CONFIGURATION ---
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu" 
COMPUTE_TYPE = "float16" 

# Use your local manually-downloaded CTranslate2 model directory directly!
MODEL_SIZE = r"C:\Programs\Karaoke_Maker\models\faster-whisper-large-v2"

BATCH_SIZE = 16 
FORCE_ENGLISH = True

def regroup_words_into_lines(words, max_words=8, max_gap_seconds=1.2):
    """
    Takes a flat list of aligned words and groups them into clean lines
    based on word count limits and silence gaps.
    """
    lines = []
    current_line_words = []
    
    # Filter out obvious silence-hallucinations (low score + specific patterns)
    filtered_words = []
    for w in words:
        if w.get("word", "").strip().lower() in ["thank", "you", "subtitles", "amara"] and w.get("score", 1.0) < 0.35:
            continue
        filtered_words.append(w)

    for i, word_data in enumerate(filtered_words):
        if not current_line_words:
            current_line_words.append(word_data)
            continue
        
        prev_word = current_line_words[-1]
        gap = word_data["start"] - prev_word["end"] if "start" in word_data and "end" in prev_word else 0
        
        if len(current_line_words) >= max_words or gap > max_gap_seconds:
            line_text = " ".join([w["word"] for w in current_line_words])
            lines.append({
                "start": current_line_words[0]["start"],
                "end": current_line_words[-1]["end"],
                "text": line_text,
                "words": current_line_words
            })
            current_line_words = [word_data]
        else:
            current_line_words.append(word_data)
            
    if current_line_words:
        line_text = " ".join([w["word"] for w in current_line_words])
        lines.append({
            "start": current_line_words[0]["start"],
            "end": current_line_words[-1]["end"],
            "text": line_text,
            "words": current_line_words
        })
        
    return lines

def get_audio_duration(file_path):
    """Gets the duration of the audio file in seconds using torchaudio."""
    info = torchaudio.info(file_path)
    return info.num_frames / info.sample_rate

def process_songs():
    print(f"--- Starting Bulk Transcription/Alignment on {DEVICE} ---")
    
    if not os.path.exists(ROOT_DIR):
        print(f"ERROR: The root directory does not exist: {ROOT_DIR}")
        return

    items = os.listdir(ROOT_DIR)
    if not items:
        print(f"WARNING: The root directory is completely empty: {ROOT_DIR}")
        return

    # Verify our local model directory exists before starting
    if not os.path.exists(MODEL_SIZE):
        print(f"ERROR: Local model path was not found: {MODEL_SIZE}")
        print("Please ensure the model is downloaded and located in that exact directory.")
        return

    # We load models lazily only when we actually have folders to process!
    whisper_model = None 

    for song_folder in items:
        folder_path = os.path.join(ROOT_DIR, song_folder)
        
        if not os.path.isdir(folder_path):
            continue
            
        vocal_path = os.path.join(folder_path, "vocals.wav")
        output_json = os.path.join(folder_path, "vocals.json")
        lyrics_path = os.path.join(folder_path, "lyrics.txt")

        # 1. Skipped warnings
        if os.path.exists(output_json):
            print(f"Skipping '{song_folder}': vocals.json already exists.")
            continue

        if not os.path.exists(vocal_path):
            print(f"Skipping '{song_folder}': Could not find '{vocal_path}'")
            continue

        print(f"\nProcessing: {song_folder}")
        try:
            audio = whisperx.load_audio(vocal_path)
            segments = []
            detected_language = "en"

            # Check if we have ground-truth lyrics to bypass transcription
            if os.path.exists(lyrics_path):
                print(f"Found 'lyrics.txt'. Using custom text alignment (bypassing model transcription)...")
                with open(lyrics_path, "r", encoding="utf-8") as f:
                    clean_lyrics = f.read().replace("\n", " ").strip()
                
                duration = get_audio_duration(vocal_path)
                
                # Mock up a single segment covering the entire audio duration containing the raw text
                segments = [{
                    "start": 0.0,
                    "end": duration,
                    "text": clean_lyrics
                }]
            else:
                # No lyrics found, proceed with regular Whisper transcription
                if whisper_model is None:
                    print(f"Loading local WhisperX model from: {MODEL_SIZE}...")
                    whisper_model = whisperx.load_model(
                        MODEL_SIZE, 
                        DEVICE, 
                        compute_type=COMPUTE_TYPE,
                        vad_options={
                            "vad_onset": 0.500,
                            "vad_offset": 0.363,
                        }
                    )
                
                print("Transcribing with Whisper...")
                transcribe_args = {"batch_size": BATCH_SIZE}
                if FORCE_ENGLISH:
                    transcribe_args["language"] = "en"
                
                result = whisper_model.transcribe(audio, **transcribe_args)
                segments = result["segments"]
                detected_language = result["language"]

            # Load align model and force align the text (either transcribed or ground-truth)
            print("Aligning phonemes to audio...")
            model_a, metadata = whisperx.load_align_model(
                language_code=detected_language, device=DEVICE
            )
            
            result = whisperx.align(
                segments, 
                model_a, 
                metadata, 
                audio, 
                DEVICE, 
                return_char_alignments=False
            )

            # Regroup words into nicely sized lines for Karaoke
            if "word_segments" in result and result["word_segments"]:
                print("Regrouping words into clean karaoke-style lines...")
                reconstructed_segments = regroup_words_into_lines(
                    result["word_segments"], 
                    max_words=7,
                    max_gap_seconds=1.0
                )
                result["segments"] = reconstructed_segments

            # Save results
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4)
            
            print(f"Successfully created: {output_json}")

            # Clean up alignment model from memory
            del model_a
            gc.collect()
            torch.cuda.empty_cache()

        except Exception as e:
            print(f"Error processing {song_folder}: {e}")

    print("\n--- All items processed ---")

if __name__ == "__main__":
    process_songs()