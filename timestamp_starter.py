import os

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def generate_empty_timestamp_structure(song_dir):
    lyrics_path = os.path.join(song_dir, "lyrics.txt")
    output_path = os.path.join(song_dir, "empty_lyrics.txt")
    
    # Only process if the source lyrics.txt file exists in the directory
    if not os.path.exists(lyrics_path):
        return

    print(f"Creating empty timestamp blueprint for: {os.path.basename(song_dir)}")

    with open(lyrics_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    output_lines = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            # Keeps empty spacer gaps between text blocks untouched if they exist
            continue
            
        # Break line cleanly into individual space-separated tokens
        line_tokens = line.split()
        formatted_tokens = [f"{token}()()" for token in line_tokens]
        
        # Merge formatted tokens with single space padding and mark line end with 'nl'
        final_line = " ".join(formatted_tokens) + "nl"
        output_lines.append(final_line)

    # Write target file out cleanly
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines) + "\n")
        
    print(f" -> Successfully exported: {output_path}")

def process_all_songs():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Target root path {ROOT_DIR} does not exist.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            generate_empty_timestamp_structure(song_dir)

if __name__ == "__main__":
    process_all_songs()