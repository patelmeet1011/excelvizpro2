import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io # Needed for handling various file types

st.set_page_config(
    page_title='ExcelViz Pro',
    page_icon='📊', # Changed icon for variety
    layout='wide'
)

# --- Optional Background and Logo ---
# Note: Ensure these files are in the same directory as your script, or provide full paths.
# If you don't have these image files, you can comment out the following sections.

# Upload the background image
# try:
#     background_image_path = 'excelvizprocopy.jpg'
#     with open(background_image_path, "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read()).decode()
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image: url(data:image/jpeg;base64,{encoded_string});
#             background-size: cover;
#             background-repeat: no-repeat;
#             background-attachment: fixed;
#             opacity: 0.85; /* Adjust main content area opacity */
#         }}
#         /* Make sidebar and other elements potentially less transparent or styled differently if needed */
#         .main .block-container {{
#             background-color: rgba(255, 255, 255, 0.9); /* Slightly transparent white background for content */
#             border-radius: 10px;
#             padding: 2rem;
#         }}
#         header {{
#             background-color: rgba(255, 255, 255, 0.0) !important; /* Transparent header background */
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )
# except FileNotFoundError:
# st.warning("Background image 'excelvizprocopy.jpg' not found. Skipping background.", icon="🖼️")


# Display the logo image
# try:
#     st.image("excelvizpro.png", width=200) # Adjust width as needed
# except FileNotFoundError:
# st.warning("Logo image 'excelvizpro.png' not found. Skipping logo.", icon="🖼️")


# --- Utility Function for Plot Download ---
def generate_html_download_link(fig, filename="plot.html"):
    """Generates a link to download a Plotly figure as an HTML file."""
    try:
        # Save plot to a BytesIO object
        buffer = io.StringIO()
        fig.write_html(buffer, include_plotlyjs="cdn")
        html_bytes = buffer.getvalue().encode()
        b64 = base64.b64encode(html_bytes).decode()
        href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}">Download Plot as HTML</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generating download link: {e}")
        return None

# --- Main Application ---
st.title('ExcelViz Pro 📈')
st.subheader('Upload your data file for analysis and visualization')

# Hide default Streamlit style elements if desired
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;} /* Optionally hide the header bar too */
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- File Uploader with Expanded File Types ---
uploaded_file = st.file_uploader(
    'Choose a file',
    type=['xlsx', 'csv', 'tsv', 'json'],
    help="Supports Excel (.xlsx), CSV (.csv), TSV (.tsv), and JSON (.json) files."
)

