import os
import subprocess
import streamlit as st

def update_proj_name(project_name):
    config_path = os.path.join(os.path.dirname(__file__), 'live_stream_analyzer_config.py')
    if os.path.exists(config_path):
        # Read the current configuration file
        with open(config_path, 'r') as f:
            lines = f.readlines()

        # Update the project_name property
        with open(config_path, 'w') as f:
            for line in lines:
                if line.startswith('project_name ='):
                    f.write(f"project_name = \"{project_name}\" # Ex: astro, osn, bein,...\n")
                else:
                    f.write(line)

        st.success(f"Updated project_name in live_stream_analyzer_config.py to '{project_name}'")
    else:
        st.error("live_stream_analyzer_config.py not found.")

def main():
    st.title('Live Stream Analyzer')

    # Dropdown for selecting project
    project_names = ['osn', 'astro', 'bein']  # Add more project names as needed
    selected_project = st.selectbox('Select Project:', project_names)

    # Update proj_name in proj_config.json
    update_proj_name(selected_project)

    # File upload section
    uploaded_file = st.file_uploader("Upload a TS file", type=["ts"])
    if uploaded_file is not None:
        ts_filename = os.path.basename(uploaded_file.name)
        with open(ts_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File uploaded successfully: {ts_filename}")

        # Process the uploaded TS file
        process_ts_file(ts_filename)

def process_ts_file(ts_filename):
    # Check if the reports are already stored in session state
    if 'report_filenames' not in st.session_state:
        # Call generate_report to process the TS file and get the list of report filenames
        st.session_state.report_filenames = generate_report(ts_filename)
    else:
        st.session_state.report_filenames = st.session_state.report_filenames

    report_filenames = st.session_state.report_filenames

    if report_filenames:
        st.success("Report file(s) generated successfully.")

        # Create download buttons for each report file
        for report_filename in report_filenames:
            report_basename = os.path.basename(report_filename)

            # Read the file content
            with open(report_filename, "rb") as file:
                file_content = file.read()

            # Create a download button
            st.download_button(
                label=f"Download **{report_basename}**",
                data=file_content,
                file_name=report_basename
            )
    else:
        st.error("No report files generated. Please check the input TS file.")

def generate_report(ts_filename):
    # Replace this with your actual logic to generate Excel file from ts_filename
    report_files = []
    try:
        # Run the subprocess to generate the report
        subprocess.run(['python', 'live_stream_scte35_parsing.py', ts_filename], check=True)

        # Assuming the script generates multiple reports, collect their filenames
        report_dir = "./"

        # Iterate over the generated report files in the directory
        if os.path.exists(report_dir):
            for file in os.listdir(report_dir):
                if file.endswith(".txt") or file.endswith(".json"):  # Assuming the reports are Excel files
                    report_files.append(os.path.join(report_dir, file))

    except subprocess.CalledProcessError as e:
        st.error(f"Error processing TS file. Selected project and uploaded TS stream don't match. Please provide an appropriate TS file.")
        return None

    return report_files if report_files else None

if __name__ == '__main__':
    main()