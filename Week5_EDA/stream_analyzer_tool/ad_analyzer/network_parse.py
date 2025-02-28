import argparse
import json
import sys
import os

from media_info import extract_media_info

def main():
    parser = argparse.ArgumentParser(description="Process a .ts file from a network path.")
    parser.add_argument("file_path", type=str, help="Network path to the .ts file")
    
    args = parser.parse_args()
    ts_file_path = args.file_path
    
    # Now you can use `ts_file_path` in your script
    if os.path.exists(ts_file_path):
        print(f"Processing file: {ts_file_path}")
    else:
        print(f"File not found: {ts_file_path}")
    media_info_av_data = extract_media_info(ts_file_path)
    print(media_info_av_data)

if __name__ == "__main__":
    main()