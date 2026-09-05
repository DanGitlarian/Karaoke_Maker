import os
import subprocess

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
FFMPEG_PATH = "ffmpeg"
VIDEO_NAME = "song_video.mp4"
LYRICS_NAME = "lyrics.ass" # Changed to match your file name
OUTPUT_SUFFIX = "_lyric_video.mp4"

def burn_karaoke_video(video_path, ass_path, out_path):
    video_path = video_path.replace("\\", "/")
    ass_path = ass_path.replace("\\", "/")
    out_path = out_path.replace("\\", "/")

    if ass_path[1:3] == ":/":
        ass_path = ass_path[0] + "\\:" + ass_path[2:]

    # vf_filter changes: 
    # 1. format=yuv420p ensures compatibility with all players
    # 2. setpts=PTS-STARTPTS fixes the 'starting halfway' sync issue
    vf_filter = f"setpts=PTS-STARTPTS,ass='{ass_path}',format=yuv420p"

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-vf", vf_filter,
        "-c:a", "copy",
        "-c:v", "libx264",    # Back to CPU for maximum stability
        "-preset", "medium",  # Slower but much more accurate
        "-crf", "20",         # Constant quality
        "-movflags", "+faststart", # Fixes playback issues in many players
        out_path
    ]

    print(f"🛠️ Stabilizing and Encoding Video...")
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
        ass = os.path.join(song_folder, LYRICS_NAME)
        output = os.path.join(song_folder, song_name + OUTPUT_SUFFIX)

        if os.path.exists(video) and os.path.exists(ass):
            print(f"🎬 Processing: {song_name}")
            try:
                burn_karaoke_video(video, ass, output)
                print(f"✅ Success: {output}\n")
            except Exception as e:
                print(f"❌ Failed: {e}")
        else:
            print(f"Skipping {song_name}: Missing video or .ass file")

if __name__ == "__main__":
    main()