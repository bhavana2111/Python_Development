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

	pip install pandas
	pip install matplotlib
	pip install streamlit
	pip install streamlit-aggrid
	pip install pymediainfo
	pip install openpyxl
	
	
4. Download MediaInfo CLI (MediaInfo_CLI_24.06_Windows_x64) from https://mediaarea.net/en/MediaInfo/Download/Windows#google_vignette and add to PATH variable.

If PATH is not updated correctly, reboot and try again.


5. To run the script, use the following command:

    a) To pass a single ts file as input ->

		py ad_analyzer.py <path/to/your/ts_file.ts>
		
		  (or)
		
		py ad_analyzer.py <path/to/your/ts_file_1.ts> <path/to/your/ts_file_2.ts> <path/to/your/ts_file_3.ts>
	
    b) To pass multiple ts files present in a folder (Assume ts files are present in a folder named ts_files_folder) ->
  
		py ad_analyzer.py ts_files_folder/
		
    c) To pass the location of ts file present on network ->
  
		py ad_analyzer.py https://ad-origin-apb.iris.synamedia.com/osmwqc5f/y6b3f2cjcta4ljo/files/file-1920i.ts
		
    d) To run the script by executing checkServices.py and then processing ts files, use the following script ->
   
       py ad_analyzer.py --run-check-services --check-services-args -c 645 -ep prod -s
   
		where, 	-c is cardID. This is mandatory param
				-ep is end point with options ['prod', 'int', 'demo', 'eu5']. Default is "eu3"
				-d is deviceID. This is optional
				-s is show_media_details. Default is False
				-l is log level. Default is INFO
				
##################

To run this from UI Page , execute ->

streamlit run app.py


		
	
		
		

  
	
	