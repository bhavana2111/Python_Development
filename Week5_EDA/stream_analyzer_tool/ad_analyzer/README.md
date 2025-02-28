# AD Analyzer Tool

This project processes a transport stream file to extract and analyze media information, including missing packets, bitrate calculations, and frame sizes. It generates visualizations, saves the results into an Excel file with appropriate remarks, and inserts the visualizations as images into separate sheets.

## Installation

1. Clone the repository:

```bash
    git clone "ssh://kvaithia@gerrit-bgl01.synamedia.com:29418/iris-e2e-tools/stream_analyzer_tool/ad_analyzer.git"

2. Create a virtual environment and activate it:

    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install the dependencies:

    pip install -r requirements.txt


4. Download MediaInfo CLI (MediaInfo_CLI_24.06_Windows_x64) from https://mediaarea.net/en/MediaInfo/Download/Windows#google_vignette and add to PATH variable.

If PATH is not updated correctly, reboot and try again.


5. To run the script, use the following command:

  a) To pass a single ts file as input ->

		py ad_analyzer.py path/to/your/ts_file.ts
	
  b) To pass multiple ts files present in a folder (Assume ts files are present in a folder named ts_files_folder) ->
  
		py ad_analyzer.py ts_files_folder/