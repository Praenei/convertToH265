import os
import subprocess
import json
import csv
import time
import argparse
import stat

def get_video_codec(file_path):
    """Returns the codec name of the first video stream using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name', '-of', 'json', file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        return data['streams'][0]['codec_name']
    except Exception:
        return "Unknown/Error"

def process_videos(root_folder, output_csv, convert_to_h265):
    # Only processing MKV files as per your change of plan
    target_extension = '.mkv'
    print(f"Scanning and Processing MKVs in: {root_folder}")
    
    total_original_size = 0
    total_new_size = 0
    files_processed = 0
    batch_start_time = time.time()

    # Pre-scan to count files for time estimation
    all_files = []
    for root, _, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(target_extension):
                all_files.append(os.path.join(root, file))
    
    total_files_to_check = len(all_files)
    
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Filename', 'Codec', 'Size (KB)', 'Full Path'])

            for index, full_path in enumerate(all_files):
                filename = os.path.basename(full_path)
                codec = get_video_codec(full_path)
                
                # Process if NOT already H.265 (hevc)
                if codec != 'hevc':
                    
                    orig_size = os.path.getsize(full_path)
                    size_kb = round(orig_size / 1024, 2)
                    
                    writer.writerow([filename, codec, size_kb, full_path])
                    print(f"\n[!] Processing: {filename} ({codec})")
                    
                    
                    if convert_to_h265:
                        base_name = os.path.splitext(full_path)[0]
                        new_base_name = base_name.replace("x264", "x265").replace("h264", "x265")
                        if "x265" not in new_base_name:
                            output_path = f"{new_base_name}_x265.mkv"
                        else:
                            output_path = f"{new_base_name}.mkv"

                        # FFmpeg Command: Includes Video re-encode, Audio copy, and Subtitle copy
                        # Using map 0 ensures ALL streams (subs included) are pulled in
                        conv_cmd = [
                            'ffmpeg', 
                            '-hide_banner',                     # Global flag first
                            '-loglevel', 'error',               # Global flag first
                            '-err_detect', 'ignore_err',
                            '-i', full_path,                    # Input
                            '-map', '0', 
                            '-c:v', 'hevc_nvenc', 
                            '-preset', 'p4',
                            '-rc', 'vbr',
                            '-cq', '32',
                            '-vf', "scale='min(1920,iw)':-2",   # Filters after input
                            '-pix_fmt', 'yuv420p',
                            '-level', '4.1',
                            '-tier', 'main',
                            '-c:a', 'copy',
                            '-c:s', 'copy',
                            '-y', 
                            output_path                         # Output last
                        ]

                        try:
                            result = subprocess.run(conv_cmd, check=True)
                            
                            # Give the OS a tiny moment to release the file handle
                            time.sleep(1) 

                            max_retries = 3
                            for i in range(max_retries):
                                try:
                                    os.chmod(full_path, stat.S_IWRITE)
                                    os.remove(full_path)
                                    print(f"Successfully removed original: {filename}")
                                    break 
                                except PermissionError:
                                    if i < max_retries - 1:
                                        print(f"File locked, retrying deletion in 2s... (Attempt {i+1}/{max_retries})")
                                        time.sleep(2)
                                    else:
                                        print(f"CRITICAL: Could not delete {filename}. Manual cleanup required.")
                            
                            # Stats tracking
                            new_size = os.path.getsize(output_path)
                            total_original_size += orig_size
                            total_new_size += new_size
                            files_processed += 1
                            
                            # Time Estimation
                            elapsed = time.time() - batch_start_time
                            avg_time = elapsed / files_processed
                            remaining = total_files_to_check - (index + 1)
                            est_min, est_sec = divmod(avg_time * remaining, 60)
                            
                            print(f"Done. Est. remaining: {int(est_min)}m {int(est_sec)}s")
                            
                        except subprocess.CalledProcessError as e:
                            print(f"Error converting {filename}: {e}")
    except KeyboardInterrupt:
        print("\n\n" + "*"*30)
        print("PROCESS INTERRUPTED BY USER (Ctrl+C)")

    # Final Summary
    duration_mins = (time.time() - batch_start_time) / 60
    total_saved_gb = (total_original_size - total_new_size) / (1024**3)
    
    print("\n" + "="*30)
    print("BATCH COMPLETE")
    print(f"Total Time:       {duration_mins:.1f} minutes")
    print(f"Space Saved:      {total_saved_gb:.2f} GB")
    print(f"New Size:      {(total_new_size/(1024**3)):.2f} GB")
    print(f"Original size:      {(total_original_size/(1024**3)):.2f} GB")
    print("="*30)

if __name__ == "__main__":
    
    # python findNonH265.py "F:\TV Series New\Robin Hood (2025)"
    # python findNonH265.py "F:\TV Series New\" --convert
    
    parser = argparse.ArgumentParser(description="Batch convert non-H265 MKVs to H265.")
    parser.add_argument("folder", help="The starting folder to scan")
    parser.add_argument("--csv", default="non_h265_inventory.csv", help="Output CSV filename")
    parser.add_argument("--convert",  action='store_true', help="Convert to H265?")
    
    args = parser.parse_args()

    if os.path.exists(args.folder):
        process_videos(args.folder, args.csv, args.convert)
    else:
        print(f"Error: Path '{args.folder}' does not exist.")
