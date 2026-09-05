import os
import re

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def parse_json_lyrics(json_lyric_content):
    """
    Parses json_lyric.txt into a list of dictionaries with word and timestamps.
    Handles lines like: 'Thank (2.444) (9.332)' or words without timestamps.
    """
    timed_words = []
    # Regex to capture word string and its opening/closing float timestamps if they exist
    pattern = re.compile(r"^(.+?)(?:\s+\((\d+\.\d+)\)\s+\((\d+\.\d+)\))?$", re.MULTILINE)
    
    for match in pattern.finditer(json_lyric_content):
        raw_word = match.group(1).strip()
        if not raw_word:
            continue
        
        start_t = match.group(2)
        end_t = match.group(3)
        
        # Clean up any trailing structural artifacts if present in text extraction
        clean_word = re.sub(r"[\[\]\(\)]", "", raw_word).strip()
        
        timed_words.append({
            "word": clean_word,
            "start": f"({start_t})" if start_t else "()",
            "end": f"({end_t})" if end_t else "()"
        })
    return timed_words

def clean_token(text):
    """Normalizes words for standard alignment comparisons."""
    return re.sub(r"[^\w]", "", text).lower()

def align_song_lyrics(song_dir):
    json_lyric_path = os.path.join(song_dir, "json_lyric.txt")
    lyrics_path = os.path.join(song_dir, "lyrics.txt")
    output_path = os.path.join(song_dir, "timestamped_lyrics.txt")
    
    if not os.path.exists(json_lyric_path) or not os.path.exists(lyrics_path):
        return

    print(f"Aligning lyric maps for folder: {os.path.basename(song_dir)}")

    with open(json_lyric_path, 'r', encoding='utf-8') as f:
        json_content = f.read()
        
    with open(lyrics_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    timed_words = parse_json_lyrics(json_content)
    word_idx = 0
    total_timed_words = len(timed_words)
    
    output_lines = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            # Keep natural empty structural lines clean
            continue
            
        line_words = line.split()
        formatted_line_parts = []
        
        for word in line_words:
            cleaned_target = clean_token(word)
            
            # Simple fallback match logic lookahead alignment loop
            matched = False
            # Check up to next 5 tokens to protect alignment syncing against tracking hiccups
            for lookahead in range(min(5, total_timed_words - word_idx)):
                current_check_idx = word_idx + lookahead
                if clean_token(timed_words[current_check_idx]["word"]) == cleaned_target:
                    # Advanced index tracker to match positions
                    word_idx = current_check_idx
                    formatted_line_parts.append(f"{word}{timed_words[word_idx]['start']}{timed_words[word_idx]['end']}")
                    word_idx += 1
                    matched = True
                    break
            
            # If alignment misses or timing data ran dry early, assign empty placeholders
            if not matched:
                if word_idx < total_timed_words:
                    # Fallback to current token alignment step if text mismatches slightly
                    formatted_line_parts.append(f"{word}{timed_words[word_idx]['start']}{timed_words[word_idx]['end']}")
                    word_idx += 1
                else:
                    formatted_line_parts.append(f"{word}()()")

        # Joint line words together with a space, then attach the end-of-line 'nl' signifier
        final_line = " ".join(formatted_line_parts) + "nl"
        output_lines.append(final_line)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines) + "\n")
        
    print(f" -> Successfully exported: {output_path}")

def process_all_songs():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Target path {ROOT_DIR} does not exist.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            align_song_lyrics(song_dir)

if __name__ == "__main__":
    process_all_songs()