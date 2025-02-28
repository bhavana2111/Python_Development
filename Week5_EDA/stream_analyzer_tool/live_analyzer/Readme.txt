Files Details:
--------------

1. config/project_config.py 	 - Configuration file holding project specific input
2. live_stream_scte35_parsing.py - Parses the live stream and extracts SCTE-35 information
3. live_stream_analyzer_app.py 	 - UI representation of the analyzer tool
4. plot_stream_line.py			 - Shows pictorial representation of stream data

Requirements:
-------------
pip install streamlit
pip install tsduck
pip install ffprobe
pip install pandas
pip install matplotlib
pip install openpyxl

Script command:
---------------
	1. To run the analyzer tool with UI representation over web page, follow below steps in gitbash or linux terminal:

			export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=20000 # Setting file upload limit to 20GB
			streamlit run live_stream_analyzer_app.py

	2. To run the anlayzer tool on git bash or linux terminal directly, follow below steps:

		python live_stream_scte35_parsing.py <ts file name>
		Ex:  "python live_stream_scte35_parsing.py OSN_TS0210min_03-07-2024.ts"

		Results are stored in current directory under files ::
			1. report_<ts_file_name>.txt
			2. scte35_data_report.txt
			3. transport_analysis_report.txt
			4. services_analysis_report.txt
			5. scte35_parsing_report.json
			6. media_info_<ts_file_name>.xlsx

	3. After running above script, filenamed "stream_timeline_data.json" will be created under folder "utils/"
	   Go to utils folder and Run below command after generation JSON file to view pictorial representation of stream data

	   python plot_stream_line.py
