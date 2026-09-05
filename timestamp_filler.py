import os
import re

ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"

def process_lyrics_file(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Global time tracker across the entire song file
    last_known_time = 0.0
    processed_lines = []

    # Regex to capture: text + (optional_start) + (optional_end)
    # It safely supports special characters like brackets and background vocal parentheses
    token_pattern = re.compile(r'([^\s(]+)\(([^)]*)\)\(([^)]*)\)')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed_lines.append("")
            continue

        # Check for trailing newline marker
        has_nl = stripped.endswith("nl")
        if has_nl:
            stripped = stripped[:-2].strip()

        # Find all matching timestamped word tokens on this line
        matches = list(token_pattern.finditer(line))
        
        if not matches:
            # Preserve structural lines (e.g., standalone markers or instrumentals) completely intact
            processed_lines.append(line.rstrip('\r\n'))
            # Try to harvest any standalone timestamps like ~~~~~(94.1)(102.9)
            standalone_times = re.findall(r'\((\d+\.?\d*)\)', line)
            if standalone_times:
                last_known_time = float(standalone_times[-1])
            continue

        # Parse matches into distinct token dictionaries
        line_tokens = []
        for m in matches:
            word = m.group(1)
            start = float(m.group(2)) if m.group(2).strip() else None
            end = float(m.group(3)) if m.group(3).strip() else None
            line_tokens.append({
                'word': word,
                'start': start,
                'end': end,
                'span': m.span()
            })

        # Break the line tokens into fully bounded interpolation segments
        segments = []
        current_segment = []
        
        for token in line_tokens:
            current_segment.append(token)
            # If a token defines a hard ending boundary, close the segment block
            if token['end'] is not None:
                segments.append(current_segment)
                current_segment = []
        if current_segment:
            segments.append(current_segment)

        # Process each bounded segment sequence
        for segment in segments:
            # Establish the segment's absolute start anchor
            if segment[0]['start'] is not None:
                start_anchor = segment[0]['start']
            else:
                start_anchor = last_known_time

            # Establish the segment's absolute end anchor
            if segment[-1]['end'] is not None:
                end_anchor = segment[-1]['end']
            else:
                # Fallback if no end anchor exists on the line segment
                end_anchor = start_anchor + len(segment) * 2.0 

            # Calculate character weights (length + 1) and implicit structural pauses
            total_weight = 0
            word_weights = []
            for token in segment:
                w_weight = len(token['word']) + 1
                word_weights.append(w_weight)
                total_weight += w_weight
            
            # Add weight for spaces/pauses between words
            num_pauses = len(segment) - 1
            total_weight += num_pauses * 1

            # Proportional time distribution math
            duration = end_anchor - start_anchor
            if total_weight > 0 and duration > 0:
                unit_time = duration / total_weight
                current_time = start_anchor

                for idx, token in enumerate(segment):
                    w_dur = word_weights[idx] * unit_time
                    
                    # Fill missing values while respecting pre-existing manual anchors
                    if token['start'] is None:
                        token['start'] = round(current_time, 1)
                    if token['end'] is None:
                        token['end'] = round(current_time + w_dur, 1)
                    
                    # Advance clock by word duration plus 1 silent interval unit
                    current_time += w_dur + (1 * unit_time)

            # Update our global clock tracker to the end of this segment
            last_known_time = end_anchor

        # Reconstruct the line precisely, preserving original text formatting and spacing positions
        rebuilt_line = ""
        last_idx = 0
        
        # Map the modified tokens back to their original text coordinates
        token_map = {t['span']: t for t in line_tokens}
        
        for span, token in token_map.items():
            # Append any leading characters or spaces skipped between tokens
            rebuilt_line += line[last_idx:span[0]]
            
            s_str = f"{token['start']:.1f}" if token['start'] is not None else ""
            e_str = f"{token['end']:.1f}" if token['end'] is not None else ""
            
            rebuilt_line += f"{token['word']}({s_str})({e_str})"
            last_idx = span[1]
            
        # Append remaining line suffix text
        rebuilt_line += line[last_idx:].rstrip('\r\n')
        
        # Ensure standard trailing structure normalization
        if has_nl and not rebuilt_line.endswith("nl"):
            rebuilt_line += "nl"
            
        processed_lines.append(rebuilt_line)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(processed_lines) + "\n")

def process_all_songs():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Target root path {ROOT_DIR} does not exist.")
        return
        
    for item in os.listdir(ROOT_DIR):
        song_dir = os.path.join(ROOT_DIR, item)
        if os.path.isdir(song_dir):
            empty_path = os.path.join(song_dir, "lyrics-lines.txt")
            filled_path = os.path.join(song_dir, "filled_lyrics.txt")
            
            if os.path.exists(empty_path):
                print(f"Processing structural timestamps for: {item}")
                process_lyrics_file(empty_path, filled_path)
                print(f" -> Successfully exported: {filled_path}")

if __name__ == "__main__":
    process_all_songs()