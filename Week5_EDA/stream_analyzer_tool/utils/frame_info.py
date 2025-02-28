import subprocess
import json
import sys


def execute_ffprobe(ts_file, stream_id, stream_element, input_entries):
    # Command to run ffprobe and extract all frames information for a specific stream ID
    command = ["ffprobe", "-v", "error", "-of", "json", ts_file]

    if stream_id is None:  # run ffprobe and extract all packets information
        command[3:3] = (
            input_entries  # Insert input_entries at index 3, after '-v error'
        )
    else:
        command[3:3] = [
            "-select_streams",
            f"i:{stream_id}",
        ]  # Insert '-select_streams' and 'stream_id'
        command[5:5] = input_entries  # Insert input_entries after '-select_streams'

    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if result.returncode != 0:
        print("Error running ffprobe:", result.stderr)
        return []

    data = json.loads(result.stdout)
    stream_element_list = data.get(stream_element, [])
    return stream_element_list


def get_all_packets(ts_file):
    sub_command = [
        "-show_entries",
        "packet=pts,duration,codec_type,stream_index,pts_time,pts_time,duration_time",
    ]
    return execute_ffprobe(ts_file, None, "packets", sub_command)


def normalize_frames(ffprobe_output):
    """
    Normalizes ffprobe JSON output to have consistent keys across platforms.
    """
    # Mapping of Linux keys to Windows keys
    key_mapping = {
        "pkt_pts": "pts",
        "pkt_pts_time": "pts_time",
        "pkt_duration": "duration",
        "pkt_duration_time": "duration_time",
    }

    for stream in ffprobe_output:
        updated_stream = stream.copy()

        for key, value in stream.items():
            if key in key_mapping:
                new_key = key_mapping[key]
                updated_stream[new_key] = value
                del updated_stream[key]

        # Replace the original stream with the updated one
        stream.clear()
        stream.update(updated_stream)

    return ffprobe_output


def extract_frame_information(ts_file, stream_id):
    sub_command = ["-show_frames"]
    # Mapping of windows keys to linux keys to avoid discrepencies in the key names during execution on windows/Linux
    frame_info = normalize_frames(
        execute_ffprobe(ts_file, stream_id, "frames", sub_command)
    )
    return frame_info


def extract_pts_frame_type(ts_file, stream_id):
    sub_command = ["-show_entries", "frame=pts,pict_type"]
    return execute_ffprobe(ts_file, stream_id, "frames", sub_command)


def get_pts_duration_from_packet_info(ts_file, stream_id):
    sub_command = ["-show_entries", "packet=pts,duration,pts_time,duration_time"]
    return execute_ffprobe(ts_file, stream_id, "packets", sub_command)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Please Pass TS_FILE_NAME, video/audio PID as arguments")
        print("Example: python frame_info.py osn-demo-1_BXP-P0144012.ts <pid>")
        sys.exit(1)

    ts_file = sys.argv[1]
    pid = sys.argv[2]
    frames = extract_frame_information(ts_file, pid)
    with open("frames_info_" + pid + ".json", "w") as json_file:
        json.dump(frames, json_file, indent=4)
