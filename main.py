import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import altair as alt # New import
import base64
import io

# --- Page Configuration ---
st.set_page_config(
    page_title='ExcelViz Pro - Diamond Edition',
    page_icon='💎',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- Initialize Session State ---
DEFAULT_SESSION_STATE = {
    'df': None, 'uploaded_file_name': None, 'chart_options': {},
    'last_chart_type': "", 'active_df_name': "No data loaded",
    'data_processing_applied': False, 'app_theme': 'Light' # New: App theme
}
for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state: st.session_state[key] = value

# --- Styling ---
PRIMARY_COLOR = "#1a7707"; SECONDARY_COLOR = "#1605b1"; TEXT_COLOR_DARK = "#333333"
BACKGROUND_COLOR_LIGHT = "#f8f9fa"; ACCENT_BACKGROUND = "#e9f5e9"
DARK_BACKGROUND = "#0E1117"; DARK_TEXT = "#FAFAFA"; DARK_SECONDARY_BG = "#1A1C2E"; DARK_METRIC_BG="#262730"


def get_app_theme_css(theme):
    if theme == 'Dark':
        # Inspired by US Population Dashboard CSS and general dark themes
        alt.themes.enable("dark") # Enable Altair dark theme
        return f"""
        <style>
            /* Dark Theme */
            .stApp {{ background-color: {DARK_BACKGROUND}; color: {DARK_TEXT}; }}
            .css-1d391kg {{ background-color: {DARK_SECONDARY_BG}; border-right: 1px solid #333; }} /* Sidebar */
            .stButton>button {{
                border: 1px solid {PRIMARY_COLOR}; background-color: {DARK_SECONDARY_BG}; color: {PRIMARY_COLOR};
                font-weight: 500; padding: 0.4rem 0.8rem; border-radius: 8px; transition: all 0.3s ease-in-out;
            }}
            .stButton>button:hover {{ border-color: {SECONDARY_COLOR}; background-color: {PRIMARY_COLOR}; color: white; }}
            h1, h2 {{ color: {PRIMARY_COLOR}; }}  h3 {{ color: {DARK_TEXT}; }}
            .stMarkdown a {{ color: {SECONDARY_COLOR}; }} .stMarkdown a:hover {{ color: {PRIMARY_COLOR}; }}
            .stFileUploader label {{ background-color: {DARK_SECONDARY_BG}; border: 2px dashed {PRIMARY_COLOR}; color: {DARK_TEXT};}}
            .stFileUploader label:hover {{ border-color: {SECONDARY_COLOR}; background-color: {PRIMARY_COLOR}; color:white; }}
            .streamlit-expanderHeader {{ font-size: 1.1rem; color: {PRIMARY_COLOR}; }}
            [data-testid="stMetric"] {{ background-color: {DARK_METRIC_BG}; text-align: center; padding: 15px 0; border-radius: 8px; }}
            [data-testid="stMetricLabel"] {{ color: #A0A0A0; display: flex; justify-content: center; align-items: center; }}
            [data-testid="stMetricValue"] {{ color: {DARK_TEXT}; }}
            [data-testid="stMetricDelta"] {{ color: {DARK_TEXT}; }}
            /* Other dark theme specific styles */
        </style>
        """
    else: # Light Theme (default)
        alt.themes.enable("default") # Enable Altair default (light) theme
        return f"""
        <style>
            /* Light Theme (from Platinum) */
            .css-1d391kg {{ background-color: {BACKGROUND_COLOR_LIGHT}; border-right: 1px solid #ddd; }}
            .stButton>button {{
                border: 1px solid {PRIMARY_COLOR}; background-color: white; color: {PRIMARY_COLOR};
                padding: 0.4rem 0.8rem; border-radius: 8px; transition: all 0.3s ease-in-out; font-weight: 500;
            }}
            .stButton>button:hover {{ border-color: {SECONDARY_COLOR}; background-color: {ACCENT_BACKGROUND}; color: {PRIMARY_COLOR}; }}
            h1, h2 {{ color: {PRIMARY_COLOR}; }} h3 {{ color: {TEXT_COLOR_DARK}; }}
            .stMarkdown a {{ color: {SECONDARY_COLOR}; }} .stMarkdown a:hover {{ color: {PRIMARY_COLOR}; }}
            .stFileUploader label {{ background-color: {ACCENT_BACKGROUND}; border: 2px dashed {PRIMARY_COLOR}; }}
            .stFileUploader label:hover {{ border-color: {SECONDARY_COLOR}; background-color: #d4eed4; }}
            .streamlit-expanderHeader {{ font-size: 1.1rem; color: {PRIMARY_COLOR}; }}
            [data-testid="stMetric"] {{ background-color: #FFFFFF; text-align: center; padding: 15px 0; border-radius: 8px; border: 1px solid #E0E0E0;}}
            [data-testid="stMetricLabel"] {{ display: flex; justify-content: center; align-items: center; }}
        </style>
        """
st.markdown(get_app_theme_css(st.session_state.app_theme), unsafe_allow_html=True)


# --- Utility Functions (Download Links, Get Selection - from Platinum) ---
def generate_html_download_link(fig, filename="plot.html"):
    try:
        buffer = io.StringIO(); fig.write_html(buffer, include_plotlyjs="cdn"); html_bytes = buffer.getvalue().encode()
        b64 = base64.b64encode(html_bytes).decode()
        button_bg = PRIMARY_COLOR if st.session_state.app_theme == 'Light' else DARK_SECONDARY_BG
        button_text_color = 'white' if st.session_state.app_theme == 'Light' else PRIMARY_COLOR
        hover_bg = SECONDARY_COLOR
        
        button_style = f"background-color:{button_bg};color:{button_text_color};padding:10px 15px;text-align:center;text-decoration:none;display:inline-block;border-radius:8px;border:none;font-weight:500;transition:all 0.3s ease;"
        href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" style="{button_style}" onmouseover="this.style.backgroundColor=\'{hover_bg}\'; this.style.color=\'white\';" onmouseout="this.style.backgroundColor=\'{button_bg}\'; this.style.color=\'{button_text_color}\';">Download Plot as HTML</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e: st.error(f"Error generating plot download link: {e}"); return None

def df_to_csv_download_link(df, filename="processed_data.csv"):
    try:
        csv = df.to_csv(index=False); b64 = base64.b64encode(csv.encode()).decode()
        button_bg = SECONDARY_COLOR if st.session_state.app_theme == 'Light' else DARK_METRIC_BG
        button_text_color = 'white' if st.session_state.app_theme == 'Light' else DARK_TEXT
        hover_bg = PRIMARY_COLOR
        button_style = f"background-color:{button_bg};color:{button_text_color};padding:10px 15px;text-align:center;text-decoration:none;display:inline-block;border-radius:8px;border:none;font-weight:500;transition:all 0.3s ease;"
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="{button_style}" onmouseover="this.style.backgroundColor=\'{hover_bg}\';this.style.color=\'white\';" onmouseout="this.style.backgroundColor=\'{button_bg}\';this.style.color=\'{button_text_color}\';">Download Data as CSV</a>'
        return st.markdown(href, unsafe_allow_html=True)
    except Exception as e: st.error(f"Error generating CSV download link: {e}"); return None

def get_selection(chart_type_key, param_key, default_value=None, options_list=None):
    # (Same robust get_selection function from Platinum Edition)
    if chart_type_key in st.session_state.chart_options:
        value = st.session_state.chart_options[chart_type_key].get(param_key, default_value)
        if options_list and value not in options_list: # Validate if stored value is still valid
            if default_value in options_list: return default_value
            elif options_list: return options_list[0] if options_list else None
        return value
    return default_value

def load_sample_data(dataset_name): # (Same as Platinum)
    if dataset_name == "Iris": return px.data.iris(), "Sample: Iris Dataset"
    elif dataset_name == "Tips": return px.data.tips(), "Sample: Tips Dataset"
    elif dataset_name == "Gapminder (subset)":
        df_gap = px.data.gapminder(); return df_gap[df_gap['year'].isin([2002, 2007])], "Sample: Gapminder (2002 & 2007)"
    return None, None

# --- Altair Chart Functions (Adapted from US Population Dashboard) ---
def make_altair_heatmap(input_df, input_y, input_x, input_color_agg_col, agg_func='mean', input_color_theme='viridis'):
    # Ensure input_color_agg_col is numeric for aggregation
    if not pd.api.types.is_numeric_dtype(input_df[input_color_agg_col]):
        st.warning(f"Color column '{input_color_agg_col}' for heatmap must be numeric for aggregation. Please convert or select a numeric column.")
        return None
    
    # Aggregation string for Altair, e.g., 'mean(population):Q'
    color_encoding = f'{agg_func}({input_color_agg_col}):Q'
    
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:N', axis=alt.Axis(title=str(input_y), titleFontSize=14, titlePadding=10, labelAngle=0)), # Nominal type for categories
        x=alt.X(f'{input_x}:N', axis=alt.Axis(title=str(input_x), titleFontSize=14, titlePadding=10)),
        color=alt.Color(color_encoding, legend=alt.Legend(title=f'{agg_func.capitalize()} of {input_color_agg_col}'),
                         scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black' if st.session_state.app_theme == 'Light' else '#555'), # Stroke based on theme
        strokeWidth=alt.value(0.25),
        tooltip=[alt.Tooltip(f'{input_x}:N', title=str(input_x)),
                 alt.Tooltip(f'{input_y}:N', title=str(input_y)),
                 alt.Tooltip(color_encoding, title=f'{agg_func.capitalize()} of {input_color_agg_col}', format=".2f")]
    ).properties(width='container', height=300 # Responsive width
    ).configure_axis(labelFontSize=10, titleFontSize=12)
    return heatmap

def make_altair_donut_chart(input_df, input_category_col, input_value_col, input_color_theme='category10'):
    # Donut chart expects aggregated data typically (e.g., sum of values per category)
    # For simplicity, if multiple rows per category, let's sum them.
    if not pd.api.types.is_numeric_dtype(input_df[input_value_col]):
        st.warning(f"Value column '{input_value_col}' for donut chart must be numeric. Please convert or select a numeric column.")
        return None
        
    source = input_df.groupby(input_category_col)[input_value_col].sum().reset_index()
    
    # Calculate percentages for the donut text if desired, or show absolute values
    # source['percentage'] = (source[input_value_col] / source[input_value_col].sum() * 100)

    base = alt.Chart(source).encode(
        theta=alt.Theta(field=input_value_col, type="quantitative"),
        color=alt.Color(field=input_category_col, type="nominal", scale=alt.Scale(scheme=input_color_theme), legend=alt.Legend(title=str(input_category_col))),
        tooltip=[alt.Tooltip(f'{input_category_col}:N'), alt.Tooltip(f'{input_value_col}:Q', format=",.0f")] # Format for thousands
    )
    donut = base.mark_arc(innerRadius=50, outerRadius=90, cornerRadius=5).properties(width=200, height=200)
    # Optional: Add text labels in the center or per slice (can get complex for many categories)
    return donut


# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<p style='text-align:center;'><img src='https://www.gstatic.com/images/branding/googlelogo/svg/googlelogo_clr_74x24px.svg' alt='ExcelVizPro Logo Placeholder' width='120'></p>", unsafe_allow_html=True) # Replace with your logo
    st.markdown(f"<h1 style='color: {PRIMARY_COLOR}; text-align: center; margin-top:0px;'>ExcelViz Pro</h1>", unsafe_allow_html=True)
    st.markdown("---")

    st.header("⚙️ App Settings")
    current_theme = st.session_state.app_theme
    new_theme = st.radio("Select App Theme:", ("Light", "Dark"), index=["Light", "Dark"].index(current_theme), key="theme_selector")
    if new_theme != current_theme:
        st.session_state.app_theme = new_theme
        st.rerun() # Rerun to apply new theme CSS

    st.markdown("---")
    st.header("💾 Data Input")
    # (Data Input: Upload File / Sample Dataset - from Platinum, unchanged)
    data_source_option = st.radio("Choose data source:", ("Upload File", "Load Sample Dataset"), key="data_source_type")
    if data_source_option == "Upload File":
        uploaded_file = st.file_uploader('Choose a file', type=['xlsx', 'xls', 'csv', 'tsv', 'json'])
        if uploaded_file:
            if st.session_state.uploaded_file_name != uploaded_file.name or not isinstance(st.session_state.df, pd.DataFrame):
                # ... (file loading logic from Platinum) ...
                st.session_state.uploaded_file_name = uploaded_file.name; st.session_state.df = None; st.session_state.chart_options = {}; st.session_state.data_processing_applied = False
                try:
                    ext = uploaded_file.name.split('.')[-1].lower()
                    if ext == 'xlsx': st.session_state.df = pd.read_excel(uploaded_file, engine='openpyxl')
                    elif ext == 'xls': st.session_state.df = pd.read_excel(uploaded_file, engine='xlrd')
                    elif ext == 'csv': st.session_state.df = pd.read_csv(uploaded_file)
                    elif ext == 'tsv': st.session_state.df = pd.read_csv(uploaded_file, sep='\t')
                    elif ext == 'json': st.session_state.df = pd.read_json(uploaded_file, orient='records', lines=True)
                    st.session_state.active_df_name = f"Uploaded: {uploaded_file.name}"; st.success(f"Loaded '{uploaded_file.name}'")
                except Exception as e: st.error(f"Error loading: {e}"); st.session_state.df = None
    elif data_source_option == "Load Sample Dataset":
        sample_name = st.selectbox("Select sample:", ["Iris", "Tips", "Gapminder (subset)"])
        if st.button("Load Sample"):
            st.session_state.df, name = load_sample_data(sample_name); st.session_state.active_df_name = name
            st.session_state.uploaded_file_name = None; st.session_state.chart_options = {}; st.session_state.data_processing_applied = False
            if st.session_state.df is not None: st.success(f"'{sample_name}' loaded!")
            else: st.error("Failed to load sample.")
            
    st.markdown("---")
    st.header("ℹ️ About & Help") # (From Platinum)
    with st.expander("About ExcelViz Pro", expanded=False): st.markdown("""**ExcelViz Pro** empowers ...""")
    with st.expander("FAQs", expanded=False): st.markdown("""**Q: How do I use ExcelVizPro?** ...""")
    st.markdown("---")
    st.markdown(f"<p style='text-align:center;color:{TEXT_COLOR_DARK if st.session_state.app_theme == 'Light' else DARK_TEXT};font-size:0.9em;'>© 2023-2024 ExcelVizPro Team</p>", unsafe_allow_html=True)


# --- Main Content Area ---
if st.session_state.df is not None:
    df = st.session_state.df

    st.header("✨ Data Dashboard & Visualizer ✨")
    st.markdown(f"Current Dataset: **{st.session_state.active_df_name}** (`{df.shape[0]}` rows, `{df.shape[1]}` columns)")
    if st.session_state.data_processing_applied: st.info("Data processing has been applied. Results reflected below.")

    # --- Data Preprocessing Tools (from Platinum) ---
    with st.expander("🛠️ Data Preprocessing Tools", expanded=False):
        # ... (Missing Value Handling and Change Column Data Type sections from Platinum Edition)
        # Make sure these sections are complete and functional.
        st.subheader("Handle Missing Values") # Placeholder
        st.subheader("Change Column Data Type") # Placeholder

    # --- Key Metrics Display (NEW) ---
    st.markdown("---")
    st.subheader("📊 Key Metrics")
    if not df.empty:
        numeric_cols_for_metrics = df.select_dtypes(include=np.number).columns.tolist()
        if numeric_cols_for_metrics:
            selected_metric_cols = st.multiselect("Select numeric columns for metrics:", numeric_cols_for_metrics, 
                                                  default=numeric_cols_for_metrics[:3] if len(numeric_cols_for_metrics) >=3 else numeric_cols_for_metrics, # Default to first 3
                                                  key="metric_col_select")
            if selected_metric_cols:
                metric_cols_display = st.columns(len(selected_metric_cols))
                for i, col_name in enumerate(selected_metric_cols):
                    with metric_cols_display[i]:
                        st.metric(label=f"Sum ({col_name})", value=f"{df[col_name].sum():,.2f}")
                        st.metric(label=f"Mean ({col_name})", value=f"{df[col_name].mean():,.2f}")
                        st.metric(label=f"Median ({col_name})", value=f"{df[col_name].median():,.2f}")
                        # Add Min, Max, Count if desired
            else: st.info("Select numeric columns to display key metrics.")
        else: st.info("No numeric columns available in the dataset to calculate metrics.")
    else: st.info("No data loaded to display metrics.")


    # --- Data Preview & Advanced Dataframe (NEW Configuration) ---
    with st.expander("🧐 Data Preview & Configuration", expanded=False):
        st.dataframe(df.head())
        st.subheader("Descriptive Statistics (Numeric Columns)")
        # ... (Descriptive stats from Platinum)
        st.subheader("Column Data Types")
        # ... (Column types from Platinum)
        
        st.subheader("Advanced Dataframe View Configuration")
        st.info("Configure how columns are displayed in the table below. Useful for large datasets or specific column formats.")
        
        column_config = {}
        cols_to_configure = st.multiselect("Select columns to configure display:", df.columns.tolist(), key="df_config_cols")
        for col_name in cols_to_configure:
            col_type = st.selectbox(f"Display type for '{col_name}':", 
                                    ["Automatic", "Text", "Number", "Progress Bar (Numeric only)", "Checkbox (Boolean only)", "Link"], 
                                    key=f"df_config_type_{col_name}")
            if col_type == "Progress Bar (Numeric only)" and pd.api.types.is_numeric_dtype(df[col_name]):
                min_val = df[col_name].min(); max_val = df[col_name].max()
                column_config[col_name] = st.column_config.ProgressColumn(label=col_name, min_value=min_val, max_value=max_val, format="%.2f")
            elif col_type == "Number" and pd.api.types.is_numeric_dtype(df[col_name]):
                num_format = st.text_input(f"Number format for '{col_name}' (e.g., %.2f, $%.0f):", "%.2f", key=f"df_config_format_{col_name}")
                column_config[col_name] = st.column_config.NumberColumn(label=col_name, format=num_format)
            elif col_type == "Checkbox (Boolean only)" and pd.api.types.is_boolean_dtype(df[col_name]):
                 column_config[col_name] = st.column_config.CheckboxColumn(label=col_name)
            elif col_type == "Link":
                 column_config[col_name] = st.column_config.LinkColumn(label=col_name)
            # Add more configurations as needed (DateColumn, TimeColumn, ImageColumn etc.)
        
        st.dataframe(df, column_config=column_config if column_config else None, use_container_width=True, height=300)


    st.markdown("---")
    st.subheader("⚙️ Configure Your Visualization")
    # --- Chart Type and Theme Selection ---
    control_col1, control_col2 = st.columns([3, 2])
    with control_col1:
        chart_type_list = [
            "Line Chart (Plotly)", "Bar Chart (Plotly)", "Pie Chart (Plotly)", "Scatter Plot (Plotly)", 
            "Histogram (Plotly)", "Box Plot (Plotly)", "Area Chart (Plotly)", "Funnel Chart (Plotly)", 
            "Sunburst Chart (Plotly)", "Treemap (Plotly)", "Map (Plotly)", "Correlation Heatmap (Plotly)",
            "Heatmap (Altair)", "Donut Chart (Altair)" # New Altair charts
        ]
        chart_type = st.selectbox("Select Chart Type:", chart_type_list, key='chart_type_selector')
    with control_col2:
        # Theme selection - Plotly themes for Plotly, Altair themes for Altair
        if "Altair" in chart_type:
            altair_theme_list = ['default', 'dark', 'vox', 'latimes', 'ggplot2', 'urbaninstitute', 'quartz']
            selected_theme = st.selectbox("Select Altair Theme:", altair_theme_list, 
                                          index=altair_theme_list.index('dark' if st.session_state.app_theme == 'Dark' else 'default'), 
                                          key='altair_theme_selector')
        else: # Plotly charts
            plotly_theme_list = ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white", None]
            selected_theme = st.selectbox("Select Plotly Theme:", plotly_theme_list, 
                                          index=plotly_theme_list.index('plotly_dark' if st.session_state.app_theme == 'Dark' else 'plotly_white'), 
                                          key='plotly_theme_selector')

    if st.session_state.last_chart_type != chart_type: # Reset options if chart type changes
        st.session_state.chart_options[chart_type] = {}
        st.session_state.last_chart_type = chart_type

    # ... (Advanced Customization: Title, X/Y Labels - from Platinum) ...
    st.markdown("**Advanced Customization:**") # Title, X/Y Labels
    # ...

    # --- Dynamic Column Selection and Plotting Logic ---
    fig = None; all_columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category', 'boolean']).columns.tolist()
    
    if chart_type not in st.session_state.chart_options: st.session_state.chart_options[chart_type] = {}
    current_chart_opts = st.session_state.chart_options[chart_type]
    # For Plotly charts
    plot_kwargs = {"title": get_selection(chart_type, "chart_title", f"{chart_type.replace('(Plotly)','').strip()}"), 
                   "template": selected_theme if "Altair" not in chart_type else None, "labels": {}}
    # For Altair charts, theme is handled by alt.themes.enable() or chart.configure_theme()

    st.markdown("---"); st.write(f"**Options for: {chart_type}**")
    if not all_columns: st.warning("Dataset has no columns.")
    else:
        # --- Plotly Chart Implementations (from Platinum, ensure complete) ---
        if chart_type == "Scatter Plot (Plotly)": # Example from Platinum
            # ... (Scatter plot config from Platinum with trendline, log_x, log_y)
            pass # Ensure this is filled out
        
        # --- NEW Altair Chart Configurations ---
        elif chart_type == "Heatmap (Altair)":
            if len(all_columns) < 3: st.warning("Heatmap requires at least 3 columns (X, Y, Color Value).")
            else:
                ac1, ac2, ac3, ac4 = st.columns(4)
                with ac1: x_col_altair_hm = st.selectbox("X-Axis (Categorical):", categorical_columns, key=f'{chart_type}_x', index=categorical_columns.index(get_selection(chart_type, "x_col", categorical_columns[0] if categorical_columns else None)) if categorical_columns else 0)
                with ac2: y_col_altair_hm = st.selectbox("Y-Axis (Categorical):", categorical_columns, key=f'{chart_type}_y', index=categorical_columns.index(get_selection(chart_type, "y_col", categorical_columns[1] if len(categorical_columns)>1 else categorical_columns[0] if categorical_columns else None)) if categorical_columns else 0)
                with ac3: val_col_altair_hm = st.selectbox("Color Value (Numeric):", numeric_columns, key=f'{chart_type}_val', index=numeric_columns.index(get_selection(chart_type, "val_col", numeric_columns[0] if numeric_columns else None)) if numeric_columns else 0)
                with ac4: agg_altair_hm = st.selectbox("Aggregation:", ['mean', 'sum', 'median', 'min', 'max', 'count'], key=f'{chart_type}_agg', index=0)
                
                if x_col_altair_hm and y_col_altair_hm and val_col_altair_hm:
                    current_chart_opts.update({"x_col": x_col_altair_hm, "y_col": y_col_altair_hm, "val_col": val_col_altair_hm, "agg_func": agg_altair_hm, "theme": selected_theme, "chart_title": get_selection(chart_type, "chart_title", f"Altair Heatmap")})
                    try: fig = make_altair_heatmap(df, y_col_altair_hm, x_col_altair_hm, val_col_altair_hm, agg_altair_hm, selected_theme)
                    except Exception as e: st.error(f"Error creating Altair Heatmap: {e}")
        
        elif chart_type == "Donut Chart (Altair)":
            if len(categorical_columns) < 1 or len(numeric_columns) < 1: st.warning("Donut chart requires at least one categorical and one numeric column.")
            else:
                ac1, ac2 = st.columns(2)
                with ac1: cat_col_altair_donut = st.selectbox("Category Column:", categorical_columns, key=f'{chart_type}_cat', index=categorical_columns.index(get_selection(chart_type, "cat_col", categorical_columns[0] if categorical_columns else None)) if categorical_columns else 0)
                with ac2: val_col_altair_donut = st.selectbox("Value Column (Numeric):", numeric_columns, key=f'{chart_type}_val', index=numeric_columns.index(get_selection(chart_type, "val_col", numeric_columns[0] if numeric_columns else None)) if numeric_columns else 0)

                if cat_col_altair_donut and val_col_altair_donut:
                    current_chart_opts.update({"cat_col": cat_col_altair_donut, "val_col": val_col_altair_donut, "theme": selected_theme, "chart_title": get_selection(chart_type, "chart_title", f"Altair Donut Chart")})
                    try: fig = make_altair_donut_chart(df, cat_col_altair_donut, val_col_altair_donut, selected_theme)
                    except Exception as e: st.error(f"Error creating Altair Donut Chart: {e}")
        
        # ... (Ensure ALL OTHER PLOTLY chart implementations from Platinum are here and complete) ...
        else:
            st.info(f"Configuration for {chart_type} needs to be fully implemented here following previous examples.")


        st.session_state.chart_options[chart_type] = current_chart_opts # Save options

    # --- Display Plot and Download ---
    st.markdown("---"); st.subheader("🖼️ Your Visualization")
    if fig:
        if "Altair" in chart_type: st.altair_chart(fig, use_container_width=True, theme=None if selected_theme=='default' else selected_theme) # Altair handles its own theming
        else: st.plotly_chart(fig, use_container_width=True) # Plotly chart
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2 = st.columns(2)
        # Note: Altair charts cannot be directly downloaded as HTML like Plotly figs.
        # For Altair, you might save as JSON spec or PNG/SVG using external libraries if needed, or just view.
        if "Altair" not in chart_type and hasattr(fig, 'write_html'): # Check if it's a Plotly fig
            with col_dl1: generate_html_download_link(fig, filename=f"{chart_type.lower().replace(' (plotly)','').replace(' ', '_')}_plot.html")
        elif "Altair" in chart_type:
            with col_dl1: st.info("Altair charts are displayed. To save, use browser's print-to-PDF or screenshot functionality.")
        
        with col_dl2: 
            if st.session_state.data_processing_applied or data_source_option == "Load Sample Dataset":
                df_to_csv_download_link(st.session_state.df, filename=f"{st.session_state.active_df_name.split('.')[0]}_processed.csv")
    else: st.info(f"Configure options for **{chart_type}** to generate plot. Ensure valid columns are selected.")

else: # Welcome Message
    st.header("Welcome to ExcelViz Pro - Diamond Edition! 💎")
    st.markdown("""Transform data into insights! Upload a file or load a sample dataset from the sidebar to begin.""")
    st.info("💡 Explore new features like Altair charts, key metrics, and advanced dataframe configuration!")
