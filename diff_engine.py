import os
import json
import re
from difflib import SequenceMatcher

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def normalize_token(word):
    """Normalizes words strictly for core matching (ignores punctuation, casing, and trailing g's)."""
    w = re.sub(r'[^\w\s]', '', word).lower().strip()
    if w.endswith('in'):
        w = w[:-2] + 'ing'
    return w

def fuzzy_word_match(w1, w2):
    """Returns True if words are strong fuzzy matches (e.g., 'ooh' vs 'ooh-ooh')."""
    nw1, nw2 = normalize_token(w1), normalize_token(w2)
    if not nw1 or not nw2:
        return False
    if nw1 in nw2 or nw2 in nw1:
        return True
    return SequenceMatcher(None, nw1, nw2).ratio() > 0.65

def parse_json_lyric_line(line):
    """Parses lines from json_lyric.txt: 'Word (start) (end)'."""
    line = line.strip()
    if not line:
        return None
    match = re.match(r"^(.+?)\s+\(([0-9.]+?)\)\s+\(([0-9.]+?)\)$", line)
    if match:
        word = match.group(1).strip()
        try:
            return {"word": word, "start": float(match.group(2)), "end": float(match.group(3))}
        except ValueError:
            pass
    return None

def find_longest_common_chunk(real_tokens, audio_tokens, r_start, r_end, a_start, a_end):
    """Finds the single largest continuous matching block of normalized tokens within bounds."""
    best_r_idx = -1
    best_a_idx = -1
    best_length = 0

    for r_idx in range(r_start, r_end):
        for a_idx in range(a_start, a_end):
            length = 0
            while (r_idx + length < r_end and a_idx + length < a_end and 
                   real_tokens[r_idx + length] == audio_tokens[a_idx + length]):
                length += 1
            
            if length > best_length:
                best_length = length
                best_r_idx = r_idx
                best_a_idx = a_idx

    return best_r_idx, best_a_idx, best_length

