import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Kept for potential future use, though px is primary
import base64
import io

# --- Page Configuration (Should be the first Streamlit command) ---
st.set_page_config(
    page_title='ExcelViz Pro - Master Edition',
    page_icon='🌠', # Even more stellar icon!
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- Initialize Session State ---
# Ensures variables persist across reruns and user interactions.
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'chart_options' not in st.session_state: # Stores user's last choices for chart elements
    st.session_state.chart_options = {}
if 'last_chart_type' not in st.session_state: # To help manage option resets if chart type changes
    st.session_state.last_chart_type = ""

# --- Styling (from style.css and general improvements) ---
PRIMARY_COLOR = "#1a7707" # Green from your style.css
SECONDARY_COLOR = "#1605b1" # A blue from button style in style.css
TEXT_COLOR_DARK = "#333333"
BACKGROUND_COLOR_LIGHT = "#f8f9fa" # A light, clean background
ACCENT_BACKGROUND = "#e9f5e9" # Light green accent

custom_css = f"""
<style>
    /* General App Styling */
    .stApp {{
        /* background-color: {BACKGROUND_COLOR_LIGHT}; */ /* Optional: uncomment for a light app background */
    }}

    /* Sidebar Styling */
    .css-1d391kg {{ /* Sidebar main class, might change with Streamlit versions */
        background-color: {BACKGROUND_COLOR_LIGHT};
        border-right: 1px solid #ddd;
    }}

    /* Button Styling */
    .stButton>button {{
        border: 1px solid {PRIMARY_COLOR};
        background-color: white;
        color: {PRIMARY_COLOR};
        padding: 0.4rem 0.8rem;
        border-radius: 8px; /* Softer radius from your style.css '10px' */
        transition: all 0.3s ease-in-out;
        font-weight: 500;
    }}
    .stButton>button:hover {{
        border-color: {SECONDARY_COLOR};
        background-color: {ACCENT_BACKGROUND};
        color: {PRIMARY_COLOR};
    }}
    .stButton>button:active {{ /* For a click effect */
        background-color: {PRIMARY_COLOR};
        color: white;
    }}

    /* Headers */
    h1, h2 {{
        color: {PRIMARY_COLOR};
        font-family: 'Poppins', sans-serif; /* Assuming Poppins is available */
    }}
    h3 {{
        color: {TEXT_COLOR_DARK};
        font-family: 'Poppins', sans-serif;
    }}

    /* Markdown links */
    .stMarkdown a {{
        color: {SECONDARY_COLOR};
        text-decoration: none;
    }}
    .stMarkdown a:hover {{
        text-decoration: underline;
        color: {PRIMARY_COLOR};
    }}

    /* File Uploader */
    .stFileUploader label {{
        background-color: {ACCENT_BACKGROUND};
        border: 2px dashed {PRIMARY_COLOR};
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        transition: all 0.3s ease-in-out;
    }}
    .stFileUploader label:hover {{
        border-color: {SECONDARY_COLOR};
        background-color: #d4eed4; /* Slightly darker green on hover */
    }}

    /* Expander header */
    .streamlit-expanderHeader {{
        font-size: 1.1rem;
        color: {PRIMARY_COLOR};
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Utility Function for Plot Download ---
def generate_html_download_link(fig, filename="plot.html"):
    try:
        buffer = io.StringIO()
        fig.write_html(buffer, include_plotlyjs="cdn")
        html_bytes = buffer.getvalue().encode()
        b64 = base64.b64encode(html_bytes).decode()
        # Styled download button
        button_style = f"background-color:{PRIMARY_COLOR};color:white;padding:10px 15px;text-align:center;text-decoration:none;display:inline-block;border-radius:8px;border:none;font-weight:500;transition:all 0.3s ease;"
        hover_style = f"background-color:{SECONDARY_COLOR};" # Simple hover change
        
        href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" style="{button_style}" onmouseover="this.style.backgroundColor=\'{SECONDARY_COLOR}\'" onmouseout="this.style.backgroundColor=\'{PRIMARY_COLOR}\'">Download Plot as HTML</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error generating download link: {e}")
        return None

# --- Helper function to get sticky selections ---
def get_selection(chart_type_key, param_key, default_value=None, options_list=None):
    """Retrieves a stored selection for a chart parameter or returns a default."""
    if chart_type_key in st.session_state.chart_options:
        value = st.session_state.chart_options[chart_type_key].get(param_key, default_value)
        # Validate if the stored value is still valid within current options_list
        if options_list and value not in options_list:
            if default_value in options_list: # Fallback to default if it's valid
                return default_value
            elif options_list: # Fallback to first option if default is also invalid
                return options_list[0]
        return value
    return default_value


# --- Sidebar ---
with st.sidebar:
    # --- Logo ---
    # Option 1: If you have a logo.png deployed with your app in an 'images' folder:
    # st.image("images/logo.png", width=150)
    # Option 2: Placeholder (replace with your actual logo URL if hosted)
    st.markdown(f"<p style='text-align:center;'><img src='https://www.gstatic.com/images/branding/googlelogo/svg/googlelogo_clr_74x24px.svg' alt='ExcelVizPro Logo Placeholder' width='120'></p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='color: {PRIMARY_COLOR}; text-align: center; margin-top:0px;'>ExcelViz Pro</h1>", unsafe_allow_html=True) # Title from index.html
    st.markdown("---")

    # --- File Uploader ---
    st.header("📤 Upload Data")
    uploaded_file = st.file_uploader(
        'Choose a file (XLSX, CSV, TSV, JSON)',
        type=['xlsx', 'csv', 'tsv', 'json'],
        help="Supports Excel, CSV, TSV, and JSON (array of objects or record-oriented) files."
    )

    if uploaded_file:
        # Process file if it's new or df is not loaded
        if st.session_state.uploaded_file_name != uploaded_file.name or st.session_state.df is None:
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.df = None  # Reset dataframe for new file
            st.session_state.chart_options = {} # Reset all stored chart options
            try:
                file_extension = uploaded_file.name.split('.')[-1].lower()
                if file_extension == 'xlsx':
                    st.session_state.df = pd.read_excel(uploaded_file, engine='openpyxl')
                elif file_extension == 'csv':
                    st.session_state.df = pd.read_csv(uploaded_file)
                elif file_extension == 'tsv':
                    st.session_state.df = pd.read_csv(uploaded_file, sep='\t')
                elif file_extension == 'json':
                    st.session_state.df = pd.read_json(uploaded_file, orient='records', lines=True, nonstandard_ όπως='float') # More robust JSON parsing
                st.success(f"File '{uploaded_file.name}' loaded!")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
                st.session_state.df = None # Ensure df is None on error
    
    st.markdown("---")

    # --- About & Help Section ---
    st.header("ℹ️ About & Help")
    with st.expander("About ExcelViz Pro", expanded=False):
        # Content from about.html, README.md, blog.html
        st.markdown("""
            **ExcelViz Pro** empowers you to effortlessly transform raw data into compelling, insightful visualizations. Upload your spreadsheet files and explore a diverse range of chart types to uncover hidden trends and patterns.

            * **Our Mission**: To make data visualization accessible, intuitive, and enjoyable for everyone, from students to professionals.
            * **The Team**: Developed by dedicated students for the IT485 course: Ameer Alshrafi, Meet Patel, Biruk Tadesse, Wayne Zhang, and Shubh Patel.
            * **Project Links**: 
                * [GitHub Repository](https://patelmeet1011.github.io/ExcelVizProIt485/)
                * [Visualizer App (Direct)](https://excelvizproo.streamlit.app/)
        """)
    with st.expander("Frequently Asked Questions (FAQs)", expanded=False):
        # Content from feedbackform.html
        st.markdown("""
        **Q: How do I use ExcelVizPro?**
        A: Simply upload your data file using the 'Upload Data' section in the sidebar. Once loaded, data insights and visualization options will appear in the main panel. Select a chart type and configure its options to generate your plot.

        **Q: What kind of graphs can I visualize?**
        A: ExcelVizPro supports a wide array of visualizations including Line Charts, Bar Charts, Pie Charts, Scatter Plots, Histograms, Box Plots, Area Charts, Funnel Charts, Sunburst Charts, Treemaps, Correlation Heatmaps, and Geographical Maps.

        **Q: Is my uploaded information private?**
        A: Your data is processed in your browser and/or on the server for visualization purposes only during your session. We are committed to user privacy and do not store or share your uploaded data files.
        """)
    
    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: {TEXT_COLOR_DARK}; font-size: 0.9em;'>© 2023-2024 ExcelVizPro Team</p>", unsafe_allow_html=True) # Footer from index.html

# --- Main Content Area ---
if st.session_state.df is not None:
    df = st.session_state.df # Make df readily available
    st.header("📊 Interactive Data Visualizer")
    st.markdown(f"Visualizing: **{st.session_state.uploaded_file_name}** (`{df.shape[0]}` rows, `{df.shape[1]}` columns)")

    # --- Data Preview and Basic Analysis ---
    with st.expander("🧐 Data Preview & Quick Insights", expanded=False):
        st.dataframe(df.head())
        st.subheader("Descriptive Statistics (Numeric Columns)")
        numeric_cols_desc = df.select_dtypes(include=['number'])
        if not numeric_cols_desc.empty:
            st.dataframe(numeric_cols_desc.describe().transpose(), use_container_width=True)
        else:
            st.info("No numeric columns found for descriptive statistics.")
        st.subheader("Column Data Types")
        st.dataframe(df.dtypes.astype(str).rename("Data Type"), use_container_width=True)

    st.markdown("---")
    st.subheader("⚙️ Configure Your Visualization")

    # --- Chart Type and Theme Selection ---
    control_col1, control_col2 = st.columns([3, 2]) # Give more space to chart type
    with control_col1:
        chart_type = st.selectbox(
            "Select Chart Type:",
            [
                "Line Chart", "Bar Chart", "Pie Chart", "Scatter Plot", "Histogram", "Box Plot", 
                "Area Chart", "Funnel Chart", "Sunburst Chart", "Treemap", 
                "Map (Geographical)", "Correlation Heatmap"
            ],
            key='chart_type_selector',
            index=0 # Default selection
        )
    with control_col2:
        plotly_theme = st.selectbox(
            "Select Plotly Theme:",
            ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white", None],
            key='plotly_theme_selector',
            index=1 # Default to plotly_white
        )
    
    # Reset specific chart options if chart type changes to avoid incompatible old settings
    if st.session_state.last_chart_type != chart_type:
        st.session_state.chart_options[chart_type] = {} # Initialize/reset options for the new chart type
        st.session_state.last_chart_type = chart_type


    # --- Advanced Chart Customization Inputs ---
    st.markdown("**Advanced Customization:**")
    cust_col1, cust_col2, cust_col3 = st.columns(3)
    default_title = f"{chart_type} of {st.session_state.uploaded_file_name.split('.')[0]}"
    with cust_col1:
        chart_title = st.text_input("Chart Title:", 
                                    value=get_selection(chart_type, "chart_title", default_title), 
                                    key=f'{chart_type}_title_input')
    with cust_col2:
        x_axis_label_val = st.text_input("X-Axis Label (Optional):", 
                                       value=get_selection(chart_type, "x_axis_label", ""), 
                                       key=f'{chart_type}_x_label_input')
    with cust_col3:
        y_axis_label_val = st.text_input("Y-Axis Label (Optional):", 
                                       value=get_selection(chart_type, "y_axis_label", ""), 
                                       key=f'{chart_type}_y_label_input')

    # --- Dynamic Column Selection and Plotting Logic ---
    fig = None
    all_columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category', 'boolean']).columns.tolist() # Include boolean as categorical

    # Ensure options dict exists for current chart type
    if chart_type not in st.session_state.chart_options:
        st.session_state.chart_options[chart_type] = {}
    
    current_chart_opts = st.session_state.chart_options[chart_type]
    
    # Common plot arguments, to be updated by specific chart logic
    plot_kwargs = {"title": chart_title, "template": plotly_theme, "labels": {}}

    # Function to safely get first element or None
    def first_or_none(lst): return lst[0] if lst else None
    def second_or_none(lst): return lst[1] if len(lst) > 1 else None
    
    # --- Chart Specific Controls ---
    # This section will contain the logic for each chart type
    # (Continuing the pattern from previous versions, making it more complete)
    
    st.markdown("---") # Visual separator for chart-specific controls
    st.write(f"**Options for: {chart_type}**")

    if not all_columns:
        st.warning("The uploaded data frame has no columns. Please check your file.")
    else:
        # Line Chart
        if chart_type == "Line Chart":
            cc1, cc2, cc3 = st.columns(3)
            with cc1: x_col = st.selectbox("X-Axis:", [None] + all_columns, key=f'{chart_type}_x', index=([None] + all_columns).index(get_selection(chart_type, "x_col", first_or_none(all_columns), [None] + all_columns)))
            with cc2: y_cols = st.multiselect("Y-Axis (Numeric):", numeric_columns, key=f'{chart_type}_y', default=get_selection(chart_type, "y_cols", [first_or_none(numeric_columns)] if numeric_columns else [], numeric_columns))
            with cc3: color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_columns, key=f'{chart_type}_color', index=([None] + categorical_columns).index(get_selection(chart_type, "color_col", None, [None] + categorical_columns)))
            if x_col and y_cols:
                current_chart_opts.update({"x_col": x_col, "y_cols": y_cols, "color_col": color_col, "chart_title": chart_title, "x_axis_label": x_axis_label_val, "y_axis_label": y_axis_label_val})
                if x_axis_label_val: plot_kwargs["labels"][x_col] = x_axis_label_val
                # Y-axis label for multiple y_cols is tricky, Plotly handles it by default or it can be a generic one.
                if y_axis_label_val and len(y_cols) == 1: plot_kwargs["labels"][y_cols[0]] = y_axis_label_val
                elif y_axis_label_val: plot_kwargs["labels"]["value"] = y_axis_label_val # Generic for multiple lines
                try: fig = px.line(df, x=x_col, y=y_cols, color=color_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Line Chart: {e}")
        
        # Bar Chart
        elif chart_type == "Bar Chart":
            cc1, cc2, cc3, cc4 = st.columns(4)
            with cc1: x_col = st.selectbox("X-Axis (Categorical/Dimension):", all_columns, key=f'{chart_type}_x', index=all_columns.index(get_selection(chart_type, "x_col", first_or_none(categorical_columns) or first_or_none(all_columns), all_columns)))
            with cc2: y_col = st.selectbox("Y-Axis (Numeric/Measure):", numeric_columns, key=f'{chart_type}_y', index=numeric_columns.index(get_selection(chart_type, "y_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with cc3: color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_columns, key=f'{chart_type}_color', index=([None] + categorical_columns).index(get_selection(chart_type, "color_col", None, [None] + categorical_columns)))
            with cc4: barmode = st.selectbox("Bar Mode:", ["group", "stack", "relative"], key=f'{chart_type}_barmode', index=["group", "stack", "relative"].index(get_selection(chart_type, "barmode", "group")))
            if x_col and y_col:
                current_chart_opts.update({"x_col": x_col, "y_col": y_col, "color_col": color_col, "barmode": barmode, "chart_title": chart_title, "x_axis_label": x_axis_label_val, "y_axis_label": y_axis_label_val})
                if x_axis_label_val: plot_kwargs["labels"][x_col] = x_axis_label_val
                if y_axis_label_val: plot_kwargs["labels"][y_col] = y_axis_label_val
                try: fig = px.bar(df, x=x_col, y=y_col, color=color_col, barmode=barmode, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Bar Chart: {e}")

        # Pie Chart
        elif chart_type == "Pie Chart":
            cc1, cc2 = st.columns(2)
            with cc1: names_col = st.selectbox("Labels/Names (Categorical):", categorical_columns, key=f'{chart_type}_names', index=categorical_columns.index(get_selection(chart_type, "names_col", first_or_none(categorical_columns), categorical_columns)) if categorical_columns else 0)
            with cc2: values_col = st.selectbox("Values (Numeric):", numeric_columns, key=f'{chart_type}_values', index=numeric_columns.index(get_selection(chart_type, "values_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            if names_col and values_col:
                current_chart_opts.update({"names_col": names_col, "values_col": values_col, "chart_title": chart_title})
                # Pie charts don't typically have x/y axis labels in the same way. Title is primary.
                try: fig = px.pie(df, names=names_col, values=values_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Pie Chart: {e}")
        
        # Scatter Plot
        elif chart_type == "Scatter Plot":
            cc1, cc2, cc3, cc4 = st.columns(4)
            with cc1: x_col = st.selectbox("X-Axis (Numeric):", numeric_columns, key=f'{chart_type}_x', index=numeric_columns.index(get_selection(chart_type, "x_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with cc2: y_col = st.selectbox("Y-Axis (Numeric):", numeric_columns, key=f'{chart_type}_y', index=numeric_columns.index(get_selection(chart_type, "y_col", second_or_none(numeric_columns) or first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with cc3: color_col = st.selectbox("Color by (Optional):", [None] + all_columns, key=f'{chart_type}_color', index=([None] + all_columns).index(get_selection(chart_type, "color_col", None, [None] + all_columns)))
            with cc4: size_col = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_columns, key=f'{chart_type}_size', index=([None] + numeric_columns).index(get_selection(chart_type, "size_col", None, [None] + numeric_columns)))
            if x_col and y_col:
                current_chart_opts.update({"x_col": x_col, "y_col": y_col, "color_col": color_col, "size_col": size_col, "chart_title": chart_title, "x_axis_label": x_axis_label_val, "y_axis_label": y_axis_label_val})
                if x_axis_label_val: plot_kwargs["labels"][x_col] = x_axis_label_val
                if y_axis_label_val: plot_kwargs["labels"][y_col] = y_axis_label_val
                try: fig = px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Scatter Plot: {e}")

        # Histogram
        elif chart_type == "Histogram":
            cc1, cc2, cc3 = st.columns(3)
            with cc1: x_col = st.selectbox("Data Column (Numeric):", numeric_columns, key=f'{chart_type}_x', index=numeric_columns.index(get_selection(chart_type, "x_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with cc2: color_col = st.selectbox("Color by (Categorical, Optional):", [None] + categorical_columns, key=f'{chart_type}_color', index=([None] + categorical_columns).index(get_selection(chart_type, "color_col", None, [None] + categorical_columns)))
            with cc3: nbins = st.slider("Number of Bins:", 5, 100, value=get_selection(chart_type, "nbins", 20), key=f'{chart_type}_nbins')
            if x_col:
                current_chart_opts.update({"x_col": x_col, "color_col": color_col, "nbins": nbins, "chart_title": chart_title, "x_axis_label": x_axis_label_val})
                if x_axis_label_val: plot_kwargs["labels"][x_col] = x_axis_label_val
                # Y-axis for histogram is usually 'count' or 'density'.
                if y_axis_label_val: plot_kwargs["labels"]["y"] = y_axis_label_val # Placeholder, might need histfunc
                try: fig = px.histogram(df, x=x_col, color=color_col, nbins=nbins, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Histogram: {e}")

        # Box Plot
        elif chart_type == "Box Plot":
            cc1, cc2, cc3 = st.columns(3)
            with cc1: y_cols = st.multiselect("Data Columns (Numeric):", numeric_columns, key=f'{chart_type}_y', default=get_selection(chart_type, "y_cols", [first_or_none(numeric_columns)] if numeric_columns else [], numeric_columns))
            with cc2: x_col = st.selectbox("Group by (Categorical, Optional):", [None] + categorical_columns, key=f'{chart_type}_x', index=([None] + categorical_columns).index(get_selection(chart_type, "x_col", None, [None] + categorical_columns)))
            with cc3: color_col = st.selectbox("Color by (if grouping, Optional):", [None] + categorical_columns, key=f'{chart_type}_color', index=([None] + categorical_columns).index(get_selection(chart_type, "color_col", None, [None] + categorical_columns))) # Often same as x_col
            if y_cols:
                current_chart_opts.update({"y_cols": y_cols, "x_col": x_col, "color_col": color_col, "chart_title": chart_title, "x_axis_label": x_axis_label_val})
                if x_axis_label_val and x_col: plot_kwargs["labels"][x_col] = x_axis_label_val
                if y_axis_label_val: plot_kwargs["labels"]["value"] = y_axis_label_val # Generic y-label
                try: fig = px.box(df, y=y_cols, x=x_col, color=color_col if x_col else None, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Box Plot: {e}")
        
        # Area Chart
        elif chart_type == "Area Chart":
            cc1, cc2, cc3 = st.columns(3)
            with cc1: x_col = st.selectbox("X-Axis:", [None] + all_columns, key=f'{chart_type}_x', index=([None] + all_columns).index(get_selection(chart_type, "x_col", first_or_none(all_columns), [None] + all_columns)))
            with cc2: y_cols = st.multiselect("Y-Axis (Numeric):", numeric_columns, key=f'{chart_type}_y', default=get_selection(chart_type, "y_cols", [first_or_none(numeric_columns)] if numeric_columns else [], numeric_columns))
            with cc3: color_col = st.selectbox("Color/Group by (Categorical, Optional):", [None] + categorical_columns, key=f'{chart_type}_color', index=([None] + categorical_columns).index(get_selection(chart_type, "color_col", None, [None] + categorical_columns)))
            if x_col and y_cols:
                current_chart_opts.update({"x_col": x_col, "y_cols": y_cols, "color_col": color_col, "chart_title": chart_title, "x_axis_label": x_axis_label_val, "y_axis_label": y_axis_label_val})
                if x_axis_label_val: plot_kwargs["labels"][x_col] = x_axis_label_val
                if y_axis_label_val and len(y_cols) == 1: plot_kwargs["labels"][y_cols[0]] = y_axis_label_val
                elif y_axis_label_val : plot_kwargs["labels"]["value"] = y_axis_label_val
                try: fig = px.area(df, x=x_col, y=y_cols, color=color_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Area Chart: {e}")

        # Funnel Chart
        elif chart_type == "Funnel Chart":
            st.info("For Funnel Charts, select a column representing stages and a column for corresponding values. Data should ideally be sorted by stage progression.")
            cc1, cc2 = st.columns(2)
            with cc1: y_stages_col = st.selectbox("Stages Column (Categorical):", categorical_columns, key=f'{chart_type}_ystages', index=categorical_columns.index(get_selection(chart_type, "y_stages_col", first_or_none(categorical_columns), categorical_columns)) if categorical_columns else 0)
            with cc2: x_values_col = st.selectbox("Values Column (Numeric):", numeric_columns, key=f'{chart_type}_xvalues', index=numeric_columns.index(get_selection(chart_type, "x_values_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            if y_stages_col and x_values_col:
                current_chart_opts.update({"y_stages_col": y_stages_col, "x_values_col": x_values_col, "chart_title": chart_title})
                # Labels are less conventional here, title is key.
                try: fig = px.funnel(df, y=y_stages_col, x=x_values_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Funnel Chart: {e}")

        # Sunburst Chart
        elif chart_type == "Sunburst Chart":
            st.info("Select a path of categorical columns (from root to leaves for hierarchy) and a numeric values column.")
            cc1, cc2 = st.columns(2)
            with cc1: path_cols = st.multiselect("Path Columns (Categorical, Hierarchical):", categorical_columns, key=f'{chart_type}_path', default=get_selection(chart_type, "path_cols", [first_or_none(categorical_columns), second_or_none(categorical_columns)] if len(categorical_columns) > 1 else [first_or_none(categorical_columns)] if categorical_columns else [], categorical_columns))
            with cc2: values_col = st.selectbox("Values Column (Numeric):", numeric_columns, key=f'{chart_type}_values', index=numeric_columns.index(get_selection(chart_type, "values_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            if path_cols and values_col:
                current_chart_opts.update({"path_cols": path_cols, "values_col": values_col, "chart_title": chart_title})
                try: fig = px.sunburst(df, path=path_cols, values=values_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Sunburst Chart: {e}. Ensure path columns form a valid hierarchy and values are numeric.")

        # Treemap
        elif chart_type == "Treemap":
            st.info("Similar to Sunburst: select hierarchical path columns and a values column. Optionally, a color column.")
            cc1, cc2, cc3 = st.columns(3)
            with cc1: path_cols = st.multiselect("Path Columns (Categorical, Hierarchical):", categorical_columns, key=f'{chart_type}_path', default=get_selection(chart_type, "path_cols", [first_or_none(categorical_columns), second_or_none(categorical_columns)] if len(categorical_columns) > 1 else [first_or_none(categorical_columns)] if categorical_columns else [], categorical_columns))
            with cc2: values_col = st.selectbox("Values Column (Numeric):", numeric_columns, key=f'{chart_type}_values', index=numeric_columns.index(get_selection(chart_type, "values_col", first_or_none(numeric_columns), numeric_columns)) if numeric_columns else 0)
            with cc3: color_col = st.selectbox("Color by (Optional):", [None] + all_columns, key=f'{chart_type}_color', index=([None] + all_columns).index(get_selection(chart_type, "color_col", None, [None] + all_columns)))
            if path_cols and values_col:
                current_chart_opts.update({"path_cols": path_cols, "values_col": values_col, "color_col": color_col, "chart_title": chart_title})
                try: fig = px.treemap(df, path=path_cols, values=values_col, color=color_col, **plot_kwargs)
                except Exception as e: st.error(f"Error creating Treemap: {e}. Ensure path columns form valid hierarchy and values are numeric.")

        # Map (Geographical)
        elif chart_type == "Map (Geographical)":
            st.info("Select Latitude and Longitude columns (must be numeric). Optionally add columns for color, size, or hover text.")
            # Attempt to auto-detect lat/lon columns
            lat_guess = first_or_none([col for col in numeric_columns if 'lat' in col.lower() or 'latitude' in col.lower()])
            lon_guess = first_or_none([col for col in numeric_columns if 'lon' in col.lower() or 'lng' in col.lower() or 'longitude' in col.lower()])

            cc1, cc2, cc3, cc4 = st.columns(4)
            with cc1: lat_col = st.selectbox("Latitude Column:", numeric_columns, key=f'{chart_type}_lat', index=numeric_columns.index(get_selection(chart_type, "lat_col", lat_guess, numeric_columns)) if lat_guess and numeric_columns else 0 if numeric_columns else 0)
            with cc2: lon_col = st.selectbox("Longitude Column:", numeric_columns, key=f'{chart_type}_lon', index=numeric_columns.index(get_selection(chart_type, "lon_col", lon_guess, numeric_columns)) if lon_guess and numeric_columns else (1 if len(numeric_columns) > 1 else 0) if numeric_columns else 0)
            with cc3: color_col = st.selectbox("Color by (Optional):", [None] + all_columns, key=f'{chart_type}_color', index=([None] + all_columns).index(get_selection(chart_type, "color_col", None, [None] + all_columns)))
            with cc4: size_col = st.selectbox("Size by (Numeric, Optional):", [None] + numeric_columns, key=f'{chart_type}_size', index=([None] + numeric_columns).index(get_selection(chart_type, "size_col", None, [None] + numeric_columns)))
            hover_name_col = st.selectbox("Hover Name (Main Label, Optional):", [None] + all_columns, key=f'{chart_type}_hover_name', index=([None] + all_columns).index(get_selection(chart_type, "hover_name_col", None, [None] + all_columns)))
            
            if lat_col and lon_col:
                current_chart_opts.update({"lat_col": lat_col, "lon_col": lon_col, "color_col": color_col, "size_col": size_col, "hover_name_col": hover_name_col, "chart_title": chart_title})
                try:
                    fig = px.scatter_mapbox(df, lat=lat_col, lon=lon_col, color=color_col, size=size_col,
                                            hover_name=hover_name_col, mapbox_style="open-street-map", 
                                            zoom=3, height=600, **plot_kwargs)
                    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
                except Exception as e: st.error(f"Error creating Map: {e}. Ensure Latitude and Longitude are valid numeric columns.")
        
        # Correlation Heatmap
        elif chart_type == "Correlation Heatmap":
            st.info("This chart displays pairwise correlations of all numeric columns in your dataset.")
            if len(numeric_columns) > 1:
                current_chart_opts.update({"chart_title": chart_title}) # Only title applies here
                try:
                    corr_matrix = df[numeric_columns].corr()
                    fig = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", 
                                    color_continuous_scale='RdBu_r', **plot_kwargs) # .2f for 2 decimal places
                except Exception as e: st.error(f"Error creating Correlation Heatmap: {e}")
            else:
                st.warning("At least two numeric columns are required for a correlation heatmap.")
        
        # Store current selections for the active chart type
        st.session_state.chart_options[chart_type] = current_chart_opts


    # --- Display Plot and Download Link ---
    st.markdown("---")
    st.subheader("🖼️ Your Visualization")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True) # Add some space before download
        generate_html_download_link(fig, filename=f"{chart_type.lower().replace(' ', '_')}_plot.html")
    else:
        st.info(f"Please configure the options for the **{chart_type}** to generate the plot. Ensure all required columns are selected and valid for the chosen chart type.")

else:
    # --- Welcome Message when no file is loaded ---
    st.header("Welcome to ExcelViz Pro!")
    st.markdown("""
        Transform your raw data into insightful visualizations with just a few clicks! 
        Please upload your data file (Excel, CSV, TSV, or JSON) using the **sidebar on the left** to begin your analysis.
        
        Once your file is loaded, you'll be able to:
        * Preview your data and see quick statistical insights.
        * Choose from a wide variety of chart types.
        * Customize the appearance of your plots.
        * Download your visualizations as interactive HTML files.

        **Our Goal:** "See Clearly, Decide Confidently: Transforming Data into Insight."
    """)
    st.info("💡 Tip: Check out the 'About & Help' section in the sidebar for FAQs and more information about ExcelViz Pro.")
