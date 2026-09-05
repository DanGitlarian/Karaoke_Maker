import json
import os

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
HOLD_TIME = 0.1  # Strictly set to 0.1 seconds to keep lines visible briefly after finishing

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

def get_kf_text(words, line_start_time):
    """Calculates ASS tracking centisecond delays using {\kf} tags relative to line start."""
    kf_parts = []
    current_time = line_start_time

    for idx, w in enumerate(words):
        start = w['start']
        end = w['end']
        word_str = w['word']

        # Account for silence gaps between words using standard spacing formatting
        if start > current_time:
            gap_duration_cs = int(round((start - current_time) * 100))
            if gap_duration_cs > 0:
                kf_parts.append(f"{{\\kf{gap_duration_cs}}}")

        duration_cs = int(round((end - start) * 100))
        if duration_cs <= 0:
            duration_cs = 1  # Guard rail against zero-length durations

        space_padding = " " if idx < len(words) - 1 else ""
        kf_parts.append(f"{{\\kf{duration_cs}}}{word_str}{space_padding}")
        current_time = end

    return "".join(kf_parts)

def process_song_directory(song_dir):
    # Strictly read from the pre-split vocal_chunks.json file
    chunks_path = os.path.join(song_dir, "vocal_chunks.json")
    if not os.path.exists(chunks_path):
        return

    print(f"Generating rich styled subtitle map from vocal_chunks.json for: {os.path.basename(song_dir)}")

    with open(chunks_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = data.get('lines', [])
    if not lines:
        return

    # ASS File Header Definition Block
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
    
    SECONDARY_COLOR_TAG = "{\\1c&H00FFFF&}"  # Light blue / Cyan prediction highlight
    events = ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

    # 1. Create the initial intro filler line if there's dead air before the first lyric hits
    first_lyric_start = lines[0]['start']
    if first_lyric_start > 0:
        intro_duration_cs = int(round(first_lyric_start * 100))
        first_line_text = lines[0]['text']
        intro_text = f"{{\\kf{intro_duration_cs}}}~" + "\\N" + f"{{\\r}}{SECONDARY_COLOR_TAG}{first_line_text}"
        events.append(f"Dialogue: 0,{format_ass_time(0.0)},{format_ass_time(first_lyric_start)},Default,,0,0,40,,{intro_text}")

    # 2. Map all chunked entries to styled Dialogue lines, checking for long silence gaps
    for i, current in enumerate(lines):
        # Calculate screen visual lifespan windows
        if i == 0:
            appear_time = 0.0 if first_lyric_start == 0 else first_lyric_start
        else:
            appear_time = max(0, current['start'] - 2.5)
            prev_end_with_hold = lines[i-1]['end'] + HOLD_TIME
            
            # CHECK FOR FORCED MID-SONG SILENCE LINES (Gap >= 5 seconds)
            # Check the actual distance from the prior chunk's finish time to this chunk's start time
            if current['start'] - lines[i-1]['end'] >= 5.0:
                silence_start = lines[i-1]['end'] + HOLD_TIME
                silence_end = current['start'] - 2.5
                
                # Make sure timestamps stay chronologically logical
                if silence_end > silence_start:
                    silence_duration_cs = int(round((silence_end - silence_start) * 100))
                    silence_text = f"{{\\kf{silence_duration_cs}}}~" + "\\N" + f"{{\\r}}{SECONDARY_COLOR_TAG}{current['text']}"
                    events.append(f"Dialogue: 0,{format_ass_time(silence_start)},{format_ass_time(silence_end)},Default,,0,0,40,,{silence_text}")
                
                # Snug the line presentation start window to the current lyric lead-in mark
                appear_time = current['start'] - 2.5

            if appear_time < prev_end_with_hold:
                appear_time = prev_end_with_hold
            
        start_str = format_ass_time(appear_time)
        end_time_with_hold = current['end'] + HOLD_TIME
        end_str = format_ass_time(end_time_with_hold)

        # Generate primary active lyric block with {\kf} tags
        display_text = get_kf_text(current['words'], appear_time)
        
        # Stably tack on the next line preview block if available without formatting leakage
        if i + 1 < len(lines):
            upcoming_text = lines[i+1]['text']
            display_text += "\\N" + f"{{\\r}}{SECONDARY_COLOR_TAG}{upcoming_text}"

        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,40,,{display_text}")

    # Save output cleanly into lyrics.ass
    ass_output = os.path.join(song_dir, "lyrics.ass")
    with open(ass_output, 'w', encoding='utf-8') as f:
        f.write("\n".join(header + events))
        
    print(f" -> Generated target script: {ass_output}")

def process_all_jsons():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Directory {ROOT_DIR} not found.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            process_song_directory(song_dir)

if __name__ == "__main__":
    process_all_jsons()