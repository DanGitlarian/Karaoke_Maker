import os
import json

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def process_all_songs():
    """Iterates through every subdirectory, extracts flat words, and generates a single column json_lyric.txt with timestamps."""
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Root directory {ROOT_DIR} does not exist.")
        return

    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        
        if os.path.isdir(song_dir):
            json_data_path = os.path.join(song_dir, "vocals.json")
            
            if not os.path.exists(json_data_path):
                continue
                
            print(f"Processing folder: {item}")
            
            # Load WhisperX JSON data
            with open(json_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract words directly from the flat word_segments array
            word_segments = data.get('word_segments', [])
            
            # Fallback to flattening the main segments if word_segments is empty or missing
            if not word_segments:
                print(" -> 'word_segments' not found at root. Falling back to nested segment words...")
                raw_words = []
                for segment in data.get('segments', []):
                    for w in segment.get('words', []):
                        raw_words.append(w)
            else:
                raw_words = word_segments

            # Format each word into a single column string with its timestamps
            formatted_lines = []
            for w in raw_words:
                word_text = w.get('word', '').strip()
                if not word_text:
                    continue
                
                # Fetch start and end times, fall back safely if None
                start_time = w.get('start')
                end_time = w.get('end')
                
                # Format timestamps if they exist, otherwise label as unknown
                s_str = f"({start_time:.3f})" if start_time is not None else "(unknown)"
                e_str = f"({end_time:.3f})" if end_time is not None else "(unknown)"
                
                formatted_lines.append(f"{word_text} {s_str} {e_str}")

            # Write out to json_lyric.txt
            json_lyric_txt_path = os.path.join(song_dir, "json_lyric.txt")
            with open(json_lyric_txt_path, "w", encoding="utf-8") as f:
                for line in formatted_lines:
                    f.write(line + "\n")
            
            print(f" -> Successfully created text configuration: json_lyric.txt ({len(formatted_lines)} words)")

if __name__ == "__main__":
    process_all_songs()