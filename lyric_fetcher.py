import os
import requests
from bs4 import BeautifulSoup

# === CONFIG ===
BASE_FOLDER = r"C:\Programs\Karaoke_Maker\Songs\input"
GENIUS_API_TOKEN = "5Mw7SobOIPqq-2Ka70WaQ82iUmTYG3E6CwjWUnp68fUe5WpnXtyG_b_oRHxcCLq3"

HEADERS = {
    "Authorization": f"Bearer {GENIUS_API_TOKEN}"
}

def fetch_song_json(artist, title):
    """Fetch song metadata from Genius API."""
    search_url = "https://api.genius.com/search"
    params = {"q": f"{title} {artist}"}
    response = requests.get(search_url, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise Exception(f"Genius API error {response.status_code}: {response.text}")
    
    hits = response.json()["response"]["hits"]
    if not hits:
        return None
    
    song_api_path = hits[0]["result"]["api_path"]
    song_url = f"https://api.genius.com{song_api_path}"
    song_resp = requests.get(song_url, headers=HEADERS)
    if song_resp.status_code != 200:
        raise Exception(f"Genius song fetch error {response.status_code}: {song_resp.text}")
    
    return song_resp.json()["response"]["song"]

def scrape_lyrics_from_path(path):
    """Scrape lyrics from the Genius song webpage, starting from [Intro] if possible."""
    url = "https://genius.com" + path
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Failed to fetch lyrics page: {url}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    lyrics_divs = soup.find_all("div", {"data-lyrics-container": "true"})

    if not lyrics_divs:
        return None

    # Combine all lyrics blocks
    lyrics_text = "\n".join(div.get_text(separator="\n") for div in lyrics_divs)
    lyrics_text = lyrics_text.strip()

    # Try to cut before [Intro], but ONLY if present
    intro_index = lyrics_text.find("[Intro]")
    if intro_index != -1:
        lyrics_text = lyrics_text[intro_index:].strip()

    return lyrics_text if lyrics_text else None

# === PROCESS FILES ===
for filename in os.listdir(BASE_FOLDER):
    if not filename.lower().endswith((".mp3", ".mp4", ".wav")):
        continue

    name_part = os.path.splitext(filename)[0]
    if " - " in name_part:
        artist, title = name_part.split(" - ", 1)
    else:
        print(f"Skipping {filename}: cannot parse artist/title")
        continue

    txt_path = os.path.join(BASE_FOLDER,f"{name_part}, f"{name_part}.txt")
    if os.path.exists(txt_path):
        print(f"Lyrics already exist for {filename}")
        continue

    try:
        print(f"Fetching metadata for {filename}...")
        song_data = fetch_song_json(artist, title)
        if not song_data or "path" not in song_data:
            print(f"No metadata or lyrics path found for {filename}")
            continue

        print(f"Scraping lyrics for {filename}...")
        lyrics_text = scrape_lyrics_from_path(song_data["path"])
        if lyrics_text:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(lyrics_text)
            print(f"Lyrics saved: {txt_path}")
        else:
            print(f"No lyrics found on Genius page for {filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

print("\nAll songs processed.")