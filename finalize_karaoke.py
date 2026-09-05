import os
import subprocess

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
FFMPEG_PATH = "ffmpeg"
VIDEO_NAME = "song_video.mp4"
AUDIO_NAME = "accompaniment.wav"  # The new audio source
LYRICS_NAME = "lyrics.ass"
OUTPUT_SUFFIX = "_karaoke.mp4"

def burn_karaoke_video(video_path, audio_path, ass_path, out_path):
    # Paths cleanup for FFmpeg filter compatibility
    video_path = video_path.replace("\\", "/")
    audio_path = audio_path.replace("\\", "/")
    ass_path = ass_path.replace("\\", "/")
    out_path = out_path.replace("\\", "/")

    # Special handling for Windows drive letters in ASS filter
    if ass_path[1:3] == ":/":
        ass_path = ass_path[0] + "\\:" + ass_path[2:]

    vf_filter = f"setpts=PTS-STARTPTS,ass='{ass_path}',format=yuv420p"

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,   # Input 0: Video
        "-i", audio_path,   # Input 1: Instrumental Audio
        "-vf", vf_filter,
        "-map", "0:v:0",    # Map first video stream from Input 0
        "-map", "1:a:0",    # Map first audio stream from Input 1
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",      # Re-encode wav to aac for mp4 compatibility
        "-b:a", "192k",     # Good quality bitrate
        "-shortest",        # End video if audio ends earlier
        "-movflags", "+faststart",
        out_path
    ]

    print(f"🛠️  Merging Instrumental + Video + Lyrics...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("FFmpeg Error Output:", result.stderr)
        raise RuntimeError("FFmpeg failed")

def main():
    for song_name in os.listdir(ROOT_DIR):
        song_folder = os.path.join(ROOT_DIR, song_name)
        if not os.path.isdir(song_folder):
            continue

        video = os.path.join(song_folder, VIDEO_NAME)
        audio = os.path.join(song_folder, AUDIO_NAME)
        ass = os.path.join(song_folder, LYRICS_NAME)
        output = os.path.join(song_folder, song_name + OUTPUT_SUFFIX)

        if all(os.path.exists(f) for f in [video, audio, ass]):
            print(f"🎬 Processing: {song_name}")
            try:
                burn_karaoke_video(video, audio, ass, output)
                print(f"✅ Success: {output}\n")
            except Exception as e:
                print(f"❌ Failed: {e}")
        else:
            missing = [f for f in [VIDEO_NAME, AUDIO_NAME, LYRICS_NAME] 
                      if not os.path.exists(os.path.join(song_folder, f))]
            print(f"Skipping {song_name}: Missing {', '.join(missing)}")

if __name__ == "__main__":
    main()