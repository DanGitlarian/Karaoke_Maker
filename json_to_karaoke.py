import json
import os
import re

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
HOLD_TIME = 0.2  # Time in seconds to keep lines visible on-screen after they finish
MAX_CHAR_LIMIT = 40

def format_ass_time(seconds):
    if seconds < 0: 
        seconds = 0
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int(round((seconds % 1) * 100))
    if centiseconds == 100:
        secs += 1
        centiseconds = 0
    return f"{hours}:{mins:02d}:{secs:02d}.{centiseconds:02d}"

def split_segment_into_lines(words, max_len=MAX_CHAR_LIMIT):
    """
    Slices a long stream of words into multiple smaller chunks, 
    each strictly keeping text under max_len characters.
    Prioritizes splitting after punctuation (. , : ? !) where possible.
    """
    chunks = []
    current_chunk = []
    
    for w in words:
        # Test line length if we add this word
        test_chunk = current_chunk + [w]
        test_text = " ".join([word['word'] for word in test_chunk])
        
        if len(test_text) <= max_len:
            current_chunk.append(w)
            # If the word ends with punctuation, it's a natural breaking spot
            if re.search(r'[.,:?!]$', w['word'].strip()):
                chunks.append(current_chunk)
                current_chunk = []
        else:
            # If current_chunk has words, save it before starting a new one
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = [w]
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def get_k_text(words, line_start_time):
    """Calculates ASS tracking millisecond delays (\k tags) relative to line start."""
    k_parts = []
    current_time = line_start_time

    for idx, w in enumerate(words):
        start = w['start']
        end = w['end']
        word_str = w['word']

        duration_cs = int(round((end - start) * 100))
        if duration_cs <= 0:
            duration_cs = 1

        # Absorb preceding gaps directly into the word's tag duration
        if start > current_time:
            gap_duration_cs = int(round((start - current_time) * 100))
            if gap_duration_cs > 0:
                duration_cs += gap_duration_cs

        space_padding = " " if idx < len(words) - 1 else ""
        k_parts.append(f"\\k{duration_cs}{word_str}{space_padding}")
        current_time = end

    return "".join(k_parts)

def process_song_directory(song_dir):
    genius_path = os.path.join(song_dir, "genius_vocals.json")
    standard_path = os.path.join(song_dir, "vocals.json")
    
    if os.path.exists(genius_path):
        target_json = genius_path
        print(f" -> Found genius_vocals.json. Processing...")
    elif os.path.exists(standard_path):
        target_json = standard_path
        print(f" -> Falling back to standard vocals.json...")
    else:
        return

    with open(target_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_chunks = []
    
    # Run all segments through the new iterative splitting rule
    for segment in data.get('segments', []):
        words = segment.get('words', [])
        if not words:
            continue
            
        split_chunks = split_segment_into_lines(words, max_len=MAX_CHAR_LIMIT)
        for chunk in split_chunks:
            if chunk:
                processed_chunks.append({
                    'start': chunk[0]['start'],
                    'end': chunk[-1]['end'],
                    'words': chunk
                })

    if not processed_chunks:
        return

    # ASS File Header Block
    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,60,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,4,0,2,100,100,120,1"
    ]
    
    SECONDARY_COLOR_TAG = "{\\1c&H0000FFFF&}"
    events = ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

    for i, current in enumerate(processed_chunks):
        if i == 0:
            appear_time = 0.0
        else:
            appear_time = max(0, current['start'] - 2.5)
            prev_end_with_hold = processed_chunks[i-1]['end'] + HOLD_TIME
            if appear_time < prev_end_with_hold:
                appear_time = prev_end_with_hold
            
        start_str = format_ass_time(appear_time)
        end_time_with_hold = current['end'] + HOLD_TIME
        end_str = format_ass_time(end_time_with_hold)

        # Generate primary animated karaoke text line
        karaoke_part = get_k_text(current['words'], appear_time)
        display_text = f"{karaoke_part}"
        
        # PREVIEW GENERATION: Append next line's text cleanly beneath the active singing line
        if i + 1 < len(processed_chunks):
            upcoming_text = " ".join([w['word'].strip() for w in processed_chunks[i+1]['words']])
            display_text += f"\\\\N{{\\\\r}}{SECONDARY_COLOR_TAG}{upcoming_text}"

        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,40,,{display_text}")

    # Forces the output filename to 'lyrics.ass'
    ass_output = os.path.join(song_dir, "lyrics.ass")
    with open(ass_output, 'w', encoding='utf-8') as f:
        f.write("\n".join(header + events))
        
    print(f" -> Generated line-snapped subtitle script: {ass_output}")

def process_all_jsons():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: {ROOT_DIR} folder path configuration not found.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            process_song_directory(song_dir)

if __name__ == "__main__":
    process_all_jsons()