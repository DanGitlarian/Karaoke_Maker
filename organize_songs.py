import os
import shutil

def organize_karaoke_songs(input_dir):
    # Ensure the target directory exists
    if not os.path.exists(input_dir):
        print(f"Error: The directory {input_dir} does not exist.")
        return

    print(f"Scanning directory: {input_dir}\n")
    
    # List all items in the input directory
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        
        # Process only files (this prevents it from processing folders it already created)
        if os.path.isfile(item_path):
            # Split the filename and its extension
            filename, file_ext = os.path.splitext(item)
            
            # Filter for video files (primarily .mp4 as requested)
            if file_ext.lower() in ['.mp4', '.mkv', '.avi', '.mov']:
                # Define the new folder path (same name as the song file)
                target_folder = os.path.join(input_dir, filename)
                
                # Create the subfolder if it doesn't already exist
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                    print(f"Created folder: {filename}")
                
                # Define the destination path with the exact name 'song_video.mp4'
                destination_file = os.path.join(target_folder, "song_video.mp4")
                
                try:
                    # Copy the file to its new subfolder location
                    shutil.copy2(item_path, destination_file)
                    print(f"  -> Copied and renamed to: {os.path.join(filename, 'song_video.mp4')}")
                    
                    # OPTIONAL: If you want to MOVE the files instead of COPYING them 
                    # (to save disk space and clean up the input folder), 
                    # uncomment the line below by removing the '#' symbol:
                    # os.remove(item_path)
                    
                except Exception as e:
                    print(f"  [Error] Could not copy {item}: {e}")

if __name__ == "__main__":
    # Using a raw string (r"...") to handle Windows backslashes correctly
    INPUT_DIRECTORY = r"C:\Programs\Karaoke_Maker\Songs\input"
    
    organize_karaoke_songs(INPUT_DIRECTORY)
    print("\nProcessing complete!")