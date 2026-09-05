import os
import re

# Folder containing your .mp4 song files
SONG_FOLDER = r"C:\Programs\Karaoke_Maker\Songs\input"

# Words/phrases to remove from titles
JUNK = [
    "official music video", "official video", "official audio",
    "lyrics", "lyric video", "audio", "hd", "hq", 
    "live", "remastered", "video", "music video"
]

def clean(text):
    text = text.lower()

    # Remove junk phrases
    for j in JUNK:
        text = text.replace(f"({j})", "")
        text = text.replace(f"[{j}]", "")
        text = text.replace(j, "")

    # Remove brackets content
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^]]*\]", "", text)

    # Remove duplicate spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def detect_artist_title(base):
    """
    Detects artist and title using smart rules:
    1) If "artist - title" → use that
    2) Else → assume last word(s) is the artist
    """

    # Rule 1: "Artist - Title"
    if " - " in base:
        artist, title = base.split(" - ", 1)
        return artist.strip(), title.strip()

    # Otherwise, split by spaces
    parts = base.split()

    # Assume last part is the artist
    artist = parts[-1]
    title = " ".join(parts[:-1])

    return artist.strip(), title.strip()


def to_title_case(s):
    return " ".join(w.capitalize() for w in s.split())


if __name__ == "__main__":
    print("=== Filename Preprocessor ===")
    print("Processing folder:", SONG_FOLDER)

    for file in os.listdir(SONG_FOLDER):
        if not file.lower().endswith(".mp4"):
            continue

        full_path = os.path.join(SONG_FOLDER, file)
        base = os.path.splitext(file)[0]

        print(f"\nOriginal: {file}")

        # Clean text
        cleaned = clean(base)

        # Detect artist and title
        artist, title = detect_artist_title(cleaned)

        # Convert to proper capitalization
        artist = to_title_case(artist)
        title = to_title_case(title)

        # New filename
        newname = f"{artist} - {title}.mp4"
        newpath = os.path.join(SONG_FOLDER, newname)

        print(f"Renaming to: {newname}")

        # Rename file
        os.rename(full_path, newpath)

    print("\nProcessing Complete!")