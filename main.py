import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io # For in-memory file handling for download

# --- Page Configuration ---
st.set_page_config(
    page_title='ExcelViz Pro (Refined)',
    page_icon='📊', # Simple and relevant
    layout='centered', # Changed to centered for a cleaner, focused look
    initial_sidebar_state='collapsed' # Keep sidebar less intrusive initially
)

# --- Styling (Inspired by your style.css and aiming for clean/nice) ---
# Primary green from your style.css: #1a7707
# Let's use a slightly lighter shade for better Streamlit component compatibility if needed
PRIMARY_ACCENT_COLOR = "#1DB954" # A nice, modern green (Spotify-like)
TEXT_COLOR = "#333333"
BACKGROUND_COLOR = "#f0f2f6" # Light grey, common for clean UIs
CONTAINER_BACKGROUND = "#FFFFFF"

st.markdown(f"""
<style>
    /* General App Styling */
    .stApp {{
        background-color: {BACKGROUND_COLOR};
    }}

    /* Main content block */
    [data-testid="block-container"] {{
        padding: 2rem 2rem 3rem 2rem; /* More padding */
        background-color: {CONTAINER_BACKGROUND};
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); /* Subtle shadow */
    }}

    /* Titles and Headers */
    h1, h2, h3 {{
        color: {PRIMARY_ACCENT_COLOR};
        font-family: 'Poppins', sans-serif; /* Assuming Poppins might be available via browser/OS */
    }}
    
    .stButton>button {{
        background-color: {PRIMARY_ACCENT_COLOR};
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #1AA34A; /* Darker shade on hover */
    }}
    .stButton>button:active {{
        background-color: #178B40; /* Even darker on click */
    }}

    /* Style for selectbox and multiselect */
    .stSelectbox, .stMultiSelect {{
        /* Add custom styling if desired, e.g., for borders or background */
    }}
    
    /* Hide Streamlit's default menu and footer for a cleaner look */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

</style>
""", unsafe_allow_html=True)


# --- Utility Function for Plot Download (Improved) ---
def generate_html_download_link(fig, filename="visualization.html"):
    """Generates a link to download a Plotly figure as an HTML file."""
    try:
        # Save plot to a BytesIO object for in-memory handling
        buffer = io.StringIO()
        fig.write_html(buffer, include_plotlyjs="cdn")
        html_bytes = buffer.getvalue().encode()
        
        b64 = base64.b64encode(html_bytes).decode()
        
        # Nicer download button style
        button_style = f"background-color:{PRIMARY_ACCENT_COLOR};color:white;padding:10px 20px;text-align:center;text-decoration:none;display:inline-block;border-radius:8px;border:none;font-weight:bold;margin-top:10px;"
        hover_style = f"background-color:#1AA34A;" # Darker shade for hover

        href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" style="{button_style}" onmouseover="this.style.backgroundColor=\'{hover_style}\'" onmouseout="this.style.backgroundColor=\'{PRIMARY_ACCENT_COLOR}\'">Download Visualization</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generating download link: {e}")
        return None

# --- Main Application ---
st.title('ExcelViz Pro 📈')
st.markdown('Upload your Excel or CSV file, select columns, and visualize your data easily!')
st.markdown("---") # Visual separator

# --- File Uploader ---
uploaded_file = st.file_uploader(
    'Choose a data file',
    type=['xlsx', 'csv', 'xls'], # Added .xls support, assuming xlrd might be installed by user if needed
    help="Supports .xlsx, .xls, and .csv files."
)

