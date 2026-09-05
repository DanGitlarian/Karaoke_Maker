import os
import subprocess

# === CONFIG ===
ROOT_DIR = r"C:\Programs\Karaoke_Maker\Songs\input"
GLOBAL_TIMING_VIDEO = r"C:\Programs\Karaoke_Maker\timing_video.mp4" # New shared path

FFMPEG_PATH = "ffmpeg"
SONG_VIDEO_NAME = "song_video.mp4"      # Source for AUDIO
LYRICS_NAME = "lyrics.ass"              # Subtitles to burn in
OUTPUT_SUFFIX = "_timing_video.mp4"

def burn_karaoke_video(song_video_path, timing_video_path, ass_path, out_path):
    # Normalize paths for FFmpeg filter parsing
    song_video_path = song_video_path.replace("\\", "/")
    timing_video_path = timing_video_path.replace("\\", "/")
    ass_path = ass_path.replace("\\", "/")
    out_path = out_path.replace("\\", "/")

    if ass_path[1:3] == ":/":
        ass_path = ass_path[0] + "\\:" + ass_path[2:]

    # Apply the subtitle burn-in and sync reset to the timing video stream
    vf_filter = f"setpts=PTS-STARTPTS,ass='{ass_path}',format=yuv420p"

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", timing_video_path,  # Input 0: Video source
        "-i", song_video_path,    # Input 1: Audio source
        "-map", "0:v:0",          # Take the video track from timing_video
        "-map", "1:a:0",          # Take the audio track from song_video
        "-vf", vf_filter,
        "-c:a", "copy",           # Direct stream copy the audio to avoid re-encoding loss
        "-c:v", "libx264",        
        "-preset", "medium",      
        "-crf", "20",             
        "-movflags", "+faststart",
        out_path
    ]

    print(f"🛠️ Remuxing Audio/Video and Burning Subtitles...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("FFmpeg Error Output:", result.stderr)
        raise RuntimeError("FFmpeg failed")

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Directory {ROOT_DIR} not found.")
        return

    # Verify that the central timing video is available before loop execution
    if not os.path.exists(GLOBAL_TIMING_VIDEO):
        print(f"Error: Core timing video file not found at: {GLOBAL_TIMING_VIDEO}")
        return

    for song_name in os.listdir(ROOT_DIR):
        song_folder = os.path.join(ROOT_DIR, song_name)
        if not os.path.isdir(song_folder):
            continue

        song_video = os.path.join(song_folder, SONG_VIDEO_NAME)
        ass = os.path.join(song_folder, LYRICS_NAME)
        output = os.path.join(song_folder, song_name + OUTPUT_SUFFIX)

        if os.path.exists(song_video) and os.path.exists(ass):
            print(f"\nProcessing Group: {song_name}")
            try:
                burn_karaoke_video(song_video, GLOBAL_TIMING_VIDEO, ass, output)
                print(f"✅ Successfully compiled: {output}")
            except Exception as e:
                print(f"❌ Failed to process {song_name}: {e}")
        else:
            missing = []
            if not os.path.exists(song_video): missing.append(SONG_VIDEO_NAME)
            if not os.path.exists(ass): missing.append(LYRICS_NAME)
            print(f"⏭️ Skipping '{song_name}' (Missing components: {', '.join(missing)})")

if __name__ == "__main__":
    main()