def run_diff_engine():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Directory {ROOT_DIR} not found.")
        return

    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if not os.path.isdir(song_dir):
            continue
            
        json_lyric_path = os.path.join(song_dir, "json_lyric.txt")
        txt_lyrics_path = os.path.join(song_dir, "lyrics.txt")
        
        if not os.path.exists(json_lyric_path) or not os.path.exists(txt_lyrics_path):
            continue
            
        print(f"Running core-anchor + boundary fine-tuning diff engine for: {item}")
        
        with open(txt_lyrics_path, 'r', encoding='utf-8') as f:
            raw_lyric_lines = [line.strip() for line in f if line.strip()]
            
        real_words_flat = []
        word_to_line_map = []
        for line_idx, line in enumerate(raw_lyric_lines):
            for w in line.split():
                real_words_flat.append(w)
                word_to_line_map.append(line_idx)

        audio_words = []
        with open(json_lyric_path, 'r', encoding='utf-8') as f:
            for line in f:
                parsed = parse_json_lyric_line(line)
                if parsed:
                    audio_words.append(parsed)
                    
        if not audio_words or not real_words_flat:
            continue

        norm_real = [normalize_token(w) for w in real_words_flat]
        norm_audio = [normalize_token(w['word']) for w in audio_words]

        mapped_audio_indices = [None] * len(real_words_flat)
        search_queue = [(0, len(real_words_flat), 0, len(audio_words))]

        # Phase 1: Macro Core Matching (unaltered massive chunks)
        while search_queue:
            r_s, r_e, a_s, a_e = search_queue.pop(0)
            if r_s >= r_e or a_s >= a_e:
                continue

            r_match, a_match, length = find_longest_common_chunk(norm_real, norm_audio, r_s, r_e, a_s, a_e)
            
            if length >= 2:
                for i in range(length):
                    mapped_audio_indices[r_match + i] = a_match + i
                
                search_queue.append((r_s, r_match, a_s, a_match))
                search_queue.append((r_match + length, r_e, a_match + length, a_e))

        # Phase 2: Local Boundary Micro Fine-Tuning (Fixes Ooh vs Ooh-ooh edge shifting)
        for i in range(len(real_words_flat)):
            if mapped_audio_indices[i] is None:
                # Look for adjacent anchored references to bound the search pocket
                prev_a = None
                for p in range(i - 1, -1, -1):
                    if mapped_audio_indices[p] is not None:
                        prev_a = mapped_audio_indices[p]
                        break
                
                next_a = None
                for n in range(i + 1, len(real_words_flat)):
                    if mapped_audio_indices[n] is not None:
                        next_a = mapped_audio_indices[n]
                        break
                
                a_start = prev_a + 1 if prev_a is not None else 0
                a_end = next_a if next_a is not None else len(audio_words)
                
                # Check if an unmatched audio token in this precise pocket matches fuzzily
                for a_idx in range(a_start, a_end):
                    if fuzzy_word_match(real_words_flat[i], audio_words[a_idx]['word']):
                        # Ensure no double assignment
                        if a_idx not in mapped_audio_indices:
                            mapped_audio_indices[i] = a_idx
                            break

        # Phase 3: Structural Reconstructor
        diff_output_lines = []
        current_audio_pointer = 0
        total_audio = len(audio_words)

        for line_idx, real_line in enumerate(raw_lyric_lines):
            real_words = real_line.split()
            line_word_indices = [i for i, l_idx in enumerate(word_to_line_map) if l_idx == line_idx]
            if not line_word_indices:
                continue

            start_flat_idx = line_word_indices[0]
            end_flat_idx = line_word_indices[-1]

            next_anchor_audio_idx = None
            for idx in range(end_flat_idx + 1, len(real_words_flat)):
                if mapped_audio_indices[idx] is not None:
                    next_anchor_audio_idx = mapped_audio_indices[idx]
                    break

            if next_anchor_audio_idx is not None:
                end_audio_idx = next_anchor_audio_idx
            else:
                end_audio_idx = total_audio

            if end_audio_idx < current_audio_pointer:
                end_audio_idx = current_audio_pointer

            mapped_audio_chunk = audio_words[current_audio_pointer:end_audio_idx]
            audio_phrase = " ".join([w['word'] for w in mapped_audio_chunk])

            # Apply 'bad-bad' squish conversion logic
            processed_real_words = []
            i = 0
            while i < len(real_words):
                w_clean = re.sub(r'[^\w\s]', '', real_words[i]).lower().strip()
                if (i < len(real_words) - 1 and w_clean == "bad" and 
                    re.sub(r'[^\w\s]', '', real_words[i+1]).lower().strip() == "bad"):
                    processed_real_words.append(f"{real_words[i]}-{real_words[i+1]}")
                    i += 2
                else:
                    processed_real_words.append(real_words[i])
                    i += 1

            bracketed_targets = " ".join([f"[{w}]" for w in processed_real_words])

            # Line Classification Check codes (r, b, p)
            clean_audio = re.sub(r'[^\w\s]', '', audio_phrase).lower().strip()
            clean_real = re.sub(r'[^\w\s]', '', real_line).lower().strip()
            has_anchor = any(mapped_audio_indices[i] is not None for i in line_word_indices)

            if "thank" in clean_audio and "thank" not in clean_real:
                line_type = "r"
            elif not has_anchor:
                line_type = "r"
            elif len(processed_real_words) > 4:
                line_type = "b"
            else:
                line_type = "p"

            diff_output_lines.append(f"{line_type} ({audio_phrase}) {bracketed_targets}")

            if line_idx < len(raw_lyric_lines) - 1:
                diff_output_lines.append("<br>")

            current_audio_pointer = end_audio_idx

        # Write final outputs
        lyric_diff_path = os.path.join(song_dir, "lyric_diff.txt")
        with open(lyric_diff_path, "w", encoding="utf-8") as f:
            for line in diff_output_lines:
                f.write(line + "\n")
                
        print(f" -> Generated Optimized Micro-Aligned Diff: {lyric_diff_path}")

if __name__ == "__main__":
    run_diff_engine()