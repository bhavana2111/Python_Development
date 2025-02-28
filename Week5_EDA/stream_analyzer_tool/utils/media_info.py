import sys
import os
import subprocess
import json
import re

# Get the parent directory of the current file
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)
import config.project_config as config

# Define the output directory
base_output_dir = os.path.join(os.path.dirname(__file__), 'output_data')
if not os.path.exists(base_output_dir):
    os.makedirs(base_output_dir)

def load_standard_values(file_path):
    file_path = os.path.join(parent_dir, 'config', file_path)
    with open(file_path, 'r') as file:
        return json.load(file)
    
def run_mediainfo(file_path):
    try:
        # Run the mediainfo command and get the output
        result = subprocess.run(['mediainfo', file_path], capture_output=True, text=True, check=True)
        return result.stdout
    except FileNotFoundError:
        print("Error: MediaInfo executable not found. Please ensure MediaInfo CLI is installed and in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: MediaInfo command failed with exit code {e.returncode}")
        sys.exit(1)


# Function to parse a given section and return a dictionary
def parse_section(section):
    pattern = re.compile(r'([^:\n]+)\s+:\s+(.+)')
    return {match.group(1).strip(): match.group(2).strip() for match in pattern.finditer(section)}

def parse_mediainfo_output(data):
    # Extracting video and audio sections
    video_section = re.findall(r'Video(?:\s#\d+)?\n(.*?)(?=\n\n|$)', data, re.DOTALL)
    audio_sections = re.findall(r'Audio #[0-9]+\n(.*?)(?=\n\n|\Z)', data, re.DOTALL)
    general_section = re.findall(r'General(?:\s#\d+)?\n(.*?)(?=\n\n|$)', data, re.DOTALL)

    # Parsing the sections
    video_info = [parse_section(section) for section in video_section]
    audio_info = [parse_section(section) for section in audio_sections]
    general_info = [parse_section(section) for section in general_section]
    
    # Storing in a dictionary
    media_info = {
        'Video': video_info,
        'Audio': audio_info,
        'General': general_info
    }
    return media_info

# Returns media info
def extract_media_info(file_path):
    output = run_mediainfo(file_path)
    info_dict = parse_mediainfo_output(output)
    filtered_info_dict = fetch_audio_video_info(info_dict)
    
    return filtered_info_dict

# Returns required audio video properties by reading expected keys from project specific config
def fetch_audio_video_info(info_dict):
    
    # Load standard values and keys not expected
    standard_keys = load_standard_values(config.project_spec_json[config.project_name])
    expected_keys = standard_keys.get('keys_expected',{})
    keys_not_expected = standard_keys.get('keys_not_expected',{})

    filtered_info = {'Video': [], 'Audio': [], 'General' : []}

    filtered_info['General'] = info_dict.get('General',[])

    for track in info_dict.get('Video', []):
        if track.get('Format', '') == 'AVC':
            filtered_data = {k: track.get(k, None) for k in expected_keys['AVC_Video']}
            filtered_info['Video'].append(filtered_data)

    keys_to_be_deleted_for_2ch = set()
    keys_to_be_deleted_for_6ch = set()
    for track in info_dict.get('Audio', []):
        if track.get('Format', '') == 'AC-3' and 'AC3_Audio' in expected_keys:
            filtered_data = {k: track.get(k, None) for k in expected_keys['AC3_Audio']} 
            if filtered_data.get('Channel(s)', '') == '2 channels':
                for k,v in filtered_data.items():
                    if keys_not_expected and k in keys_not_expected['AC3_2_channels'] and v is None:
                        keys_to_be_deleted_for_2ch.add(k)
            elif filtered_data.get('Channel(s)', '') == '6 channels':
                for k,v in filtered_data.items():
                    if keys_not_expected and k in keys_not_expected['AC3_6_channels'] and v is None:
                        keys_to_be_deleted_for_6ch.add(k)
            filtered_info['Audio'].append(filtered_data)
        elif track.get('Format', '') == 'MPEG Audio' and 'MPEG_Audio' in expected_keys:
            filtered_data = {k: track.get(k, None) for k in expected_keys['MPEG_Audio']}
            filtered_info['Audio'].append(filtered_data)
        elif track.get('Format', '') == 'AAC LC SBR' and 'AAC_LC_SBR_Audio' in expected_keys:
            filtered_data = {k: track.get(k, None) for k in expected_keys['AAC_LC_SBR_Audio']}
            if filtered_data.get('Channel(s)', '') == '2 channels':
                filtered_info['Audio'].append(filtered_data)
        elif track.get('Format', '') == 'E-AC-3' and 'EAC3_Audio' in expected_keys:
            filtered_data = {k: track.get(k, None) for k in expected_keys['EAC3_Audio']}
            if filtered_data.get('Channel(s)', '') == '6 channels':
                filtered_info['Audio'].append(filtered_data)

    for audio in filtered_info['Audio']:
        if audio['Format'] == 'AC-3':
            if audio.get('Channel(s)', '') == '2 channels':
                for key in keys_to_be_deleted_for_2ch:
                    audio.pop(key, None)
            elif audio.get('Channel(s)', '') == '6 channels':
                for key in keys_to_be_deleted_for_6ch:
                    audio.pop(key, None)

    return filtered_info

# Output media info data to a file
def save_media_info_to_json(info_dict, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(info_dict, json_file, indent=4)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main_script.py path/to/ts_file.ts")
        sys.exit(1)

    ts_file = sys.argv[1]
    ts_file_basename = os.path.basename(ts_file)
    # Extract the file name without the extension and create a directory
    ts_file_name = os.path.splitext(ts_file_basename)[0]
    ts_file_path = os.path.abspath(ts_file)
    output_dir = os.path.join(base_output_dir, ts_file_name)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    media_data = extract_media_info(ts_file_path)

    output_json_path = os.path.join(output_dir, 'media_info.json')
    save_media_info_to_json(media_data, output_json_path)

if __name__ == "__main__":
    main()