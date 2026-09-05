import os
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

import torch
import numpy as np
import torchaudio
import json
import gc
import whisperx

# Compatibility Hacks
np.NaN = np.nan 
if not hasattr(torchaudio, 'AudioMetaData'):
    import torchaudio.backend.common
    torchaudio.AudioMetaData = torchaudio.backend.common.AudioMetaData

# --- CONFIGURATION ---
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu" 
COMPUTE_TYPE = "float16" 
MODEL_SIZE = "large-v3" #
BATCH_SIZE = 16 

def process_songs():
    print(f"--- Starting Bulk Transcription on {DEVICE} ---")
    
    # 1. Load Model with custom VAD parameters
    # vad_options: we lower the 'v_offset' to prevent it from cutting off ends of words
    print(f"Loading WhisperX model ({MODEL_SIZE})...")
    model = whisperx.load_model(
        MODEL_SIZE, 
        DEVICE, 
        compute_type=COMPUTE_TYPE,
        vad_options={
            "vad_onset": 0.300, # Start detecting earlier
            "vad_offset": 0.100, # Stop detecting much later (keeps trailing notes)
        }
    )

    for song_folder in os.listdir(ROOT_DIR):
        folder_path = os.path.join(ROOT_DIR, song_folder)
        if os.path.isdir(folder_path):
            vocal_path = os.path.join(folder_path, "vocals.wav")
            output_json = os.path.join(folder_path, "vocals.json")

            if os.path.exists(vocal_path) and not os.path.exists(output_json):
                print(f"\nProcessing: {song_folder}")
                try:
                    audio = whisperx.load_audio(vocal_path)
                    
                    # A. Transcribe with relaxed chunking
                    # We want Whisper to consider melodic sections as speech
                    result = model.transcribe(audio, batch_size=BATCH_SIZE)

                    # B. Align with NO interpolation (Forces phoneme-level accuracy)
                    model_a, metadata = whisperx.load_align_model(
                        language_code=result["language"], device=DEVICE
                    )
                    
                    # align() changes: 
                    # We keep return_char_alignments=False but rely on the Wav2Vec2 
                    # model's ability to "see" the vibration of the vocals
                    result = whisperx.align(
                        result["segments"], 
                        model_a, 
                        metadata, 
                        audio, 
                        DEVICE, 
                        return_char_alignments=False
                    )

                    with open(output_json, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=4)
                    
                    print(f"Successfully created: {output_json}")

                    del model_a
                    gc.collect()
                    torch.cuda.empty_cache()

                except Exception as e:
                    print(f"Error processing {song_folder}: {e}")

    print("\n--- All items processed ---")

if __name__ == "__main__":
    process_songs()