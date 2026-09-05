import os
import json
import re

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def parse_timestamped_line(line):
    """
    Parses a single line from timestamped_lyrics.txt.
    Example input format: "Hello(0.122)(0.256) world(0.256)(0.600)nl"
    Or with empty placeholders: "Hello()() world()()nl"
    """
    line = line.strip()
    if not line:
        return None
        
    # Strip the trailing 'nl' end-of-line signifier
    if line.endswith("nl"):
        line = line[:-2].strip()
        
    if not line:
        return None

    # Matches word text followed by two sets of parentheses (with floats or empty inside)
    # e.g., "Hello(0.122)(0.256)" or "world()()"
    word_pattern = re.compile(r"([^\s\(\)]+)\((.*?)\)\((.*?)\)")
    matches = word_pattern.findall(line)
    
    words_list = []
    
    for word_text, start_val, end_val in matches:
        word_entry = {"word": word_text}
        
        # If timestamps are valid floats, convert them. Otherwise, leave them out or use None
        if start_val.strip() and end_val.strip():
            try:
                word_entry["start"] = float(start_val)
                word_entry["end"] = float(end_val)
            except ValueError:
                pass # Fallback to untimed if float conversion fails
                
        words_list.append(word_entry)
        
    if not words_list:
        return None

    # Extract overall line timestamps based on the first and last timed words
    timed_starts = [w["start"] for w in words_list if "start" in w]
    timed_ends = [w["end"] for w in words_list if "end" in w]
    
    line_start = timed_starts[0] if timed_starts else 0.0
    line_end = timed_ends[-1] if timed_ends else 0.0

    # Reconstruct the clean raw text sentence for the line level
    line_text = " ".join([w["word"] for w in words_list])

    return {
        "start": line_start,
        "end": line_end,
        "text": line_text,
        "words": words_list
    }

def convert_timestamped_lyrics_to_json(song_dir):
    input_path = os.path.join(song_dir, "timestamped_lyrics.txt")
    output_path = os.path.join(song_dir, "vocal_chunks_from_txt.json")
    
    if not os.path.exists(input_path):
        return

    print(f"Converting timestamped text to JSON for: {os.path.basename(song_dir)}")

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    json_lines = []
    for line in lines:
        parsed_line = parse_timestamped_line(line)
        if parsed_line:
            json_lines.append(parsed_line)

    # Save format to exactly mimic structural architecture of vocal_chunks.json
    output_data = {"lines": json_lines}

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
        
    print(f" -> Successfully created: {output_path}")

def process_all_songs():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Directory {ROOT_DIR} not found.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            convert_timestamped_lyrics_to_json(song_dir)

if __name__ == "__main__":
    process_all_songs()