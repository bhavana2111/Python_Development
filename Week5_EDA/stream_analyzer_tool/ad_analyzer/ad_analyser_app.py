import streamlit as st
import pandas as pd
import subprocess
import os

from st_aggrid import AgGrid, GridOptionsBuilder


def update_proj_name(project_name):
    config_path = os.path.join(os.path.dirname(__file__), "../config/project_config.py")

    if os.path.exists(config_path):
        try:
            # Read the file content
            with open(config_path, "r") as file:
                lines = file.readlines()

            # Update only the project_name line
            updated_lines = []
            for line in lines:
                if line.strip().startswith("project_name ="):
                    updated_line = (
                        f'project_name = "{project_name}" # Ex: astro, osn, bein,...\n'
                    )
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)

            # Write the updated content back to the file
            with open(config_path, "w") as file:
                file.writelines(updated_lines)

            st.success(f"Updated project_name in project_config.py to '{project_name}'")
        except Exception as e:
            st.error(f"Error updating project_config.py: {e}")
    else:
        st.error("project_config.py not found.")


def ad_analyzer_ui():
    st.header("AD Analyzer")

    # Dropdown for selecting project
    project_names = ["astro", "osn", "bein"]  # Add more project names as needed
    selected_project = st.selectbox("Select Project:", project_names)

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


def live_analyzer_ui():
    st.header("Live Analyzer")
    st.write(
        "Feature coming soon! This section will include live stream analysis tools."
    )


def main():
    st.set_page_config(layout="wide")
    st.title("Analyzer Tool")

    # Dropdown for selecting Analyzer type
    analyzer_options = ["AD Analyzer", "Live Analyzer"]
    selected_analyzer = st.selectbox("Select Analyzer Type:", analyzer_options)

    if selected_analyzer == "AD Analyzer":
        ad_analyzer_ui()
    elif selected_analyzer == "Live Analyzer":
        live_analyzer_ui()


def process_ts_file(ts_filename):
    excel_filename = generate_excel(ts_filename)

    if excel_filename:
        st.success("Excel file generated successfully.")
        base_dir = os.path.dirname(__file__)  # Current script directory
        excel_filepath = os.path.join(base_dir, excel_filename)

        if os.path.exists(excel_filepath):
            # Provide a download button for the file
            try:
                with open(excel_filepath, "rb") as f:
                    excel_data = f.read()
                st.download_button(
                    label=f"Download {os.path.basename(excel_filepath)}",
                    data=excel_data,
                    file_name=os.path.basename(excel_filepath),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"Error while reading the file: {str(e)}")
        else:
            st.error(f"File not found at: {excel_filepath}")

        # Display each sheet of the Excel file
        display_excel_sheets(excel_filename)
        display_excel_charts(ts_filename)


def generate_excel(ts_filename):
    try:
        subprocess.run(["python", "ad_analyzer.py", ts_filename], check=True)
        folder_name = os.path.splitext(os.path.basename(ts_filename))[0]
        excel_filename = f"output_data/{folder_name}/media_info_{folder_name}.xlsx"
        return excel_filename
    except subprocess.CalledProcessError as e:
        # st.error(f"Error processing TS file: {e}")
        st.error(
            f"Error processing TS file. Selected project and uploaded TS stream dont match.\n Please provide appropriate TS file."
        )
        return None


def display_excel_charts(ts_filename):

    folder_name = os.path.splitext(ts_filename)[0]
    charts_dir = f"output_data/{folder_name}"

    if os.path.exists(charts_dir):

        # List all files in the output_data directory
        chart_files = os.listdir(charts_dir)

        # Filter audio charts
        audio_charts = [
            file
            for file in chart_files
            if file.startswith(f"chart_{folder_name}_audio")
        ]

        video_charts = [
            file
            for file in chart_files
            if file.startswith(f"chart_{folder_name}_video")
        ]

        if audio_charts:
            st.subheader("Audio Charts")
            for idx, audio_chart in enumerate(audio_charts):
                audio_chart_path = os.path.join(charts_dir, audio_chart)
                st.image(
                    audio_chart_path,
                    caption=f"Audio Chart {idx+1}: {audio_chart}",
                    use_column_width=True,
                )
                # Add a separator between charts, except after the last one
                if idx < len(audio_charts) - 1:
                    st.markdown("---")  # Insert a horizontal rule
        else:
            st.warning("No audio charts found.")

        if video_charts:
            st.subheader("Video Charts")
            for idx, video_chart in enumerate(video_charts):
                video_chart_path = os.path.join(charts_dir, video_chart)
                st.image(
                    video_chart_path,
                    caption=f"Video Chart {idx+1}: {video_chart}",
                    use_column_width=True,
                )
                # Add a separator between charts, except after the last one
                if idx < len(video_charts) - 1:
                    st.markdown("---")  # Insert a horizontal rule
        else:
            st.warning("No video charts found.")
    else:
        st.error("Charts not found.")


def display_excel_sheets(excel_filename):
    # Read Excel file
    xl = pd.ExcelFile(excel_filename)
    sheet_names = xl.sheet_names

    # Display each sheet in a separate section
    for sheet_name in sheet_names:
        # Check if the sheet does not contain charts
        if "Chart" not in sheet_name:
            st.subheader(sheet_name)
            df = pd.read_excel(excel_filename, sheet_name=sheet_name)
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(width=200)
            grid_options = gb.build()
            AgGrid(df, gridOptions=grid_options, height=500, width="100%")


if __name__ == "__main__":
    main()
