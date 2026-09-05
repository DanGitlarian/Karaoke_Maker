import os
import json
import re
from difflib import SequenceMatcher

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def clean_word(word):
    """Removes punctuation and forces lowercase for better matching."""
    return re.sub(r'[^\w\s]', '', word).lower().strip()

def load_real_lyrics(txt_path):
    """Reads the ground truth lyrics text file safely if it exists."""
    if not os.path.exists(txt_path):
        return []
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def extract_json_words_and_segments(json_path):
    """Extracts both flat words and original reconstructed lines from the WhisperX JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flat_words = []
    whisper_lines = []
    
    for segment in data.get('segments', []):
        # Gather text lines exactly as Whisper paired them
        seg_text = segment.get('text', '').strip()
        if seg_text:
            whisper_lines.append(seg_text)
            
        for w in segment.get('words', []):
            flat_words.append({
                'word': w.get('word', '').strip(),
                'start': w.get('start', None),
                'end': w.get('end', None)
            })
    return flat_words, whisper_lines

def align_and_merge_global(real_lines, json_words):
    """Flattens everything and uses global anchors with two-way interpolation."""
    real_tokens = []
    token_to_line_map = []
    
    for line_idx, line in enumerate(real_lines):
        for word in line.split():
            real_tokens.append(word)
            token_to_line_map.append(line_idx)
            
    clean_real = [clean_word(w) for w in real_tokens]
    clean_json = [clean_word(w['word']) for w in json_words]
    
    matcher = SequenceMatcher(None, clean_real, clean_json)
    matching_blocks = matcher.get_matching_blocks()
    
    aligned_words = []
    for word_val, line_val in zip(real_tokens, token_to_line_map):
        aligned_words.append({
            'word': word_val,
            'start': None,
            'end': None,
            'line_idx': line_val
        })
    
    for block in matching_blocks:
        r_start, j_start, length = block
        for i in range(length):
            r_idx = r_start + i
            j_idx = j_start + i
            if r_idx < len(aligned_words) and j_idx < len(json_words):
                aligned_words[r_idx]['start'] = json_words[j_idx]['start']
                aligned_words[r_idx]['end'] = json_words[j_idx]['end']

    for i, w in enumerate(aligned_words):
        if w['start'] is not None:
            continue
            
        prev_time = None
        for j in range(i - 1, -1, -1):
            if aligned_words[j]['end'] is not None:
                prev_time = aligned_words[j]['end']
                break
                
        next_time = None
        for j in range(i + 1, len(aligned_words)):
            if aligned_words[j]['start'] is not None:
                next_time = aligned_words[j]['start']
                break

        if prev_time is not None and next_time is not None:
            w['start'] = prev_time + (next_time - prev_time) * 0.3
            w['end'] = prev_time + (next_time - prev_time) * 0.7
        elif prev_time is not None:
            w['start'] = prev_time + 0.2
            w['end'] = w['start'] + 0.3
        elif next_time is not None:
            w['start'] = max(0.0, next_time - 0.5)
            w['end'] = next_time - 0.2
        else:
            w['start'] = i * 0.4
            w['end'] = w['start'] + 0.3

    final_segments = []
    current_line_idx = -1
    current_words = []
    
    for w in aligned_words:
        if w['line_idx'] != current_line_idx:
            if current_words:
                final_segments.append({
                    "start": current_words[0]['start'],
                    "end": current_words[-1]['end'],
                    "text": real_lines[current_line_idx],
                    "words": current_words
                })
            current_words = []
            current_line_idx = w['line_idx']
            
        current_words.append({
            'word': w['word'],
            'start': round(w['start'], 3),
            'end': round(w['end'], 3)
        })
        
    if current_words:
        final_segments.append({
            "start": current_words[0]['start'],
            "end": current_words[-1]['end'],
            "text": real_lines[current_line_idx],
            "words": current_words
        })
        
    return {"segments": final_segments}

def process_all_songs():
    """Iterates through every subdirectory inside ROOT_DIR and aligns them."""
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Root directory {ROOT_DIR} does not exist.")
        return

    # Scan directories inside root path
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        
        if os.path.isdir(song_dir):
            json_data_path = os.path.join(song_dir, "vocals.json")
            txt_lyrics_path = os.path.join(song_dir, "lyrics.txt")
            
            # Skip folders that don't have vocal raw alignments
            if not os.path.exists(json_data_path):
                continue
                
            print(f"\nProcessing folder: {item}")
            
            # 1. Extract Whisper data
            json_words, whisper_lines = extract_json_words_and_segments(json_data_path)
            
            # 2. Write the json_lyric.txt file (Whisper's exact output phrases layout)
            json_lyric_txt_path = os.path.join(song_dir, "json_lyric.txt")
            with open(json_lyric_txt_path, "w", encoding="utf-8") as f:
                for line in whisper_lines:
                    f.write(line + "\n")
            print(f" -> Created structural raw layout: json_lyric.txt")
            
            # 3. Check for ground truth lyrics text file to perform timestamps generation
            if os.path.exists(txt_lyrics_path):
                txt_lyrics = load_real_lyrics(txt_lyrics_path)
                corrected_vocals_json = align_and_merge_global(txt_lyrics, json_words)
                
                output_json_path = os.path.join(song_dir, "matched_lyrics.json")
                with open(output_json_path, "w", encoding="utf-8") as f:
                    json.dump(corrected_vocals_json, f, indent=4, ensure_ascii=False)
                print(f" -> Generated timestamp configurations: matched_lyrics.json")
            else:
                print(f" -> Skipped timestamps matching: 'lyrics.txt' not found inside directory.")

if __name__ == "__main__":
    process_all_songs()
    print("\nBatch processing completed successfully!")