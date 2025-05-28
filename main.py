import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="DataViz Pro 📊",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---

@st.cache_data(ttl=3600) # Cache data loading for 1 hour
def load_data(uploaded_file, sheet_name=None):
    """Loads data from various file types."""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == 'xlsx':
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            if sheet_name:
                return pd.read_excel(xls, sheet_name=sheet_name), sheet_names
            return pd.read_excel(xls, sheet_name=sheet_names[0]), sheet_names # Load first sheet by default
        elif file_extension == 'csv':
            return pd.read_csv(uploaded_file), None
        elif file_extension == 'tsv':
            return pd.read_csv(uploaded_file, sep='\t'), None
        elif file_extension == 'json':
            return pd.read_json(uploaded_file), None
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None, None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

def generate_download_link(df_or_fig, filename, text, is_figure=False):
    """Generates a download link for DataFrames (as CSV) or Plotly figures (as HTML)."""
    try:
        if is_figure:
            buffer = io.StringIO()
            df_or_fig.write_html(buffer, include_plotlyjs="cdn")
            data_bytes = buffer.getvalue().encode()
            mime_type = "text/html"
        else: # DataFrame
            csv = df_or_fig.to_csv(index=False).encode()
            data_bytes = csv
            mime_type = "text/csv"

        b64 = base64.b64encode(data_bytes).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{text}</a>'
        return href
    except Exception as e:
        st.error(f"Error generating download link: {e}")
        return ""

def get_column_types(df):
    """Separates columns by their general data type."""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'boolean']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols

# --- Initialize Session State ---
if 'df' not in st.session_state:
    st.session_state.df = None
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'sheet_names' not in st.session_state:
    st.session_state.sheet_names = None
if 'selected_sheet' not in st.session_state:
    st.session_state.selected_sheet = None

# --- Sidebar for File Upload and Sheet Selection ---
with st.sidebar:
    st.title("🖼️ DataViz Pro")
    st.markdown("Upload your data file and explore visualizations.")

    uploaded_file = st.file_uploader(
        "Choose a data file",
        type=['xlsx', 'csv', 'tsv', 'json'],
        help="Supports Excel, CSV, TSV, and JSON files."
    )

    if uploaded_file:
        if st.session_state.df is None or st.session_state.get('uploaded_file_name') != uploaded_file.name:
            st.session_state.uploaded_file_name = uploaded_file.name # track filename
            df_loaded, sheet_names_loaded = load_data(uploaded_file)
            st.session_state.df = df_loaded
            st.session_state.processed_df = df_loaded.copy() if df_loaded is not None else None
            st.session_state.sheet_names = sheet_names_loaded
            st.session_state.selected_sheet = sheet_names_loaded[0] if sheet_names_loaded else None

        if st.session_state.sheet_names and len(st.session_state.sheet_names) > 1:
            st.session_state.selected_sheet = st.selectbox(
                "Select Excel Sheet",
                st.session_state.sheet_names,
                index=st.session_state.sheet_names.index(st.session_state.selected_sheet) if st.session_state.selected_sheet in st.session_state.sheet_names else 0
            )
            if st.session_state.selected_sheet:
                # Reload data if sheet selection changes
                current_df_sheet_check, _ = load_data(uploaded_file, st.session_state.selected_sheet)
                # Check if dataframe from selected sheet is different from current df
                # This simple check might not be robust enough for all cases.
                # A more robust check would compare column names and dtypes or even content.
                if not st.session_state.df.equals(current_df_sheet_check):
                    st.session_state.df, _ = load_data(uploaded_file, st.session_state.selected_sheet)
                    st.session_state.processed_df = st.session_state.df.copy() if st.session_state.df is not None else None
                    st.experimental_rerun()


    if st.session_state.processed_df is not None:
        st.markdown("---")
        st.markdown(generate_download_link(st.session_state.processed_df, "processed_data.csv", "📥 Download Processed Data (CSV)"), unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.info("Built with Streamlit & Plotly.")

# --- Main Application Area ---
if st.session_state.processed_df is None:
    st.info("Please upload a data file using the sidebar to get started.")
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=300)

