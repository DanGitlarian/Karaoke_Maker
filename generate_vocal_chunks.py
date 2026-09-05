import os
import json
import re

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def split_segment_by_length(words, limit=40):
    """
    Evaluates words of a single natural segment line.
    Returns a list of chunks, splitting ONLY if text > 40 chars.
    Favors splitting right after a punctuation mark (. , ! ? : ;) 
    as long as both split parts remain within the character limit.
    """
    full_text = " ".join([w['word'] for w in words])
    
    if len(full_text) <= limit:
        return [words]
        
    mid_point = len(full_text) // 2
    best_space_idx = -1
    min_dist = float('inf')
    found_punctuation_split = False

    # Track structural character position while iterating through words
    accumulated_len = 0
    
    for i in range(len(words) - 1):
        word_text = words[i]['word']
        # The potential split position is the space immediately after this word
        space_idx = accumulated_len + len(word_text)
        
        # Calculate lengths of the resulting left and right substrings
        left_sub_len = space_idx
        right_sub_len = len(full_text) - (space_idx + 1)
        
        # Check if this word ends with a punctuation mark
        has_punctuation = bool(re.search(r'[.,!?路径:;]$', word_text)) or (word_text and word_text[-1] in '.,!?路径:;')
        
        if has_punctuation and left_sub_len <= limit and right_sub_len <= limit:
            # Punctuation splits take absolute priority. Find the one closest to the center.
            dist = abs(space_idx - mid_point)
            if not found_punctuation_split or dist < min_dist:
                min_dist = dist
                best_space_idx = space_idx
                found_punctuation_split = True
                
        # Fallback whitespace tracker if no punctuation points meet the constraint yet
        if not found_punctuation_split:
            dist = abs(space_idx - mid_point)
            if dist < min_dist:
                min_dist = dist
                best_space_idx = space_idx
                
        accumulated_len += len(word_text) + 1  # Add 1 to account for the space character
        
    if best_space_idx == -1:
        return [words]
        
    left_words = []
    right_words = []
    current_char_count = 0
    
    for w in words:
        if current_char_count <= best_space_idx:
            left_words.append(w)
        else:
            right_words.append(w)
        current_char_count += len(w['word']) + 1
        
    return [left_words, right_words]

def run_chunk_generator():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: {ROOT_DIR} folder path not found.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if not os.path.isdir(song_dir):
            continue
            
        genius_path = os.path.join(song_dir, "genius_vocals.json")
        standard_path = os.path.join(song_dir, "vocals.json")
        
        target_json = genius_path if os.path.exists(genius_path) else standard_path
        if not os.path.exists(target_json):
            continue
            
        print(f"Creating vocal_chunks.json from {os.path.basename(target_json)} for: {item}")
        
        with open(target_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        flat_chunks = []
        for segment in data.get('segments', []):
            words = segment.get('words', [])
            if not words:
                continue
                
            # Process segment line strictly independent from neighbors
            split_results = split_segment_by_length(words, limit=40)
            for chunk_words in split_results:
                if chunk_words:
                    flat_chunks.append({
                        "start": chunk_words[0]["start"],
                        "end": chunk_words[-1]["end"],
                        "text": " ".join([w["word"] for w in chunk_words]),
                        "words": chunk_words
                    })
                    
        output_path = os.path.join(song_dir, "vocal_chunks.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"lines": flat_chunks}, f, indent=4, ensure_ascii=False)
        print(f" -> Successfully saved: {output_path}")

if __name__ == "__main__":
    run_chunk_generator()