if uploaded_file:
    st.markdown('---')
    st.subheader('🔎 Data Preview & Visualization Options:')
    df = None
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == 'xlsx':
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension == 'tsv':
            df = pd.read_csv(uploaded_file, sep='\t')
        elif file_extension == 'json':
            try:
                df = pd.read_json(uploaded_file)
            except ValueError as e:
                st.error(f"Error reading JSON: {e}. Ensure JSON is in a format pandas can parse (e.g., records, table).")
                st.info("For JSON, try a structure like: `[{'col1':'val1', 'col2':'val2'}, {'col1':'val3', 'col2':'val4'}]`")
                st.stop()
        else:
            st.error("Unsupported file format. Please upload an XLSX, CSV, TSV, or JSON file.")
            st.stop()

        if df.empty:
            st.error("The uploaded file is empty or could not be parsed correctly.")
            st.stop()

        st.write("First 5 rows of your data:", df.head())

        # --- Automatic Insights (Suggestions for Automation) ---
        with st.expander("💡 Automated Data Insights (Suggestions)"):
            st.write("**Column Data Types:**")
            st.write(df.dtypes.astype(str))
            
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()

            if numeric_cols:
                st.write(f"**Numeric Columns Found:** `{', '.join(numeric_cols)}`")
                st.write("Consider using these for axes in line, bar, scatter, histogram, box plots.")
            if categorical_cols:
                st.write(f"**Categorical/Text Columns Found:** `{', '.join(categorical_cols)}`")
                st.write("Consider using these for grouping, categories in bar charts, or labels in pie charts.")
            if datetime_cols:
                st.write(f"**Date/Time Columns Found:** `{', '.join(datetime_cols)}`")
                st.write("Ideal for the X-axis in time series line charts.")
            
            if len(numeric_cols) >= 2:
                st.write(f"**Suggestion:** You have multiple numeric columns. Try a **Scatter Plot** to see relationships (e.g., '{numeric_cols[0]}' vs '{numeric_cols[1]}').")
            if numeric_cols and categorical_cols:
                st.write(f"**Suggestion:** Explore a **Box Plot** to see numeric distributions across categories (e.g., '{numeric_cols[0]}' by '{categorical_cols[0]}').")


        st.markdown('---')
        st.subheader("📊 Select Visualization Options")
        
        all_columns = df.columns.tolist()

        # --- Chart Type Selection ---
        chart_type = st.selectbox(
            "Select a chart type:",
            [
                "Line Chart", "Bar Chart", "Pie Chart", "Scatter Plot",
                "Histogram", "Box Plot", "Area Chart", "Funnel Chart",
                "Sunburst Chart", "Treemap", "Map (Geographical)"
            ]
        )
        
        fig = None # Initialize fig

        # --- Dynamic Column Selection Based on Chart Type ---
        
        if chart_type == "Line Chart":
            st.write("Select X-axis (often time-based) and one or more Y-axes (numeric).")
            x_axis_line = st.selectbox("Select X-Axis Column:", [None] + all_columns, key="line_x")
            y_axes_line = st.multiselect("Select Y-Axis Column(s) (must be numeric):",
                                         df.select_dtypes(include=['number']).columns.tolist(), key="line_y")
            if x_axis_line and y_axes_line:
                try:
                    fig = px.line(df, x=x_axis_line, y=y_axes_line, title=f'Line Chart: {", ".join(y_axes_line)} over {x_axis_line}')
                except Exception as e:
                    st.error(f"Error creating line chart: {e}")
            elif st.button("Generate Line Chart", key="gen_line"):
                st.warning("Please select X and Y axes for the Line Chart.")

        elif chart_type == "Bar Chart":
            st.write("Select a categorical X-axis and a numeric Y-axis.")
            x_bar = st.selectbox("Select X-Axis Column (Categorical/Dimension):", all_columns, key="bar_x")
            y_bar = st.selectbox("Select Y-Axis Column (Numeric/Measure):", df.select_dtypes(include=['number']).columns.tolist(), key="bar_y")
            color_bar = st.selectbox("Select Color Column (Optional, Categorical):", [None] + all_columns, key="bar_color")
            if x_bar and y_bar:
                try:
                    fig = px.bar(df, x=x_bar, y=y_bar, color=color_bar, title=f'Bar Chart: {y_bar} by {x_bar}')
                except Exception as e:
                    st.error(f"Error creating bar chart: {e}")
            elif st.button("Generate Bar Chart", key="gen_bar"):
                st.warning("Please select X and Y axes for the Bar Chart.")

        elif chart_type == "Pie Chart":
            st.write("Select a column for labels (categories) and a column for values (numeric).")
            labels_pie = st.selectbox("Select Labels Column (Categories):", all_columns, key="pie_labels")
            values_pie = st.selectbox("Select Values Column (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="pie_values")
            if labels_pie and values_pie:
                try:
                    fig = px.pie(df, names=labels_pie, values=values_pie, title=f'Pie Chart: {values_pie} by {labels_pie}')
                except Exception as e:
                    st.error(f"Error creating pie chart: {e}")
            elif st.button("Generate Pie Chart", key="gen_pie"):
                st.warning("Please select Labels and Values columns for the Pie Chart.")
        
        elif chart_type == "Scatter Plot":
            st.write("Select X and Y numeric columns. Optionally, add columns for color, size, or hover information.")
            x_scatter = st.selectbox("Select X-Axis Column (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="scatter_x")
            y_scatter = st.selectbox("Select Y-Axis Column (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="scatter_y")
            color_scatter = st.selectbox("Select Color Column (Optional, Categorical or Numeric):", [None] + all_columns, key="scatter_color")
            size_scatter = st.selectbox("Select Size Column (Optional, Numeric):", [None] + df.select_dtypes(include=['number']).columns.tolist(), key="scatter_size")
            hover_scatter = st.multiselect("Select Hover Data Columns (Optional):", all_columns, key="scatter_hover")
            
            if x_scatter and y_scatter:
                try:
                    fig = px.scatter(df, x=x_scatter, y=y_scatter, color=color_scatter, size=size_scatter, 
                                     hover_data=hover_scatter if hover_scatter else None,
                                     title=f'Scatter Plot: {y_scatter} vs. {x_scatter}')
                except Exception as e:
                    st.error(f"Error creating scatter plot: {e}")
            elif st.button("Generate Scatter Plot", key="gen_scatter"):
                st.warning("Please select X and Y axes for the Scatter Plot.")

        elif chart_type == "Histogram":
            st.write("Select a numeric column to see its distribution.")
            hist_col = st.selectbox("Select Column for Histogram (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="hist_col")
            color_hist = st.selectbox("Select Color Column (Optional, Categorical):", [None] + all_columns, key="hist_color")
            if hist_col:
                try:
                    fig = px.histogram(df, x=hist_col, color=color_hist, title=f'Histogram of {hist_col}')
                except Exception as e:
                    st.error(f"Error creating histogram: {e}")
            elif st.button("Generate Histogram", key="gen_hist"):
                st.warning("Please select a column for the Histogram.")

        elif chart_type == "Box Plot":
            st.write("Select one or more numeric columns to see their distribution. Optionally, group by a categorical column.")
            y_box = st.multiselect("Select Y-Axis Column(s) (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="box_y")
            x_box = st.selectbox("Select X-Axis Column (Optional, Categorical for Grouping):", [None] + all_columns, key="box_x")
            color_box = st.selectbox("Select Color Column (Optional, if X-axis is used for grouping):", [None] + all_columns, key="box_color") # Typically same as x_box or another category
            if y_box:
                try:
                    fig = px.box(df, y=y_box, x=x_box, color=color_box if x_box else None, title=f'Box Plot of {", ".join(y_box)}' + (f' by {x_box}' if x_box else ''))
                except Exception as e:
                    st.error(f"Error creating box plot: {e}")
            elif st.button("Generate Box Plot", key="gen_box"):
                st.warning("Please select at least one Y-axis column for the Box Plot.")
        
        elif chart_type == "Area Chart":
            st.write("Select X-axis (often time-based) and one or more Y-axes (numeric).")
            x_axis_area = st.selectbox("Select X-Axis Column:", [None] + all_columns, key="area_x")
            y_axes_area = st.multiselect("Select Y-Axis Column(s) (must be numeric):",
                                         df.select_dtypes(include=['number']).columns.tolist(), key="area_y")
            color_area = st.selectbox("Select Color Column (Optional, Categorical):", [None] + all_columns, key="area_color")                                         
            if x_axis_area and y_axes_area:
                try:
                    fig = px.area(df, x=x_axis_area, y=y_axes_area, color=color_area, title=f'Area Chart: {", ".join(y_axes_area)} over {x_axis_area}')
                except Exception as e:
                    st.error(f"Error creating area chart: {e}")
            elif st.button("Generate Area Chart", key="gen_area"):
                st.warning("Please select X and Y axes for the Area Chart.")

        elif chart_type == "Funnel Chart":
            st.write("Select a column for stages/categories and a column for corresponding numeric values.")
            x_funnel_values = st.selectbox("Select Values Column (Numeric, e.g., counts, amounts):", df.select_dtypes(include=['number']).columns.tolist(), key="funnel_x_val")
            y_funnel_stages = st.selectbox("Select Stages Column (Categorical):", all_columns, key="funnel_y_stages")
            if x_funnel_values and y_funnel_stages:
                try:
                    # Funnel charts usually expect aggregated data or data sorted by stage
                    # For simplicity, we plot directly. User might need to pre-process for meaningful funnel.
                    fig = px.funnel(df, x=x_funnel_values, y=y_funnel_stages, title=f'Funnel Chart: {x_funnel_values} by {y_funnel_stages}')
                except Exception as e:
                    st.error(f"Error creating funnel chart: {e}")
            elif st.button("Generate Funnel Chart", key="gen_funnel"):
                st.warning("Please select Values and Stages columns for the Funnel Chart.")
        
        elif chart_type == "Sunburst Chart":
            st.write("Select a path of categorical columns (from root to leaves) and a values column (numeric).")
            path_sunburst = st.multiselect("Select Path Columns (Categorical, Hierarchical):", all_columns, key="sunburst_path")
            values_sunburst = st.selectbox("Select Values Column (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="sunburst_values")
            if path_sunburst and values_sunburst:
                try:
                    fig = px.sunburst(df, path=path_sunburst, values=values_sunburst, title=f'Sunburst Chart by {", ".join(path_sunburst)}')
                except Exception as e:
                    st.error(f"Error creating sunburst chart: {e}. Ensure path columns create a valid hierarchy.")
            elif st.button("Generate Sunburst Chart", key="gen_sunburst"):
                st.warning("Please select Path and Values columns for the Sunburst Chart.")

        elif chart_type == "Treemap":
            st.write("Similar to Sunburst: select a path of categorical columns and a values column.")
            path_treemap = st.multiselect("Select Path Columns (Categorical, Hierarchical):", all_columns, key="treemap_path")
            values_treemap = st.selectbox("Select Values Column (Numeric):", df.select_dtypes(include=['number']).columns.tolist(), key="treemap_values")
            color_treemap = st.selectbox("Select Color Column (Optional, Numeric or Categorical):", [None] + all_columns, key="treemap_color")
            if path_treemap and values_treemap:
                try:
                    fig = px.treemap(df, path=path_treemap, values=values_treemap, color=color_treemap,
                                     title=f'Treemap by {", ".join(path_treemap)}')
                except Exception as e:
                    st.error(f"Error creating treemap: {e}. Ensure path columns create a valid hierarchy.")
            elif st.button("Generate Treemap", key="gen_treemap"):
                st.warning("Please select Path and Values columns for the Treemap.")
                
        elif chart_type == "Map (Geographical)":
            st.write("Select columns for Latitude and Longitude. Optionally, add columns for color, size, or hover text.")
            # Attempt to auto-detect lat/lon columns
            lat_guess = None
            lon_guess = None
            for col in df.columns:
                if 'lat' in col.lower() or 'latitude' in col.lower():
                    lat_guess = col
                if 'lon' in col.lower() or 'lng' in col.lower() or 'longitude' in col.lower():
                    lon_guess = col
            
            latitude_column = st.selectbox("Select Latitude Column:", all_columns, index=all_columns.index(lat_guess) if lat_guess in all_columns else 0, key="map_lat")
            longitude_column = st.selectbox("Select Longitude Column:", all_columns, index=all_columns.index(lon_guess) if lon_guess in all_columns else 1 if len(all_columns)>1 else 0, key="map_lon")
            color_map = st.selectbox("Select Color Column (Optional, Numeric or Categorical):", [None] + all_columns, key="map_color")
            size_map = st.selectbox("Select Size Column (Optional, Numeric):", [None] + df.select_dtypes(include=['number']).columns.tolist(), key="map_size")
            hover_map = st.multiselect("Select Hover Data Columns (Optional):", all_columns, key="map_hover")

            if latitude_column and longitude_column and pd.api.types.is_numeric_dtype(df[latitude_column]) and pd.api.types.is_numeric_dtype(df[longitude_column]):
                try:
                    # Basic Scatter Mapbox
                    fig = px.scatter_mapbox(df,
                                        lat=latitude_column,
                                        lon=longitude_column,
                                        color=color_map,
                                        size=size_map,
                                        hover_name=hover_map[0] if hover_map else None, # Use first hover col as name if available
                                        hover_data=hover_map[1:] if len(hover_map) > 1 else None,
                                        title='Geographical Map',
                                        zoom=3, # Default zoom
                                        height=600)
                    fig.update_layout(mapbox_style="open-street-map")
                    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
                except Exception as e:
                    st.error(f"Error creating map: {e}. Ensure latitude and longitude are numeric.")
            elif st.button("Generate Map", key="gen_map"):
                 st.warning("Please select valid numeric Latitude and Longitude columns.")


        # --- Display Plot and Download Link ---
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.subheader('Downloads:')
            generate_html_download_link(fig, filename=f"{chart_type.lower().replace(' ', '_')}_plot.html")
        else:
            st.info(f"Configure options for {chart_type} and the plot will appear here.")

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.exception(e) # Provides more detailed traceback for debugging

else:
    st.info("Awaiting for a file to be uploaded. ")
