import os
import sys
import time
from moviepy import VideoFileClip

def batch_convert(input_folder, output_folder):
    valid_extensions = ('.mp4', '.webm', '.mkv', '.mov', '.avi', '.ts')
    total_original_size = 0
    total_new_size = 0
    files_processed = 0

    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' not found.")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    all_files = os.listdir(input_folder)
    files_to_process = [
        f for f in all_files 
        if f.lower().endswith(valid_extensions) and not f.lower().endswith('_x265.mp4')
    ]

    total_files = len(files_to_process)
    if total_files == 0:
        print("No new files found to process.")
        return

    print(f"Found {total_files} files. Starting batch...")
    batch_start_time = time.time()

    for index, filename in enumerate(files_to_process):
        input_path = os.path.join(input_folder, filename)
        name_part, _ = os.path.splitext(filename)
        output_filename = f"{name_part}_x265.mp4"
        output_path = os.path.join(output_folder, output_filename)

        if os.path.exists(output_path):
            continue

        print(f"\n[{index + 1}/{total_files}] Processing: {filename}")
        orig_size = os.path.getsize(input_path)
        
        try:
            with VideoFileClip(input_path) as clip:
                clip.write_videofile(
                    output_path, 
                    codec="hevc_nvenc", 
                    ffmpeg_params=[
                        "-preset", "p7", 
                        "-rc", "vbr", 
                        "-cq", "35",      
                        "-qmin", "32", 
                        "-maxrate", "2000k", 
                        "-bufsize", "4000k"
                    ],
                    audio_codec="aac",
                    logger=None 
                )
            
            total_original_size += orig_size
            total_new_size += os.path.getsize(output_path)
            files_processed += 1
            
            # --- Time Estimation Logic ---
            elapsed_batch_time = time.time() - batch_start_time
            avg_time_per_file = elapsed_batch_time / files_processed
            files_remaining = total_files - (index + 1)
            est_remaining_seconds = avg_time_per_file * files_remaining
            
            # Convert seconds to a readable format
            est_min, est_sec = divmod(est_remaining_seconds, 60)
            print(f"File Done. Estimated time remaining: {int(est_min)}m {int(est_sec)}s")

        except Exception as e:
            print(f"Failed to convert {filename}: {e}")

    # Final Summary
    end_time = time.time()
    duration_mins = (end_time - batch_start_time) / 60
    total_saved_gb = (total_original_size - total_new_size) / (1024**3)
    
    print("\n" + "="*30)
    print("BATCH COMPLETE")
    print(f"Total Time:       {duration_mins:.1f} minutes")
    print(f"Space Saved:      {total_saved_gb:.2f} GB")
    if total_original_size > 0:
        reduction = (1 - (total_new_size / total_original_size)) * 100
        print(f"Reduction Ratio:  {reduction:.1f}%")
    print("="*30)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py \"C:\\Input\" \"C:\\Output\"")
    else:
        batch_convert(sys.argv[1], sys.argv[2])