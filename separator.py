import requests
import os

API_URL = "http://127.0.0.1:9999/api"
SOURCE_FOLDER = r"C:\Programs\Karaoke_Maker\Songs\input"
MODEL = "2stems"  # change to 4stems or 5stems

VALID_EXTENSIONS = (".mp3", ".wav", ".mp4", ".m4a", ".flac", ".aac", ".ogg", ".wma")

def process_file(filepath):
    print(f"\nProcessing: {filepath}")

    with open(filepath, "rb") as f:
        files = {"file": f}
        data = {"model": MODEL}

        response = requests.post(API_URL, timeout=600, data=data, files=files)

    try:
        result = response.json()
    except:
        print("Invalid response from server.")
        return

    if result["code"] != 0:
        print("Error:", result["msg"])
        return

    print("Separation successful!")
    print("Generated files:")

    for url in result["data"]:
        print("   →", url)


def main():
    print("Scanning folder:", SOURCE_FOLDER)
    
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.lower().endswith(VALID_EXTENSIONS):
            fullpath = os.path.join(SOURCE_FOLDER, filename)
            process_file(fullpath)

    print("\nDone!")

if __name__ == "__main__":
    main()