if uploaded_file:
    st.markdown('---')
    st.header('📊 Data Analysis and Visualization')
    
    df = None
    fig = None # Initialize fig outside conditional blocks

    try:
        file_name = uploaded_file.name
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_name.endswith('.xls'):
            # For .xls, pandas will try to use xlrd. User needs to have it installed.
            try:
                df = pd.read_excel(uploaded_file) # engine=None lets pandas decide
            except ImportError:
                st.error("To read .xls files, please install the 'xlrd' library (e.g., pip install xlrd).")
                st.stop()
            except Exception as e:
                st.error(f"Error reading .xls file: {e}")
                st.stop()
        elif file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        
        if df is None: # If df wasn't loaded for any reason (e.g. unsupported extension if type list was broader)
            st.error("Unsupported file format or error during upload. Please upload an XLSX, XLS or CSV file.")
            st.stop()

        if df.empty:
            st.warning("The uploaded file is empty or could not be parsed correctly.")
            st.stop()

        with st.expander("Preview Data", expanded=False):
            st.dataframe(df.head(), use_container_width=True)

        st.markdown("#### 1. Select Columns for Visualization")
        # Allow selecting multiple columns for Y-axis in line/bar if desired, or single for others
        # For simplicity, let's stick to the original's single column approach for most unless specified.
        all_columns = df.columns.tolist()
        numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
        categorical_columns = df.select_dtypes(include='object').columns.tolist()
        
        # Simplified column selection inspired by the original's directness
        # Column selection will be inside each chart type for clarity

        st.markdown("#### 2. Choose Chart Type & Options")
        chart_type_options = ["Line Chart", "Bar Chart", "Pie Chart", "Scatter Plot", "Map"]
        chart_type = st.selectbox("Select a chart type:", chart_type_options)

        # Input for custom chart title
        custom_title = st.text_input("Enter a custom chart title (optional):")


        # --- Chart Generation Logic ---
        if chart_type == "Line Chart":
            st.markdown("##### Line Chart Options")
            if not numeric_columns:
                st.warning("Line charts require numeric data. Please select numeric columns.")
            else:
                x_axis_line = st.selectbox("Select X-Axis Column (Optional, uses index if None):", [None] + all_columns, key="line_x")
                y_axis_line = st.selectbox("Select Y-Axis Column (Numeric):", numeric_columns, key="line_y")
                color_by_line = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_columns, key="line_color")

                if y_axis_line: # Y-axis is mandatory
                    title = custom_title if custom_title else f'{y_axis_line} Line Chart'
                    try:
                        fig = px.line(df, 
                                      x=x_axis_line if x_axis_line else df.index, 
                                      y=y_axis_line, 
                                      color=color_by_line,
                                      title=title,
                                      labels={y_axis_line: y_axis_line, x_axis_line if x_axis_line else "Index": x_axis_line if x_axis_line else "Index"}
                                     )
                    except Exception as e:
                        st.error(f"Error creating line chart: {e}")
                else:
                    st.info("Please select a Y-Axis column for the Line Chart.")
        
        elif chart_type == "Bar Chart":
            st.markdown("##### Bar Chart Options")
            if not (numeric_columns and (categorical_columns or all_columns)):
                 st.warning("Bar charts typically require a categorical X-axis and a numeric Y-axis.")
            else:
                x_axis_bar = st.selectbox("Select X-Axis Column (Categorical/Dimension):", categorical_columns or all_columns, key="bar_x")
                y_axis_bar = st.selectbox("Select Y-Axis Column (Numeric/Measure):", numeric_columns, key="bar_y")
                color_by_bar = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_columns, key="bar_color")

                if x_axis_bar and y_axis_bar:
                    title = custom_title if custom_title else f'Bar Chart: {y_axis_bar} by {x_axis_bar}'
                    try:
                        fig = px.bar(df, 
                                     x=x_axis_bar, 
                                     y=y_axis_bar, 
                                     color=color_by_bar,
                                     title=title,
                                     labels={y_axis_bar: y_axis_bar, x_axis_bar: x_axis_bar}
                                    )
                    except Exception as e:
                        st.error(f"Error creating bar chart: {e}")
                else:
                    st.info("Please select X-Axis and Y-Axis columns for the Bar Chart.")

        elif chart_type == "Pie Chart":
            st.markdown("##### Pie Chart Options")
            if not (numeric_columns and categorical_columns):
                 st.warning("Pie charts require a categorical column for labels and a numeric column for values.")
            else:
                labels_pie = st.selectbox("Select Labels Column (Categories):", categorical_columns, key="pie_labels")
                values_pie = st.selectbox("Select Values Column (Numeric):", numeric_columns, key="pie_values")

                if labels_pie and values_pie:
                    title = custom_title if custom_title else f'Pie Chart: {values_pie} by {labels_pie}'
                    try:
                        fig = px.pie(df, 
                                     names=labels_pie, 
                                     values=values_pie, 
                                     title=title
                                    )
                    except Exception as e:
                        st.error(f"Error creating pie chart: {e}")
                else:
                    st.info("Please select Labels and Values columns for the Pie Chart.")
        
        elif chart_type == "Scatter Plot":
            st.markdown("##### Scatter Plot Options")
            if len(numeric_columns) < 2:
                st.warning("Scatter plots require at least two numeric columns for X and Y axes.")
            else:
                x_axis_scatter = st.selectbox("Select X-Axis Column (Numeric):", numeric_columns, key="scatter_x")
                # Ensure y_axis default is different from x_axis if possible
                available_y_scatter = [col for col in numeric_columns if col != x_axis_scatter]
                if not available_y_scatter and len(numeric_columns)>0: available_y_scatter = numeric_columns # fallback if only one num col
                
                y_axis_scatter = st.selectbox("Select Y-Axis Column (Numeric):", available_y_scatter or numeric_columns, key="scatter_y")
                color_by_scatter = st.selectbox("Color by (Optional):", [None] + all_columns, key="scatter_color")
                size_by_scatter = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_columns, key="scatter_size")

                if x_axis_scatter and y_axis_scatter:
                    title = custom_title if custom_title else f'Scatter Plot: {y_axis_scatter} vs. {x_axis_scatter}'
                    try:
                        fig = px.scatter(df, 
                                         x=x_axis_scatter, 
                                         y=y_axis_scatter, 
                                         color=color_by_scatter,
                                         size=size_by_scatter,
                                         title=title,
                                         labels={y_axis_scatter: y_axis_scatter, x_axis_scatter: x_axis_scatter}
                                        )
                    except Exception as e:
                        st.error(f"Error creating scatter plot: {e}")
                else:
                    st.info("Please select X-Axis and Y-Axis columns for the Scatter Plot.")
            
        elif chart_type == "Map":
            st.markdown("##### Map Options")
            st.info("For Map visualization, ensure your data has columns for Latitude and Longitude.")
            
            # Guess common names for lat/lon
            lat_guess = next((col for col in all_columns if 'lat' in col.lower()), None)
            lon_guess = next((col for col in all_columns if 'lon' in col.lower() or 'lng' in col.lower()), None)
            
            lat_idx = all_columns.index(lat_guess) if lat_guess else 0
            lon_idx = all_columns.index(lon_guess) if lon_guess else (1 if len(all_columns)>1 else 0)

            latitude_column = st.selectbox("Select Latitude Column:", all_columns, index=lat_idx, key="map_lat")
            longitude_column = st.selectbox("Select Longitude Column:", all_columns, index=lon_idx, key="map_lon")
            color_by_map = st.selectbox("Color by (Optional):", [None] + all_columns, key="map_color_val")
            size_by_map = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_columns, key="map_size_val")
            hover_name_map = st.selectbox("Hover Name (Label for points, Optional):", [None] + all_columns, key="map_hover")

            if latitude_column and longitude_column:
                # Check if selected lat/lon columns are numeric
                if not (pd.api.types.is_numeric_dtype(df[latitude_column]) and pd.api.types.is_numeric_dtype(df[longitude_column])):
                    st.warning("Latitude and Longitude columns must be numeric.")
                else:
                    title = custom_title if custom_title else 'Geographical Map'
                    try:
                        fig = px.scatter_mapbox(df,
                                                lat=latitude_column,
                                                lon=longitude_column,
                                                color=color_by_map,
                                                size=size_by_map,
                                                hover_name=hover_name_map,
                                                title=title,
                                                mapbox_style="open-street-map",
                                                zoom=3,
                                                height=500
                                               )
                        fig.update_layout(margin={"r":0,"t":35,"l":0,"b":0})
                    except Exception as e:
                        st.error(f"Error creating map: {e}")
            else:
                st.info("Please select Latitude and Longitude columns for the Map.")


        # --- Display Plot and Download Link ---
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("#### 3. Download Visualization")
            generate_html_download_link(fig, filename=f"{chart_type.lower().replace(' ', '_')}_visualization.html")
        else:
            st.info("Configure options above to generate a visualization.")

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.exception(e) # Shows detailed traceback for debugging

else:
    st.info("👆 Upload a data file to get started!")
