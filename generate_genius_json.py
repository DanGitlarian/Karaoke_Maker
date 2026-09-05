import os
import json
import re

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def clean_only_letters(text):
    """Returns pure alphanumeric character tokens for length calculation."""
    return re.sub(r'[^\w]', '', text)

def parse_json_lyric_file(filepath):
    """Parses json_lyric.txt file back into a list of word dictionaries with timestamps."""
    words = []
    if not os.path.exists(filepath):
        return words
        
    pattern = r"^(.+?)\s+\(([0-9.]+?)\)\s+\(([0-9.]+?)\)$"
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = re.match(pattern, line)
            if match:
                words.append({
                    "word": match.group(1).strip(),
                    "start": float(match.group(2)),
                    "end": float(match.group(3))
                })
    return words

def parse_lyric_diff_file(filepath):
    """Parses lyric_diff.txt, extracting groupings separated by <br>."""
    lines_data = []
    if not os.path.exists(filepath):
        return lines_data
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split blocks via the line break tags
    raw_blocks = content.split("<br>")
    
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
            
        # Match lines like: b (Audio phrase here) [Target1] [Target2]
        match = re.match(r"^[rpb]\s+\((.*?)\)\s+(.*)$", block)
        if match:
            audio_phrase_str = match.group(1).strip()
            targets_str = match.group(2).strip()
            
            # Find all words enclosed inside square brackets []
            target_words = re.findall(r"\[(.*?)\]", targets_str)
            if target_words:
                lines_data.append({
                    "audio_str": audio_phrase_str,
                    "targets": target_words
                })
    return lines_data

def distribute_proportional_times(targets, total_start, total_end):
    """Distributes words over a span proportionally based on character length plus space padding."""
    words_out = []
    if total_start is None or total_end is None or total_start >= total_end:
        # Fallback values if timestamps are corrupt
        total_start, total_end = 0.0, 1.0
        
    total_duration = total_end - total_start
    
    # Calculate character lengths (with a virtual space added between words)
    word_lengths = [max(1, len(clean_only_letters(w))) for w in targets]
    # Add 1 space weight between words
    weights = [l + 1 for l in word_lengths]
    if weights:
        weights[-1] -= 1 # Remove trailing space padding on final word
        
    total_weight = sum(weights)
    if total_weight == 0:
        total_weight = 1

    current_time = total_start
    for idx, word in enumerate(targets):
        w_dur = (weights[idx] / total_weight) * total_duration
        w_start = round(current_time, 3)
        w_end = round(current_time + w_dur, 3)
        
        words_out.append({
            "word": word,
            "start": w_start,
            "end": w_end
        })
        current_time += w_dur
        
    return words_out

def run_genius_json_generator():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Directory {ROOT_DIR} not found.")
        return

    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if not os.path.isdir(song_dir):
            continue
            
        json_lyric_path = os.path.join(song_dir, "json_lyric.txt")
        lyric_diff_path = os.path.join(song_dir, "lyric_diff.txt")
        
        if not os.path.exists(json_lyric_path) or not os.path.exists(lyric_diff_path):
            continue
            
        print(f"Generating structured genius_vocals.json for song: {item}")
        
        audio_stream = parse_json_lyric_file(json_lyric_path)
        diff_lines = parse_lyric_diff_file(lyric_diff_path)
        
        final_segments = []
        audio_idx = 0
        
        for line in diff_lines:
            targets = line["targets"]
            audio_tokens = line["audio_str"].split()
            num_audio = len(audio_tokens)
            
            # Consume matching tokens from the original timestamp stream
            line_audio_words = audio_stream[audio_idx : audio_idx + num_audio]
            audio_idx += num_audio
            
            if not line_audio_words:
                continue
                
            line_start = line_audio_words[0]["start"]
            line_end = line_audio_words[-1]["end"]
            
            # Scenario A: Words are completely replaced or count mismatch (e.g. 2 audio words -> 7 lyric words)
            if num_audio != len(targets):
                processed_words = distribute_proportional_times(targets, line_start, line_end)
            
            # Scenario B: Word count is identical, check inside for sub-splits or multi-word targets
            else:
                processed_words = []
                for i, target_word in enumerate(targets):
                    src_w = line_audio_words[i]
                    
                    # Split logic handling sub-words mapping or dash merges
                    # Example: audio word 'easy' maps to target array entry 'easy, no'
                    sub_targets = target_word.split('-') if '-' in target_word and not target_word.startswith('-') else [target_word]
                    
                    # Also handle fallback spaces inside single target brackets
                    sub_targets = [st.strip() for st in target_word.split() if st.strip()]
                    
                    if len(sub_targets) > 1:
                        sub_splits = distribute_proportional_times(sub_targets, src_w["start"], src_w["end"])
                        processed_words.extend(sub_splits)
                    else:
                        processed_words.append({
                            "word": target_word,
                            "start": src_w["start"],
                            "end": src_w["end"]
                        })

            # Append structural array line container item
            final_segments.append({
                "start": processed_words[0]["start"] if processed_words else line_start,
                "end": processed_words[-1]["end"] if processed_words else line_end,
                "text": " ".join(targets),
                "words": processed_words
            })

        # Save structured vocals output file
        output_json_path = os.path.join(song_dir, "genius_vocals.json")
        output_data = {"segments": final_segments}
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
            
        print(f" -> Successfully exported: {output_json_path}")

if __name__ == "__main__":
    run_genius_json_generator()