import os
import re

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
HOLD_TIME = 0.1  # Keep lines visible briefly for 0.1 seconds after singing finishes

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

def parse_timestamped_line(line):
    """
    Parses a single line from timestamped_lyrics.txt into a structural dict.
    Example: "Hello(0.122)(0.256) world(0.256)(0.600)nl"
    """
    line = line.strip()
    if not line:
        return None
        
    # Remove the trailing 'nl' end-of-line signifier
    if line.endswith("nl"):
        line = line[:-2].strip()
        
    if not line:
        return None

    # Pattern to capture word text and float timestamps
    word_pattern = re.compile(r"([^\s\(\)]+)\((.*?)\)\((.*?)\)")
    matches = word_pattern.findall(line)
    
    words_list = []
    for word_text, start_val, end_val in matches:
        word_entry = {"word": word_text}
        if start_val.strip() and end_val.strip():
            try:
                word_entry["start"] = float(start_val)
                word_entry["end"] = float(end_val)
            except ValueError:
                pass
        words_list.append(word_entry)
        
    if not words_list:
        return None

    # Find overall line boundary timings
    timed_starts = [w["start"] for w in words_list if "start" in w]
    timed_ends = [w["end"] for w in words_list if "end" in w]
    
    line_start = timed_starts[0] if timed_starts else 0.0
    line_end = timed_ends[-1] if timed_ends else 0.0
    line_text = " ".join([w["word"] for w in words_list])

    return {
        "start": line_start,
        "end": line_end,
        "text": line_text,
        "words": words_list
    }

def get_kf_text(words, line_start_time):
    """Calculates ASS tracking centisecond delays using {\\kf} tags relative to line appearance."""
    kf_parts = []
    current_time = line_start_time

    for idx, w in enumerate(words):
        start = w.get('start', current_time)
        end = w.get('end', start + 0.1)
        word_str = w['word']

        # Silence check gap filler tags
        if start > current_time:
            gap_duration_cs = int(round((start - current_time) * 100))
            if gap_duration_cs > 0:
                kf_parts.append(f"{{\\kf{gap_duration_cs}}}")

        duration_cs = int(round((end - start) * 100))
        if duration_cs <= 0:
            duration_cs = 1

        space_padding = " " if idx < len(words) - 1 else ""
        kf_parts.append(f"{{\\kf{duration_cs}}}{word_str}{space_padding}")
        current_time = end

    return "".join(kf_parts)

def convert_text_to_ass(song_dir):
    input_path = os.path.join(song_dir, "timestamped_lyrics.txt")
    ass_output = os.path.join(song_dir, "lyrics.ass")
    
    if not os.path.exists(input_path):
        return

    print(f"Generating SubStation Alpha karaoke from text for: {os.path.basename(song_dir)}")

    with open(input_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    lines = []
    for line in raw_lines:
        parsed = parse_timestamped_line(line)
        if parsed:
            lines.append(parsed)

    if not lines:
        return

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
    
    SECONDARY_COLOR_TAG = "{\\1c&H00FFFF&}"  # Light blue / Cyan preview line color block
    events = ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

    # 1. First structural pass: Add introductory dead-air space if it exists
    first_lyric_start = lines[0]['start']
    if first_lyric_start > 0:
        intro_duration_cs = int(round(first_lyric_start * 100))
        first_line_text = lines[0]['text']
        intro_text = f"{{\\kf{intro_duration_cs}}}~" + "\\N" + f"{{\\r}}{SECONDARY_COLOR_TAG}{first_line_text}"
        events.append(f"Dialogue: 0,{format_ass_time(0.0)},{format_ass_time(first_lyric_start)},Default,,0,0,40,,{intro_text}")

    # 2. Main generation loop mapping parsed elements 1:1
    for i, current in enumerate(lines):
        if i == 0:
            appear_time = 0.0 if first_lyric_start == 0 else first_lyric_start
        else:
            appear_time = max(0, current['start'] - 2.5)
            prev_end_with_hold = lines[i-1]['end'] + HOLD_TIME
            
            # DYNAMIC BREAK SILENCE: Checks if rest interval lasts 5+ seconds
            if current['start'] - lines[i-1]['end'] >= 5.0:
                silence_start = lines[i-1]['end'] + HOLD_TIME
                silence_end = current['start'] - 2.5
                
                if silence_end > silence_start:
                    silence_duration_cs = int(round((silence_end - silence_start) * 100))
                    silence_text = f"{{\\kf{silence_duration_cs}}}~" + "\\N" + f"{{\\r}}{SECONDARY_COLOR_TAG}{current['text']}"
                    events.append(f"Dialogue: 0,{format_ass_time(silence_start)},{format_ass_time(silence_end)},Default,,0,0,40,,{silence_text}")
                
                appear_time = current['start'] - 2.5

            if appear_time < prev_end_with_hold:
                appear_time = prev_end_with_hold
            
        start_str = format_ass_time(appear_time)
        end_time_with_hold = current['end'] + HOLD_TIME
        end_str = format_ass_time(end_time_with_hold)

        # Build primary tags tracking string literals
        display_text = get_kf_text(current['words'], appear_time)
        
        # Tack on preview line cleanly to prevent backslash print bleeding
        if i + 1 < len(lines):
            upcoming_text = lines[i+1]['text']
            display_text += "\\N" + f"{{\\r}}{SECONDARY_COLOR_TAG}{upcoming_text}"

        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,40,,{display_text}")

    with open(ass_output, 'w', encoding='utf-8') as f:
        f.write("\n".join(header + events))
        
    print(f" -> Successfully compiled target encoding file: {ass_output}")

def process_all_songs():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Directory {ROOT_DIR} not found.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            convert_text_to_ass(song_dir)

if __name__ == "__main__":
    process_all_songs()