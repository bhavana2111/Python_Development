import subprocess
import json
import sys


def get_stream_info(ts_file):
    # Command to run ffprobe and list all streams
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        ts_file,
    ]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if result.returncode != 0:
        print("Error running ffprobe:", result.stderr)
        return []

    data = json.loads(result.stdout)
    stream_info = data.get("streams", [])
    return stream_info


def extract_audio_video_pids(stream_info):
    # Extract audio and video PIDs
    video_pids = []
    audio_pids = []
    if stream_info:
        for stream in stream_info:
            if stream["codec_type"] == "video":
                video_pids.append(stream["id"])

            if stream["codec_type"] == "audio":
                audio_pids.append(stream["id"])

    return audio_pids, video_pids


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please Pass TS_FILE_NAME  as arguments")
        print("Example: python stream_info.py osn-demo-1_BXP-P0144012.ts")
        # print("Example: python validate_stream_for_missing_pts.py Emirates_A380_Business_Class_OSN.ts")
        sys.exit(1)
    ts_file = sys.argv[1]

    stream_info = get_stream_info(ts_file)
    with open("streams_data.json", "w") as json_file:
        json.dump(stream_info, json_file, indent=4)

    audio_pids, video_pids = extract_audio_video_pids(stream_info)
