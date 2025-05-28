import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import numpy as np # For sample data and potential calculations

# --- Page Configuration ---
st.set_page_config(
    page_title='ExcelViz Pro - Platinum Edition',
    page_icon='💎',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- Initialize Session State ---
DEFAULT_SESSION_STATE = {
    'df': None,
    'uploaded_file_name': None,
    'chart_options': {}, # Stores parameters for each chart type
    'last_chart_type': "",
    'active_df_name': "No data loaded", # To show if it's uploaded or sample
    'data_processing_applied': False # Flag to track if processing happened
}
for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Styling (from previous versions) ---
PRIMARY_COLOR = "#1a7707"
SECONDARY_COLOR = "#1605b1"
TEXT_COLOR_DARK = "#333333"
BACKGROUND_COLOR_LIGHT = "#f8f9fa"
ACCENT_BACKGROUND = "#e9f5e9"

custom_css = f"""
<style>
    /* General App Styling */
    .stApp {{ /* background-color: {BACKGROUND_COLOR_LIGHT}; */ }}
    .css-1d391kg {{ background-color: {BACKGROUND_COLOR_LIGHT}; border-right: 1px solid #ddd; }}
    .stButton>button {{
        border: 1px solid {PRIMARY_COLOR}; background-color: white; color: {PRIMARY_COLOR};
        padding: 0.4rem 0.8rem; border-radius: 8px; transition: all 0.3s ease-in-out; font-weight: 500;
    }}
    .stButton>button:hover {{ border-color: {SECONDARY_COLOR}; background-color: {ACCENT_BACKGROUND}; color: {PRIMARY_COLOR}; }}
    .stButton>button:active {{ background-color: {PRIMARY_COLOR}; color: white; }}
    h1, h2 {{ color: {PRIMARY_COLOR}; font-family: 'Poppins', sans-serif; }}
    h3 {{ color: {TEXT_COLOR_DARK}; font-family: 'Poppins', sans-serif; }}
    .stMarkdown a {{ color: {SECONDARY_COLOR}; text-decoration: none; }}
    .stMarkdown a:hover {{ text-decoration: underline; color: {PRIMARY_COLOR}; }}
    .stFileUploader label {{
        background-color: {ACCENT_BACKGROUND}; border: 2px dashed {PRIMARY_COLOR};
        padding: 1rem; border-radius: 8px; text-align: center; transition: all 0.3s ease-in-out;
    }}
    .stFileUploader label:hover {{ border-color: {SECONDARY_COLOR}; background-color: #d4eed4; }}
    .streamlit-expanderHeader {{ font-size: 1.1rem; color: {PRIMARY_COLOR}; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Utility Functions ---
def generate_html_download_link(fig, filename="plot.html"):
    try:
        buffer = io.StringIO()
        fig.write_html(buffer, include_plotlyjs="cdn")
        html_bytes = buffer.getvalue().encode()
        b64 = base64.b64encode(html_bytes).decode()
        button_style = f"background-color:{PRIMARY_COLOR};color:white;padding:10px 15px;text-align:center;text-decoration:none;display:inline-block;border-radius:8px;border:none;font-weight:500;transition:all 0.3s ease;"
        href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" style="{button_style}" onmouseover="this.style.backgroundColor=\'{SECONDARY_COLOR}\'" onmouseout="this.style.backgroundColor=\'{PRIMARY_COLOR}\'">Download Plot as HTML</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e: st.error(f"Error generating plot download link: {e}"); return None

def df_to_csv_download_link(df, filename="processed_data.csv"):
    try:
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        button_style = f"background-color:{SECONDARY_COLOR};color:white;padding:10px 15px;text-align:center;text-decoration:none;display:inline-block;border-radius:8px;border:none;font-weight:500;transition:all 0.3s ease;"
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="{button_style}" onmouseover="this.style.backgroundColor=\'{PRIMARY_COLOR}\'" onmouseout="this.style.backgroundColor=\'{SECONDARY_COLOR}\'">Download Processed Data as CSV</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e: st.error(f"Error generating CSV download link: {e}"); return None

def get_selection(chart_type_key, param_key, default_value=None, options_list=None):
    if chart_type_key in st.session_state.chart_options:
        value = st.session_state.chart_options[chart_type_key].get(param_key, default_value)
        if options_list and value not in options_list:
            if default_value in options_list: return default_value
            elif options_list: return options_list[0] if options_list else None # Check if options_list is not empty
        return value
    return default_value

# --- Sample Datasets ---
def load_sample_data(dataset_name):
    if dataset_name == "Iris":
        return px.data.iris(), "Sample: Iris Dataset"
    elif dataset_name == "Tips":
        return px.data.tips(), "Sample: Tips Dataset"
    elif dataset_name == "Gapminder (subset)":
        df = px.data.gapminder()
        return df[df['year'].isin([2002, 2007])], "Sample: Gapminder (2002 & 2007)"
    return None, None

# --- Sidebar ---
with st.sidebar:
    # Logo and Title
    st.markdown(f"<p style='text-align:center;'><img src='https://www.gstatic.com/images/branding/googlelogo/svg/googlelogo_clr_74x24px.svg' alt='ExcelVizPro Logo Placeholder' width='120'></p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='color: {PRIMARY_COLOR}; text-align: center; margin-top:0px;'>ExcelViz Pro</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Data Input Section
    st.header("💾 Data Input")
    data_source_option = st.radio("Choose data source:", ("Upload File", "Load Sample Dataset"), key="data_source_type")

    if data_source_option == "Upload File":
        uploaded_file = st.file_uploader('Choose a file (XLSX, CSV, TSV, JSON)', type=['xlsx', 'xls', 'csv', 'tsv', 'json'], help="Supports Excel, CSV, TSV, and JSON files.")
        if uploaded_file:
            if st.session_state.uploaded_file_name != uploaded_file.name or not isinstance(st.session_state.df, pd.DataFrame):
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.df = None; st.session_state.chart_options = {}; st.session_state.data_processing_applied = False
                try:
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    if file_extension == 'xlsx': st.session_state.df = pd.read_excel(uploaded_file, engine='openpyxl')
                    elif file_extension == 'xls': st.session_state.df = pd.read_excel(uploaded_file, engine='xlrd') # Added xlrd support
                    elif file_extension == 'csv': st.session_state.df = pd.read_csv(uploaded_file)
                    elif file_extension == 'tsv': st.session_state.df = pd.read_csv(uploaded_file, sep='\t')
                    elif file_extension == 'json': st.session_state.df = pd.read_json(uploaded_file, orient='records', lines=True)
                    st.session_state.active_df_name = f"Uploaded: {uploaded_file.name}"
                    st.success(f"File '{uploaded_file.name}' loaded!")
                except Exception as e: st.error(f"Error loading file: {e}"); st.session_state.df = None
    
    elif data_source_option == "Load Sample Dataset":
        sample_dataset_name = st.selectbox("Select a sample dataset:", ["Iris", "Tips", "Gapminder (subset)"], key="sample_data_selector")
        if st.button("Load Sample", key="load_sample_btn"):
            st.session_state.df, active_name = load_sample_data(sample_dataset_name)
            st.session_state.active_df_name = active_name
            st.session_state.uploaded_file_name = None # Clear uploaded file name
            st.session_state.chart_options = {}; st.session_state.data_processing_applied = False
            if st.session_state.df is not None: st.success(f"'{sample_dataset_name}' dataset loaded!")
            else: st.error("Failed to load sample dataset.")

    st.markdown("---")
    # About & Help Section (from previous version)
    st.header("ℹ️ About & Help")
    # ... (Keep the expanders for About & FAQs from the "Master Edition")
    with st.expander("About ExcelViz Pro", expanded=False):
        st.markdown("""**ExcelViz Pro** empowers you to effortlessly transform raw data into compelling, insightful visualizations...""")
    with st.expander("Frequently Asked Questions (FAQs)", expanded=False):
        st.markdown("""**Q: How do I use ExcelVizPro?** ...""")


    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: {TEXT_COLOR_DARK}; font-size: 0.9em;'>© 2023-2024 ExcelVizPro Team</p>", unsafe_allow_html=True)


# --- Main Content Area ---
if st.session_state.df is not None:
    df = st.session_state.df # Local reference for convenience

    st.header("✨ Data Dashboard & Visualizer ✨")
    st.markdown(f"Current Dataset: **{st.session_state.active_df_name}** (`{df.shape[0]}` rows, `{df.shape[1]}` columns)")
    if st.session_state.data_processing_applied:
        st.info("Data processing has been applied. Download the processed data using the button below the chart.")

    # --- Data Preprocessing Section ---
    with st.expander("🛠️ Data Preprocessing Tools", expanded=False):
        st.subheader("Handle Missing Values")
        missing_summary = df.isnull().sum()
        missing_summary = missing_summary[missing_summary > 0]
        if not missing_summary.empty:
            st.write("Missing values per column:", missing_summary)
            
            col_to_fill = st.selectbox("Select column to process for missing values:", missing_summary.index.tolist(), key="mv_col_select")
            
            mv_options = ["Remove rows with missing values (in selected column)", 
                          "Impute with Mean (numeric only)", 
                          "Impute with Median (numeric only)", 
                          "Impute with Mode", 
                          "Impute with Custom Value"]
            mv_action = st.selectbox("Action:", mv_options, key="mv_action_select")

            custom_val = None
            if mv_action == "Impute with Custom Value":
                custom_val = st.text_input(f"Enter custom value for {col_to_fill}:", key="mv_custom_val")

            if st.button("Apply Missing Value Action", key="mv_apply_btn"):
                df_processed = df.copy()
                if mv_action == "Remove rows with missing values (in selected column)":
                    df_processed.dropna(subset=[col_to_fill], inplace=True)
                elif mv_action == "Impute with Mean (numeric only)":
                    if pd.api.types.is_numeric_dtype(df_processed[col_to_fill]):
                        df_processed[col_to_fill].fillna(df_processed[col_to_fill].mean(), inplace=True)
                    else: st.warning(f"{col_to_fill} is not numeric. Mean imputation not applied.")
                elif mv_action == "Impute with Median (numeric only)":
                    if pd.api.types.is_numeric_dtype(df_processed[col_to_fill]):
                        df_processed[col_to_fill].fillna(df_processed[col_to_fill].median(), inplace=True)
                    else: st.warning(f"{col_to_fill} is not numeric. Median imputation not applied.")
                elif mv_action == "Impute with Mode":
                    df_processed[col_to_fill].fillna(df_processed[col_to_fill].mode()[0], inplace=True) # mode() can return multiple, take first
                elif mv_action == "Impute with Custom Value" and custom_val is not None:
                    try: # Attempt to convert custom_val to column's original type if possible
                        original_type = df[col_to_fill].dtype
                        converted_val = pd.Series([custom_val]).astype(original_type)[0]
                        df_processed[col_to_fill].fillna(converted_val, inplace=True)
                    except Exception as e_conv:
                        st.warning(f"Could not convert '{custom_val}' to {original_type}, filling as string. Error: {e_conv}")
                        df_processed[col_to_fill].fillna(custom_val, inplace=True)
                
                st.session_state.df = df_processed
                st.session_state.data_processing_applied = True
                st.success(f"Missing value action '{mv_action}' applied to column '{col_to_fill}'.")
                st.rerun() # Rerun to reflect changes in dataframe immediately

        else: st.info("No missing values found in the dataset.")
        st.markdown("---")
        st.subheader("Change Column Data Type")
        col_to_change_type = st.selectbox("Select column to change data type:", df.columns, key="dt_col_select")
        current_type = df[col_to_change_type].dtype
        st.write(f"Current data type of '{col_to_change_type}': **{current_type}**")
        
        new_type_options = {"Numeric (Float)": 'float64', "Numeric (Integer)": 'int64', "Text/String": 'object', 
                            "Category": 'category', "Boolean": 'bool', "Date/Time": 'datetime64[ns]'}
        new_type_display = st.selectbox("Select new data type:", list(new_type_options.keys()), key="dt_new_type_select")
        
        if st.button("Apply Data Type Change", key="dt_apply_btn"):
            selected_new_type = new_type_options[new_type_display]
            try:
                df_processed = df.copy()
                if selected_new_type == 'datetime64[ns]':
                    df_processed[col_to_change_type] = pd.to_datetime(df_processed[col_to_change_type], errors='coerce')
                else:
                    df_processed[col_to_change_type] = df_processed[col_to_change_type].astype(selected_new_type)
                st.session_state.df = df_processed
                st.session_state.data_processing_applied = True
                st.success(f"Data type of '{col_to_change_type}' changed to '{selected_new_type}'.")
                st.rerun()
            except Exception as e_type: st.error(f"Error changing data type for '{col_to_change_type}': {e_type}")


    # --- Data Preview and Basic Analysis ---
    with st.expander("🧐 Data Preview & Quick Insights", expanded=False):
        # ... (same as "Master Edition", ensure it uses st.session_state.df) ...
        st.dataframe(st.session_state.df.head())
        # ... (Descriptive Stats, Column Types) ...


    st.markdown("---")
    st.subheader("⚙️ Configure Your Visualization")
    # ... (Chart Type and Theme Selection from "Master Edition") ...
    control_col1, control_col2 = st.columns([3, 2])
    with control_col1: chart_type = st.selectbox("Select Chart Type:", ["Line Chart", "Bar Chart", "Pie Chart", "Scatter Plot", "Histogram", "Box Plot", "Area Chart", "Funnel Chart", "Sunburst Chart", "Treemap", "Map (Geographical)", "Correlation Heatmap"], key='chart_type_selector', index=0)
    with control_col2: plotly_theme = st.selectbox("Select Plotly Theme:", ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white", None], key='plotly_theme_selector', index=1)
    
    if st.session_state.last_chart_type != chart_type:
        st.session_state.chart_options[chart_type] = {}
        st.session_state.last_chart_type = chart_type

    st.markdown("**Advanced Customization:**")
    cust_col1, cust_col2, cust_col3 = st.columns(3)
    default_title = f"{chart_type} of {st.session_state.active_df_name.replace('Sample: ', '').replace('Uploaded: ', '').split('.')[0]}"
    with cust_col1: chart_title = st.text_input("Chart Title:", value=get_selection(chart_type, "chart_title", default_title), key=f'{chart_type}_title_input')
    with cust_col2: x_axis_label_val = st.text_input("X-Axis Label (Optional):", value=get_selection(chart_type, "x_axis_label", ""), key=f'{chart_type}_x_label_input')
    with cust_col3: y_axis_label_val = st.text_input("Y-Axis Label (Optional):", value=get_selection(chart_type, "y_axis_label", ""), key=f'{chart_type}_y_label_input')

    # --- Dynamic Column Selection and Plotting Logic ---
    fig = None; all_columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=np.number).columns.tolist() # More robust numeric detection
    categorical_columns = df.select_dtypes(include=['object', 'category', 'boolean']).columns.tolist()
    
    if chart_type not in st.session_state.chart_options: st.session_state.chart_options[chart_type] = {}
    current_chart_opts = st.session_state.chart_options[chart_type]
    plot_kwargs = {"title": chart_title, "template": plotly_theme, "labels": {}}
    
    def first_or_none(lst): return lst[0] if lst else None
    def second_or_none(lst): return lst[1] if len(lst) > 1 else None

    st.markdown("---"); st.write(f"**Options for: {chart_type}**")

    if not all_columns: st.warning("The dataset has no columns. Please check your data or preprocessing steps.")
    else:
        # --- All Chart Implementations (Line, Bar, Pie, Scatter, etc. from "Master Edition") ---
        # Ensure these are complete and use the get_selection pattern.
        # For example, Scatter Plot with Trendline and Log Axis:
        if chart_type == "Scatter Plot":
            s_cc1, s_cc2, s_cc3, s_cc4 = st.columns(4)
            with s_cc1: x_col = st.selectbox("X-Axis (Numeric):", numeric_columns, key=f'{chart_type}_x', index=numeric_columns.index(get_selection(chart_type, "x_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with s_cc2: y_col = st.selectbox("Y-Axis (Numeric):", numeric_columns, key=f'{chart_type}_y', index=numeric_columns.index(get_selection(chart_type, "y_col", second_or_none(numeric_columns) or first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with s_cc3: color_col = st.selectbox("Color by (Optional):", [None] + all_columns, key=f'{chart_type}_color', index=([None] + all_columns).index(get_selection(chart_type, "color_col", None, [None] + all_columns)))
            with s_cc4: size_col = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_columns, key=f'{chart_type}_size', index=([None] + numeric_columns).index(get_selection(chart_type, "size_col", None, [None] + numeric_columns)))
            
            adv_s_cc1, adv_s_cc2 = st.columns(2)
            with adv_s_cc1: trendline_options = [None, "ols", "lowess"] # OLS: Ordinary Least Squares
                                trendline = st.selectbox("Add Trendline (Optional):", trendline_options, key=f'{chart_type}_trendline', index=trendline_options.index(get_selection(chart_type, "trendline", None)))
            with adv_s_cc2: log_x = st.checkbox("Logarithmic X-axis", value=get_selection(chart_type, "log_x", False), key=f'{chart_type}_logx')
                                log_y = st.checkbox("Logarithmic Y-axis", value=get_selection(chart_type, "log_y", False), key=f'{chart_type}_logy')
            
            if x_col and y_col:
                current_chart_opts.update({"x_col": x_col, "y_col": y_col, "color_col": color_col, "size_col": size_col, 
                                           "trendline": trendline, "log_x": log_x, "log_y": log_y,
                                           "chart_title": chart_title, "x_axis_label": x_axis_label_val, "y_axis_label": y_axis_label_val})
                if x_axis_label_val: plot_kwargs["labels"][x_col] = x_axis_label_val
                if y_axis_label_val: plot_kwargs["labels"][y_col] = y_axis_label_val
                try: fig = px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col, 
                                      trendline=trendline, log_x=log_x, log_y=log_y, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Scatter Plot: {e}")
        
        # ... (Implement ALL OTHER CHART TYPES: Line, Bar, Pie, Histogram, Box, Area, Funnel, Sunburst, Treemap, Map, Correlation Heatmap)
        #       using the same pattern: st.columns for layout, get_selection for sticky options,
        #       updating current_chart_opts, and then calling px.chart_type(...)
        #       Remember to add specific advanced options where appropriate (e.g., barmode for Bar Chart).

        # Placeholder for other charts - YOU MUST COMPLETE THESE based on the "Master Edition"
        elif chart_type in ["Line Chart", "Bar Chart", "Pie Chart", "Histogram", "Box Plot", "Area Chart", "Funnel Chart", "Sunburst Chart", "Treemap", "Map (Geographical)", "Correlation Heatmap"]:
            st.info(f"Configuration for {chart_type} needs to be fully re-implemented here following the Scatter Plot example and Master Edition structure.")
            # Example: For Line Chart, you'd have selectboxes for x_col, y_cols, color_col, etc.
            # and then current_chart_opts.update({...}) and px.line(...)

        st.session_state.chart_options[chart_type] = current_chart_opts

    # --- Display Plot and Download ---
    st.markdown("---"); st.subheader("🖼️ Your Visualization")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1: generate_html_download_link(fig, filename=f"{chart_type.lower().replace(' ', '_')}_plot.html")
        with col_dl2: 
            if st.session_state.data_processing_applied or data_source_option == "Load Sample Dataset":
                df_to_csv_download_link(st.session_state.df, filename=f"{st.session_state.active_df_name.split('.')[0]}_processed.csv")
    else: st.info(f"Please configure options for **{chart_type}** to generate the plot. Ensure required columns are selected and valid.")

else:
    # --- Welcome Message (from Master Edition) ---
    st.header("Welcome to ExcelViz Pro - Platinum Edition!")
    st.markdown("""Transform your raw data into insightful visualizations...""")
    st.info("💡 Tip: Upload a file or load a sample dataset from the sidebar to begin!")