else:
    df = st.session_state.processed_df # Use the processed dataframe for all tabs
    numeric_cols, categorical_cols, datetime_cols = get_column_types(df)
    all_columns = df.columns.tolist()

    tab1, tab2, tab3 = st.tabs(["📖 Data Overview", "🛠️ Preprocessing", "📊 Visualization"])

    with tab1:
        st.header("Data Overview")
        st.subheader(f"Displaying: {st.session_state.selected_sheet if st.session_state.selected_sheet else uploaded_file.name}")

        st.dataframe(df.head(10))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Number of Rows", df.shape[0])
        with col2:
            st.metric("Number of Columns", df.shape[1])

        with st.expander("Column Details & Statistics"):
            st.write("**Column Data Types:**")
            st.dataframe(df.dtypes.astype(str).to_frame(name='Data Type'))
            st.write("**Descriptive Statistics (Numeric Columns):**")
            if numeric_cols:
                st.dataframe(df[numeric_cols].describe().T)
            else:
                st.info("No numeric columns found for descriptive statistics.")
            st.write("**Missing Values per Column:**")
            missing_values = df.isnull().sum().to_frame(name='Missing Count')
            missing_values = missing_values[missing_values['Missing Count'] > 0]
            if not missing_values.empty:
                st.dataframe(missing_values)
            else:
                st.success("No missing values found in the dataset! 🎉")


    with tab2:
        st.header("Data Preprocessing")
        st.info("Changes made here will reflect in the 'Visualization' tab. Original data remains unchanged until processing.")

        # Make a copy to ensure modifications in this tab don't affect the original st.session_state.df unintentionally before applying
        # df_to_process = st.session_state.processed_df.copy()

        st.subheader("1. Handle Missing Values")
        col_to_handle_na = st.selectbox("Select column with missing values:", [None] + all_columns, key="na_col_select")
        if col_to_handle_na and df[col_to_handle_na].isnull().any():
            st.write(f"Column '{col_to_handle_na}' has {df[col_to_handle_na].isnull().sum()} missing values.")
            na_strategy = st.selectbox("Choose strategy:", ["None", "Drop Rows with NA", "Fill with Mean (Numeric only)", "Fill with Median (Numeric only)", "Fill with Mode", "Fill with Custom Value"])

            custom_fill_value = None
            if na_strategy == "Fill with Custom Value":
                custom_fill_value = st.text_input("Enter custom value to fill NA:")

            if st.button("Apply NA Handling", key="apply_na"):
                df_copy = st.session_state.processed_df.copy() # Operate on the current state of processed_df
                if na_strategy == "Drop Rows with NA":
                    df_copy.dropna(subset=[col_to_handle_na], inplace=True)
                elif na_strategy == "Fill with Mean (Numeric only)":
                    if col_to_handle_na in numeric_cols:
                        df_copy[col_to_handle_na].fillna(df_copy[col_to_handle_na].mean(), inplace=True)
                    else:
                        st.error("Mean filling only applicable to numeric columns.")
                elif na_strategy == "Fill with Median (Numeric only)":
                    if col_to_handle_na in numeric_cols:
                        df_copy[col_to_handle_na].fillna(df_copy[col_to_handle_na].median(), inplace=True)
                    else:
                        st.error("Median filling only applicable to numeric columns.")
                elif na_strategy == "Fill with Mode":
                    df_copy[col_to_handle_na].fillna(df_copy[col_to_handle_na].mode()[0], inplace=True) # mode() can return multiple values
                elif na_strategy == "Fill with Custom Value" and custom_fill_value is not None:
                    try:
                        # Attempt to convert custom value to column's original type (simple approach)
                        original_dtype = df_copy[col_to_handle_na].dtype
                        converted_value = pd.Series([custom_fill_value]).astype(original_dtype).iloc[0]
                        df_copy[col_to_handle_na].fillna(converted_value, inplace=True)
                    except Exception as e:
                        st.error(f"Error converting custom value or filling: {e}. Try matching the column's data type.")
                st.session_state.processed_df = df_copy # Update session state
                st.success(f"NA handling '{na_strategy}' applied to '{col_to_handle_na}'.")
                st.experimental_rerun() # Rerun to reflect changes immediately
        elif col_to_handle_na:
            st.success(f"Column '{col_to_handle_na}' has no missing values.")


        st.subheader("2. Change Column Data Type")
        col_to_change_type = st.selectbox("Select column to change type:", [None] + all_columns, key="type_col_select")
        if col_to_change_type:
            current_type = df[col_to_change_type].dtype
            st.write(f"Current type of '{col_to_change_type}': **{current_type}**")
            new_type_str = st.selectbox("Select new data type:", ["None", "object (string)", "int64", "float64", "boolean", "datetime64[ns]"])

            if st.button("Apply Type Change", key="apply_type"):
                df_copy = st.session_state.processed_df.copy()
                try:
                    if new_type_str != "None":
                        if new_type_str == "datetime64[ns]":
                             df_copy[col_to_change_type] = pd.to_datetime(df_copy[col_to_change_type], errors='coerce')
                        else:
                             df_copy[col_to_change_type] = df_copy[col_to_change_type].astype(new_type_str)
                        st.session_state.processed_df = df_copy
                        st.success(f"Column '{col_to_change_type}' changed to {new_type_str}.")
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error changing type for '{col_to_change_type}': {e}")
        
        st.subheader("3. Reset Processed Data")
        if st.button("Reset to Original Uploaded Data", key="reset_data"):
            st.session_state.processed_df = st.session_state.df.copy() if st.session_state.df is not None else None
            st.success("Data reset to its original uploaded state.")
            st.experimental_rerun()


    with tab3:
        st.header("Data Visualization")
        if not all_columns:
            st.warning("No columns available for visualization. Check your data.")
        else:
            chart_type = st.selectbox(
                "Select Chart Type:",
                [
                    "Select...", "Line Chart", "Bar Chart", "Pie Chart", "Scatter Plot",
                    "Histogram", "Box Plot", "Area Chart", "Heatmap (Correlation)",
                    "Funnel Chart", "Sunburst Chart", "Treemap", "Map (Geographical)"
                ]
            )
            fig = None

            if chart_type == "Line Chart":
                x_ax = st.selectbox("X-axis (often Time/Index):", [None] + all_columns, key="line_x")
                y_ax_multi = st.multiselect("Y-axis (Numeric):", numeric_cols, key="line_y")
                color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_cols, key="line_color")
                if x_ax and y_ax_multi:
                    fig = px.line(df, x=x_ax, y=y_ax_multi, color=color_col, title=f"{', '.join(y_ax_multi)} over {x_ax}")

            elif chart_type == "Bar Chart":
                x_ax = st.selectbox("X-axis (Categorical/Dimension):", [None] + categorical_cols + datetime_cols, key="bar_x")
                y_ax = st.selectbox("Y-axis (Numeric/Measure):", [None] + numeric_cols, key="bar_y")
                color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_cols, key="bar_color")
                barmode = st.selectbox("Bar Mode (Optional):", ["group", "stack", "relative", "overlay"], index=0, key="bar_mode")
                if x_ax and y_ax:
                    fig = px.bar(df, x=x_ax, y=y_ax, color=color_col, title=f"{y_ax} by {x_ax}", barmode=barmode)

            elif chart_type == "Pie Chart":
                names_col = st.selectbox("Labels/Names (Categorical):", [None] + categorical_cols, key="pie_names")
                values_col = st.selectbox("Values (Numeric):", [None] + numeric_cols, key="pie_values")
                if names_col and values_col:
                    fig = px.pie(df, names=names_col, values=values_col, title=f"Distribution by {names_col}")

            elif chart_type == "Scatter Plot":
                x_ax = st.selectbox("X-axis (Numeric):", [None] + numeric_cols + datetime_cols, key="scatter_x")
                y_ax = st.selectbox("Y-axis (Numeric):", [None] + numeric_cols, key="scatter_y")
                color_col = st.selectbox("Color by (Optional):", [None] + all_columns, key="scatter_color")
                size_col = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_cols, key="scatter_size")
                if x_ax and y_ax:
                    fig = px.scatter(df, x=x_ax, y=y_ax, color=color_col, size=size_col, title=f"{y_ax} vs {x_ax}")

            elif chart_type == "Histogram":
                x_ax = st.selectbox("Column to plot (Numeric):", [None] + numeric_cols, key="hist_x")
                color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_cols, key="hist_color")
                nbins = st.slider("Number of Bins (Optional):", 5, 100, 20, key="hist_bins")
                if x_ax:
                    fig = px.histogram(df, x=x_ax, color=color_col, nbins=nbins, title=f"Distribution of {x_ax}")

            elif chart_type == "Box Plot":
                y_ax = st.multiselect("Y-axis / Values (Numeric):", numeric_cols, key="box_y")
                x_ax = st.selectbox("X-axis / Categories (Categorical, Optional):", [None] + categorical_cols + datetime_cols, key="box_x")
                color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_cols, key="box_color")
                if y_ax:
                    fig = px.box(df, y=y_ax, x=x_ax, color=color_col, title="Box Plot")

            elif chart_type == "Area Chart":
                x_ax = st.selectbox("X-axis (often Time/Index):", [None] + all_columns, key="area_x")
                y_ax_multi = st.multiselect("Y-axis (Numeric):", numeric_cols, key="area_y")
                color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_cols, key="area_color")
                if x_ax and y_ax_multi:
                    fig = px.area(df, x=x_ax, y=y_ax_multi, color=color_col, title=f"Area chart of {', '.join(y_ax_multi)} over {x_ax}")

            elif chart_type == "Heatmap (Correlation)":
                st.info("This heatmap shows the Pearson correlation between numeric columns.")
                if len(numeric_cols) > 1:
                    corr_matrix = df[numeric_cols].corr()
                    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", title="Correlation Heatmap")
                else:
                    st.warning("At least two numeric columns are needed for a correlation heatmap.")
            
            elif chart_type in ["Sunburst Chart", "Treemap"]:
                path_cols = st.multiselect(f"Path / Hierarchy (Categorical, from root to leaf):", categorical_cols, key=f"{chart_type}_path")
                values_col = st.selectbox(f"Values (Numeric):", [None] + numeric_cols, key=f"{chart_type}_values")
                color_col = st.selectbox(f"Color by (Optional):", [None] + all_columns, key=f"{chart_type}_color") # Can be numeric for continuous color or categorical
                if path_cols and values_col:
                    if chart_type == "Sunburst Chart":
                        fig = px.sunburst(df, path=path_cols, values=values_col, color=color_col, title=f"Sunburst: {values_col} by {', '.join(path_cols)}")
                    else: # Treemap
                        fig = px.treemap(df, path=path_cols, values=values_col, color=color_col, title=f"Treemap: {values_col} by {', '.join(path_cols)}")
            
            elif chart_type == "Funnel Chart":
                x_values = st.selectbox("Values (Numeric, e.g., counts at each stage):", [None] + numeric_cols, key="funnel_x")
                y_stages = st.selectbox("Stages (Categorical):", [None] + categorical_cols, key="funnel_y")
                color_stages = st.selectbox("Color by Stages (Optional, usually same as Y-axis):", [None] + categorical_cols, key="funnel_color")
                if x_values and y_stages:
                     # For a meaningful funnel, data usually needs to be sorted by stage or be aggregated.
                    # This simple version plots directly.
                    fig = px.funnel(df, x=x_values, y=y_stages, color=color_stages if color_stages else y_stages, title=f"Funnel: {x_values} by {y_stages}")


            elif chart_type == "Map (Geographical)":
                st.info("Requires columns with Latitude and Longitude data.")
                lat_col_options = [None] + numeric_cols
                lon_col_options = [None] + numeric_cols

                # Attempt to pre-select common names
                lat_guess = next((c for c in numeric_cols if 'lat' in c.lower()), None)
                lon_guess = next((c for c in numeric_cols if 'lon' in c.lower() or 'lng' in c.lower()), None)

                lat_idx = lat_col_options.index(lat_guess) if lat_guess else 0
                lon_idx = lon_col_options.index(lon_guess) if lon_guess else (1 if len(lon_col_options) > 1 else 0)


                lat_col = st.selectbox("Latitude Column (Numeric):", lat_col_options, index=lat_idx, key="map_lat")
                lon_col = st.selectbox("Longitude Column (Numeric):", lon_col_options, index=lon_idx, key="map_lon")
                color_col = st.selectbox("Color by (Optional):", [None] + all_columns, key="map_color")
                size_col = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_cols, key="map_size")
                hover_name_col = st.selectbox("Hover Label (Optional):", [None] + all_columns, key="map_hover_name")
                
                if lat_col and lon_col:
                    df_map = df.dropna(subset=[lat_col, lon_col]) # Drop rows where lat/lon is NA
                    if not df_map.empty:
                        fig = px.scatter_mapbox(df_map, lat=lat_col, lon=lon_col, color=color_col, size=size_col,
                                                hover_name=hover_name_col,
                                                mapbox_style="open-street-map", zoom=2, height=600,
                                                title="Geographical Map")
                        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
                    else:
                        st.warning("No valid data points after removing NA from latitude/longitude columns.")


            # Display the plot and download link
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                download_filename = f"{chart_type.lower().replace(' ', '_')}_plot.html"
                st.markdown(generate_download_link(fig, download_filename, f"📥 Download '{chart_type}' Plot (HTML)", is_figure=True), unsafe_allow_html=True)
            elif chart_type != "Select...":
                st.info("Configure the chart options above to generate a visualization.")
