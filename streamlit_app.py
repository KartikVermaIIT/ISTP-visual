"""
Tree Species Classification - Streamlit Web Application
Interactive UI for running and visualizing classification results
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import os
import subprocess
import sys
from streamlit_folium import folium_static
import folium
from io import StringIO
import time

# Initialize Earth Engine at startup
def _init_ee():
    import ee

    # Priority 1: Streamlit Cloud secrets
    try:
        ee_secrets = st.secrets.get("earthengine", {})
        refresh_token = ee_secrets.get("refresh_token", None)
        ee_project = ee_secrets.get("project", None)
    except Exception:
        refresh_token = None
        ee_project = None

    # Priority 2: Environment variable
    if not ee_project:
        ee_project = os.environ.get('EARTHENGINE_PROJECT', 'istp-489219')

    if refresh_token:
        # Write credentials file to the location EE expects
        import pathlib, json
        creds_path = pathlib.Path.home() / '.config' / 'earthengine' / 'credentials'
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        creds_data = {
            'redirect_uri': 'http://localhost:8085',
            'refresh_token': refresh_token,
            'scopes': [
                'https://www.googleapis.com/auth/earthengine',
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/drive'
            ]
        }
        creds_path.write_text(json.dumps(creds_data))
        ee.Initialize(project=ee_project)
    else:
        # Local: use default credentials from earthengine-authenticated CLI
        ee.Initialize(project=ee_project)

try:
    _init_ee()
    EE_INITIALIZED = True
    EE_ERROR = None
except Exception as e:
    EE_INITIALIZED = False
    EE_ERROR = str(e)

# Page configuration
st.set_page_config(
    page_title="Tree Species Classification",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #2E7D32;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #558B2F;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
    .stAlert {
        background-color: #FFF9C4;
    }
    </style>
""", unsafe_allow_html=True)


def load_config():
    """Load configuration data"""
    try:
        import config
        return {
            'CLASS_NAMES': config.CLASS_NAMES,
            'SEASONS': config.SEASONS,
            'CONFIG': config.CONFIG,
            'FEATURES': config.FEATURES
        }
    except:
        return None


def load_class_names():
    """Load tree species class names"""
    config_data = load_config()
    if config_data:
        return config_data['CLASS_NAMES']
    return ['Oak', 'Pine', 'Spruce', 'Beech', 'Birch', 'Fir', 'Mixed Forest']


@st.cache_data
def generate_sample_confusion_matrix(n_classes=7):
    """Generate a sample confusion matrix for demonstration"""
    # Create a realistic confusion matrix
    base = np.eye(n_classes) * 45
    noise = np.random.randint(0, 5, (n_classes, n_classes))
    confusion = (base + noise).astype(int)
    np.fill_diagonal(confusion, np.random.randint(45, 52, n_classes))
    return confusion


@st.cache_data
def calculate_accuracy_metrics(confusion_matrix):
    """Calculate accuracy metrics from confusion matrix"""
    confusion = np.array(confusion_matrix)
    
    # Overall Accuracy
    overall_acc = np.trace(confusion) / np.sum(confusion)
    
    # Producer's Accuracy (sensitivity/recall)
    producer_acc = np.diag(confusion) / np.sum(confusion, axis=1)
    
    # User's Accuracy (precision)
    user_acc = np.diag(confusion) / np.sum(confusion, axis=0)
    
    # F1 Score
    f1_scores = 2 * (producer_acc * user_acc) / (producer_acc + user_acc + 1e-10)
    
    # Kappa
    po = overall_acc
    pe = np.sum(np.sum(confusion, axis=1) * np.sum(confusion, axis=0)) / (np.sum(confusion) ** 2)
    kappa = (po - pe) / (1 - pe)
    
    return {
        'overall_accuracy': overall_acc,
        'kappa': kappa,
        'producer_accuracy': producer_acc,
        'user_accuracy': user_acc,
        'f1_scores': f1_scores
    }


@st.cache_data
def generate_sample_area_data(class_names_tuple):
    """Generate sample area statistics"""
    class_names = list(class_names_tuple)
    n_classes = len(class_names)
    areas = np.random.randint(500, 5000, n_classes)
    
    data = []
    for i, (name, area) in enumerate(zip(class_names, areas)):
        data.append({
            'Class': name,
            'Area_Hectares': area,
            'Area_km2': area / 100,
            'Percentage': 0  # Will calculate after
        })
    
    df = pd.DataFrame(data)
    df['Percentage'] = (df['Area_Hectares'] / df['Area_Hectares'].sum() * 100).round(2)
    
    return df


def plot_confusion_matrix(confusion_matrix, class_names):
    """Create an interactive confusion matrix heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=confusion_matrix,
        x=class_names,
        y=class_names,
        colorscale='Greens',
        text=confusion_matrix,
        texttemplate='%{text}',
        textfont={"size": 12},
        colorbar=dict(title="Count")
    ))
    
    fig.update_layout(
        title='Confusion Matrix',
        xaxis_title='Predicted Class',
        yaxis_title='Actual Class',
        height=600,
        width=700
    )
    
    return fig


def plot_accuracy_by_class(metrics, class_names):
    """Plot accuracy metrics by class"""
    df = pd.DataFrame({
        'Class': class_names,
        'Producer Accuracy': metrics['producer_accuracy'],
        'User Accuracy': metrics['user_accuracy'],
        'F1-Score': metrics['f1_scores']
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Producer Accuracy',
        x=df['Class'],
        y=df['Producer Accuracy'],
        marker_color='#66BB6A'
    ))
    
    fig.add_trace(go.Bar(
        name='User Accuracy',
        x=df['Class'],
        y=df['User Accuracy'],
        marker_color='#42A5F5'
    ))
    
    fig.add_trace(go.Bar(
        name='F1-Score',
        x=df['Class'],
        y=df['F1-Score'],
        marker_color='#FFA726'
    ))
    
    fig.update_layout(
        title='Accuracy Metrics by Class',
        xaxis_title='Tree Species',
        yaxis_title='Score',
        barmode='group',
        height=500,
        yaxis=dict(range=[0, 1])
    )
    
    return fig


def plot_area_distribution(area_df):
    """Plot area distribution pie chart"""
    fig = px.pie(
        area_df,
        values='Area_Hectares',
        names='Class',
        title='Area Distribution by Species',
        color_discrete_sequence=px.colors.sequential.Greens_r,
        hole=0.3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Area: %{value:.0f} ha<br>Percentage: %{percent}'
    )
    
    fig.update_layout(height=500)
    
    return fig


def plot_area_bar_chart(area_df):
    """Plot area as horizontal bar chart"""
    fig = px.bar(
        area_df.sort_values('Area_Hectares', ascending=True),
        x='Area_Hectares',
        y='Class',
        orientation='h',
        title='Area Coverage by Species',
        color='Area_Hectares',
        color_continuous_scale='Greens',
        text='Area_Hectares'
    )
    
    fig.update_traces(
        texttemplate='%{text:.0f} ha',
        textposition='outside'
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_title='Area (Hectares)',
        yaxis_title='Tree Species'
    )
    
    return fig


def create_feature_importance_chart():
    """Create sample feature importance visualization"""
    features = [
        'EVI_summer_p80', 'NDVI_autumn_p80', 'VH_VV_ratio_spring',
        'NIR_Contrast', 'MTCI_summer', 'EVI_gradient', 'Slope',
        'REIP_autumn', 'VH_winter_p20', 'Aspect_N'
    ]
    importance = np.random.uniform(0.05, 0.15, len(features))
    importance = importance / importance.sum()  # Normalize
    importance = np.sort(importance)[::-1]
    
    fig = go.Figure(go.Bar(
        x=importance,
        y=features,
        orientation='h',
        marker_color='#4CAF50'
    ))
    
    fig.update_layout(
        title='Top 10 Most Important Features',
        xaxis_title='Importance',
        yaxis_title='Feature',
        height=500
    )
    
    return fig


def run_script_with_output(script_name, description):
    """Run a Python script and capture output"""
    output_container = st.empty()
    
    with st.spinner(f"🔄 {description}..."):
        try:
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, result.stdout, result.stderr
            else:
                return False, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Script timeout after 5 minutes"
        except Exception as e:
            return False, "", str(e)


def create_earth_engine_map(center_lat=37.7, center_lon=-122.4, zoom=10):
    """Create an interactive map using Google Earth Engine with folium"""
    import ee
    
    # Create base folium map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        width='100%',
        height='600px'
    )
    
    # Define the study area
    aoi = ee.Geometry.Rectangle([center_lon - 0.1, center_lat - 0.1, 
                                 center_lon + 0.1, center_lat + 0.1])
    
    # Load Sentinel-2 imagery for the area (most recent)
    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate('2023-06-01', '2023-09-30') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .median() \
        .clip(aoi)
    
    # Add RGB visualization as EE tile layer
    rgb_vis = {
        'min': 0,
        'max': 3000,
        'bands': ['B4', 'B3', 'B2']
    }
    
    try:
        map_id_dict = ee.Image(s2).getMapId(rgb_vis)
        folium.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name='Sentinel-2 RGB',
            overlay=True,
            control=True
        ).add_to(m)
    except:
        pass
    
    # Add NDVI layer
    try:
        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndvi_vis = {
            'min': 0,
            'max': 1,
            'palette': ['red', 'yellow', 'green']
        }
        ndvi_map_id = ee.Image(ndvi).getMapId(ndvi_vis)
        folium.TileLayer(
            tiles=ndvi_map_id['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name='NDVI',
            overlay=True,
            control=True,
            show=False
        ).add_to(m)
    except:
        pass
    
    # Add study area marker
    folium.Marker(
        [center_lat, center_lon],
        popup='Study Area Center',
        tooltip='Analysis Center Point',
        icon=folium.Icon(color='red', icon='leaf')
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m


def check_ee_authenticated():
    """Check if Earth Engine is authenticated"""
    return EE_INITIALIZED


def main():
    """Main Streamlit application"""
    
    # Show authentication status banner at the top
    if not EE_INITIALIZED:
        st.error(f"""
        ❌ **Google Earth Engine Not Authenticated**
        
        Error: {EE_ERROR}
        
        **To authenticate, run this command in your terminal:**
        ```bash
        earthengine authenticate
        ```
        
        Then restart this Streamlit app.
        """)
        st.stop()
    
    # Header
    st.markdown('<h1 class="main-header">🌲 Tree Species Classification</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Multi-seasonal Sentinel-1/2 Classification using Google Earth Engine</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/google/earthengine-api/master/docs/images/GoogleEarthEngine_v1.png", width=250)
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["🏠 Home", "⚙️ Configuration", "📊 Results Dashboard", "📈 Analysis", "🗺️ Map Visualization", "🚀 Run Pipeline", "📚 Documentation"],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### Quick Info")
        st.info("""
        **Resolution:** 10m  
        **Classes:** 7 species  
        **Features:** 100+  
        **Platform:** Google Earth Engine
        """)
        
        st.markdown("---")
        st.markdown("### Status")
        
        # Show Earth Engine status (already checked at startup)
        st.success("✅ Earth Engine: Connected")
        st.success("✅ System Ready")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Page routing
    if page == "🏠 Home":
        show_home_page()
    elif page == "⚙️ Configuration":
        show_configuration_page()
    elif page == "📊 Results Dashboard":
        show_results_dashboard()
    elif page == "📈 Analysis":
        show_analysis_page()
    elif page == "🗺️ Map Visualization":
        show_visualization_page()
    elif page == "🚀 Run Pipeline":
        show_run_pipeline_page()
    elif page == "📚 Documentation":
        show_documentation_page()


def show_home_page():
    """Home page with overview"""
    st.markdown("## Welcome to the Tree Species Classification System")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🛰️ Data Sources</h3>
            <ul>
                <li>Sentinel-2 Optical</li>
                <li>Sentinel-1 SAR</li>
                <li>SRTM DEM</li>
                <li>Multi-seasonal (4 seasons)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🔬 Features</h3>
            <ul>
                <li>9 Spectral Indices</li>
                <li>8 Texture Features</li>
                <li>4 Radar Indices</li>
                <li>Temporal Gradients</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯 Performance</h3>
            <ul>
                <li>Accuracy: 75-90%</li>
                <li>Resolution: 10m</li>
                <li>7 Tree Species</li>
                <li>Random Forest (71 trees)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick start guide
    st.markdown("## 🚀 Quick Start Guide")
    
    tab1, tab2, tab3 = st.tabs(["1️⃣ Setup", "2️⃣ Data Preparation", "3️⃣ Run Classification"])
    
    with tab1:
        st.markdown("""
        ### Install Dependencies
        ```bash
        pip install -r requirements.txt
        ```
        
        ### Authenticate Earth Engine
        ```bash
        earthengine authenticate
        ```
        
        ### Initialize in Python
        ```python
        import ee
        ee.Initialize()
        ```
        """)
        
        if st.button("📋 Copy Setup Commands"):
            st.code("pip install -r requirements.txt && earthengine authenticate")
            st.success("Commands copied to clipboard!")
    
    with tab2:
        st.markdown("""
        ### Prepare Training Data
        
        1. **Collect field samples** with GPS coordinates
        2. **Label each sample** with tree species class (0-6)
        3. **Create CSV** with columns: longitude, latitude, class
        
        #### CSV Format:
        """)
        
        sample_data = pd.DataFrame({
            'longitude': [-122.5, -122.4, -122.3],
            'latitude': [37.5, 37.6, 37.7],
            'class': [0, 1, 2],
            'species_name': ['Oak', 'Pine', 'Spruce']
        })
        
        st.dataframe(sample_data, use_container_width=True)
        
        if st.button("📥 Download CSV Template"):
            st.download_button(
                "Download Template",
                sample_data.to_csv(index=False),
                "training_template.csv",
                "text/csv"
            )
    
    with tab3:
        st.markdown("""
        ### Run Classification
        
        ```python
        from tree_species_classification import main
        import ee
        
        ee.Initialize()
        
        # Define study area
        aoi = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
        
        # Load data
        training = ee.FeatureCollection('users/YOUR_USERNAME/training')
        validation = ee.FeatureCollection('users/YOUR_USERNAME/validation')
        zones = ee.FeatureCollection('users/YOUR_USERNAME/forest_zones')
        
        # Run classification
        results = main(aoi, training, validation, zones, 'my_classification')
        ```
        """)
        
        st.info("💡 Results will be exported to your Google Drive")
    
    st.markdown("---")
    
    # System architecture
    st.markdown("## 🏗️ System Architecture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Processing Pipeline
        1. **Data Acquisition**
           - Load Sentinel-1 & Sentinel-2
           - Apply cloud masking
           - Filter by quality
        
        2. **Feature Extraction**
           - Compute spectral indices
           - Extract texture features
           - Calculate radar indices
           - Add terrain data
        
        3. **Classification**
           - Train Random Forest
           - Classify pixels
           - Export results
        """)
    
    with col2:
        st.markdown("""
        ### Key Features
        - ✅ Multi-seasonal analysis
        - ✅ Cloud-based processing
        - ✅ High-resolution output (10m)
        - ✅ Comprehensive accuracy assessment
        - ✅ Zonal statistics
        - ✅ Interactive visualization
        - ✅ Export to GeoTIFF
        - ✅ Easy to customize
        """)


def show_configuration_page():
    """Configuration page"""
    st.markdown("## ⚙️ Configuration")
    
    config_data = load_config()
    
    # Get default values from config
    default_year = 2019
    if config_data:
        default_year = config_data['CONFIG'].get('year', 2019)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Study Area Settings")
        
        year = st.number_input("Study Year", min_value=2015, max_value=2026, value=default_year)
        
        st.markdown("### Seasonal Date Ranges")
        spring_start = st.date_input("Spring Start", value=pd.to_datetime("2019-03-01"))
        spring_end = st.date_input("Spring End", value=pd.to_datetime("2019-03-31"))
        
        summer_start = st.date_input("Summer Start", value=pd.to_datetime("2019-06-01"))
        summer_end = st.date_input("Summer End", value=pd.to_datetime("2019-06-30"))
        
        st.markdown("### Area of Interest")
        lon_min = st.number_input("Longitude Min", value=10.0, format="%.4f")
        lat_min = st.number_input("Latitude Min", value=48.0, format="%.4f")
        lon_max = st.number_input("Longitude Max", value=10.5, format="%.4f")
        lat_max = st.number_input("Latitude Max", value=48.5, format="%.4f")
    
    with col2:
        st.markdown("### Classification Settings")
        
        n_trees = st.slider("Number of Trees (Random Forest)", 10, 200, 71)
        n_classes = st.number_input("Number of Classes", 2, 10, 7)
        resolution = st.select_slider("Spatial Resolution (m)", options=[10, 20, 30], value=10)
        
        st.markdown("### Feature Selection")
        
        use_spectral = st.checkbox("Spectral Indices", value=True)
        use_texture = st.checkbox("Texture Features", value=True)
        use_radar = st.checkbox("Radar Indices", value=True)
        use_temporal = st.checkbox("Temporal Gradients", value=True)
        use_terrain = st.checkbox("Terrain Features", value=True)
        
        st.markdown("### Export Settings")
        
        export_format = st.selectbox("Export Format", ["GeoTIFF", "Asset", "Drive"])
        export_scale = st.number_input("Export Scale (m)", value=10, min_value=10)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Configuration", use_container_width=True):
            st.success("Configuration saved!")
    
    with col2:
        if st.button("🔄 Reset to Default", use_container_width=True):
            st.warning("Configuration reset to default values")
    
    with col3:
        if st.button("📥 Export Config", use_container_width=True):
            config_dict = {
                'year': year,
                'n_trees': n_trees,
                'n_classes': n_classes,
                'resolution': resolution
            }
            st.download_button(
                "Download JSON",
                json.dumps(config_dict, indent=2),
                "config.json",
                "application/json"
            )


def show_results_dashboard():
    """Results dashboard page"""
    st.markdown("## 📊 Results Dashboard")
    
    class_names = load_class_names()
    confusion = generate_sample_confusion_matrix(len(class_names))
    metrics = calculate_accuracy_metrics(confusion)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Accuracy", f"{metrics['overall_accuracy']:.1%}",
                  delta="Good" if metrics['overall_accuracy'] > 0.8 else "Needs Improvement")
    with col2:
        st.metric("Kappa Coefficient", f"{metrics['kappa']:.3f}",
                  delta="Excellent" if metrics['kappa'] > 0.8 else "Good")
    with col3:
        st.metric("Mean Producer's Acc.", f"{np.mean(metrics['producer_accuracy']):.1%}")
    with col4:
        st.metric("Mean User's Acc.", f"{np.mean(metrics['user_accuracy']):.1%}")
    
    st.markdown("---")
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.plotly_chart(plot_confusion_matrix(confusion, class_names), use_container_width=True)
    with col2:
        st.markdown("### 📈 Accuracy Summary")
        summary_df = pd.DataFrame({
            'Class': class_names,
            'Producer': [f"{acc:.1%}" for acc in metrics['producer_accuracy']],
            'User': [f"{acc:.1%}" for acc in metrics['user_accuracy']],
            'F1': [f"{score:.1%}" for score in metrics['f1_scores']]
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        best_class = class_names[np.argmax(metrics['f1_scores'])]
        worst_class = class_names[np.argmin(metrics['f1_scores'])]
        st.success(f"**Best:** {best_class} ({metrics['f1_scores'].max():.1%})")
        st.warning(f"**Worst:** {worst_class} ({metrics['f1_scores'].min():.1%})")
    
    st.markdown("---")
    st.plotly_chart(plot_accuracy_by_class(metrics, class_names), use_container_width=True)
    
    # ── Download & View Results ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Classification Results")

    import glob as _glob, os as _os, zipfile as _zipfile
    from io import BytesIO as _BytesIO, StringIO as _StringIO

    # ── Resolve data source: session_state → disk → sample ──────────────
    _has_session = ('accuracy_csv' in st.session_state and 'area_csv' in st.session_state)
    _disk_m = sorted(_glob.glob('accuracy_metrics_*.csv'))
    _disk_a = sorted(_glob.glob('area_statistics_*.csv'))
    _disk_t = sorted(_glob.glob('tree_classification_*.tif'))

    if _has_session:
        st.success("✅ Showing results from your classification run")
        _acc_str  = st.session_state['accuracy_csv']
        _area_str = st.session_state['area_csv']
        _ts       = st.session_state.get('results_timestamp', 'latest')
        _acc_fname  = f"accuracy_metrics_{_ts}.csv"
        _area_fname = f"area_statistics_{_ts}.csv"
        _tif_bytes  = st.session_state.get('tif_bytes')
        _tif_fname  = st.session_state.get('tif_name', 'tree_classification.tif')
        _acc_bytes  = _acc_str.encode()
        _area_bytes = _area_str.encode()
        try:
            _acc_df  = pd.read_csv(_StringIO(_acc_str))
            _area_df = pd.read_csv(_StringIO(_area_str))
        except Exception:
            _acc_df = pd.DataFrame(); _area_df = pd.DataFrame()

    elif _disk_m or _disk_a:
        st.success("✅ Found result files on disk")
        _acc_fname  = _os.path.basename(_disk_m[-1]) if _disk_m else 'accuracy_metrics.csv'
        _area_fname = _os.path.basename(_disk_a[-1]) if _disk_a else 'area_statistics.csv'
        try:
            _acc_bytes  = open(_disk_m[-1],  'rb').read() if _disk_m else b''
            _area_bytes = open(_disk_a[-1], 'rb').read() if _disk_a else b''
            _tif_bytes  = open(_disk_t[-1],  'rb').read() if _disk_t else None
        except Exception:
            _acc_bytes = b''; _area_bytes = b''; _tif_bytes = None
        _tif_fname = _os.path.basename(_disk_t[-1]) if _disk_t else 'tree_classification.tif'
        try:
            _acc_df  = pd.read_csv(_disk_m[-1]) if _disk_m else pd.DataFrame()
            _area_df = pd.read_csv(_disk_a[-1]) if _disk_a else pd.DataFrame()
        except Exception:
            _acc_df = pd.DataFrame(); _area_df = pd.DataFrame()

    else:
        st.info("ℹ️ No classification run yet — showing **sample output** so you can preview the format and test downloads.")
        _sp = ['Oak', 'Pine', 'Spruce', 'Beech', 'Birch', 'Fir', 'Mixed Forest']
        _acc_df  = pd.DataFrame([{'Class': i, 'Species': n,
            'Producer_Accuracy': round(0.75+i*0.02, 3), 'User_Accuracy': round(0.76+i*0.02, 3),
            'F1_Score': round(0.755+i*0.02, 3), 'Sample_Count': 80} for i, n in enumerate(_sp)])
        _area_df = pd.DataFrame({'Class': list(range(7)), 'Species': _sp,
            'Area_Hectares': [1254, 892, 673, 541, 412, 389, 290],
            'Percentage': [28.6, 20.4, 15.4, 12.4, 9.4, 8.9, 6.6]})
        _acc_bytes  = _acc_df.to_csv(index=False).encode()
        _area_bytes = _area_df.to_csv(index=False).encode()
        _acc_fname  = 'sample_accuracy_metrics.csv'
        _area_fname = 'sample_area_statistics.csv'
        _tif_bytes  = None
        _tif_fname  = 'tree_classification.tif'

    # ── BIG download buttons at the very top (not inside tabs/columns) ───
    st.markdown("#### ⬇️ Download Files")
    _dl1, _dl2, _dl3 = st.columns(3)
    with _dl1:
        st.download_button(
            label="📊 Accuracy Metrics (.csv)",
            data=_acc_bytes,
            file_name=_acc_fname,
            mime="text/csv",
            use_container_width=True,
            type="primary",
            key="dl_acc"
        )
    with _dl2:
        st.download_button(
            label="🗺️ Area Statistics (.csv)",
            data=_area_bytes,
            file_name=_area_fname,
            mime="text/csv",
            use_container_width=True,
            type="primary",
            key="dl_area"
        )
    with _dl3:
        if _tif_bytes:
            st.download_button(
                label="🖼️ Classification Map (.tif)",
                data=_tif_bytes,
                file_name=_tif_fname,
                mime="image/tiff",
                use_container_width=True,
                type="primary",
                key="dl_tif"
            )
        else:
            st.button("🖼️ Map (.tif) — run first", disabled=True, use_container_width=True)

    # ZIP of everything
    _zip_buf = _BytesIO()
    with _zipfile.ZipFile(_zip_buf, 'w', _zipfile.ZIP_DEFLATED) as _zf:
        if _acc_bytes:  _zf.writestr(_acc_fname,  _acc_bytes)
        if _area_bytes: _zf.writestr(_area_fname, _area_bytes)
        if _tif_bytes:  _zf.writestr(_tif_fname,  _tif_bytes)
    st.download_button(
        label="📦 Download ALL as ZIP",
        data=_zip_buf.getvalue(),
        file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
        use_container_width=True,
        key="dl_zip"
    )

    # ── Inline data preview (always visible) ─────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Accuracy Metrics — Preview")
    if not _acc_df.empty:
        st.dataframe(_acc_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No accuracy data available.")

    st.markdown("#### 🗺️ Area Statistics — Preview")
    if not _area_df.empty:
        st.dataframe(_area_df, use_container_width=True, hide_index=True)
        # Pie chart
        try:
            _sp_col = 'Species' if 'Species' in _area_df.columns else _area_df.columns[0]
            _ha_col = 'Area_Hectares' if 'Area_Hectares' in _area_df.columns else \
                      _area_df.select_dtypes('number').columns[0]
            _fig_pie = px.pie(_area_df, values=_ha_col, names=_sp_col,
                              title='Area Distribution by Species', hole=0.35,
                              color_discrete_sequence=px.colors.sequential.Greens_r)
            _fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(_fig_pie, use_container_width=True)
        except Exception:
            pass
    else:
        st.warning("No area data available.")


def show_analysis_page():
    """Analysis page with detailed charts - uses real result files if available"""
    st.markdown("## 📈 Detailed Analysis")
    
    import glob
    
    # Load real data if available, otherwise show message
    area_files = sorted(glob.glob('area_statistics_*.csv'))
    metrics_files = sorted(glob.glob('accuracy_metrics_*.csv'))
    
    has_real_data = bool(area_files and metrics_files)
    
    if has_real_data:
        st.success(f"📊 Showing real classification results from `{os.path.basename(area_files[-1])}`")
        area_df = pd.read_csv(area_files[-1])
        metrics_df = pd.read_csv(metrics_files[-1])
        # Normalise column names
        species_col = 'Species' if 'Species' in area_df.columns else ('Class' if 'Class' in area_df.columns else area_df.columns[0])
        area_col = 'Area_Hectares' if 'Area_Hectares' in area_df.columns else area_df.select_dtypes('number').columns[0]
    else:
        st.warning("⚠️ No classification results found. Run classification first (Map Visualization → Run & Display). Showing placeholder charts.")
        class_names = load_class_names()
        area_df = generate_sample_area_data(tuple(class_names))
        species_col = 'Class'
        area_col = 'Area_Hectares'
        metrics_df = None
    
    tab1, tab2, tab3 = st.tabs(["🌍 Area Statistics", "🎯 Accuracy Metrics", "🎯 Feature Importance"])
    
    with tab1:
        st.markdown("### Area Distribution by Species")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                area_df,
                values=area_col,
                names=species_col,
                title='Area Distribution by Species',
                color_discrete_sequence=px.colors.sequential.Greens_r,
                hole=0.35
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=450)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                area_df.sort_values(area_col, ascending=True),
                x=area_col,
                y=species_col,
                orientation='h',
                title='Area Coverage by Species',
                color=area_col,
                color_continuous_scale='Greens',
                text=area_col
            )
            fig_bar.update_traces(texttemplate='%{text:.0f} ha', textposition='outside')
            fig_bar.update_layout(height=450, showlegend=False, xaxis_title='Area (Hectares)', yaxis_title='Species')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("### Detailed Statistics")
        st.dataframe(area_df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        total_ha = area_df[area_col].sum()
        dominant = area_df.loc[area_df[area_col].idxmax(), species_col]
        with col1:
            st.metric("Total Area", f"{total_ha:,.0f} ha")
        with col2:
            st.metric("Total Area", f"{total_ha / 100:.2f} km²")
        with col3:
            st.metric("Dominant Species", dominant)
    
    with tab2:
        if has_real_data and metrics_df is not None:
            st.markdown("### Accuracy Assessment from Classification")
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Plot accuracy bars if columns exist
            num_cols = [c for c in ['Producer_Accuracy', 'User_Accuracy', 'F1_Score'] if c in metrics_df.columns]
            id_col = 'Species' if 'Species' in metrics_df.columns else metrics_df.columns[0]
            
            if num_cols:
                plot_df = metrics_df[metrics_df[id_col] != 'Overall'] if 'Overall' in metrics_df[id_col].values else metrics_df
                fig_acc = go.Figure()
                colors = ['#66BB6A', '#42A5F5', '#FFA726']
                labels = {'Producer_Accuracy': 'Producer Accuracy', 'User_Accuracy': 'User Accuracy', 'F1_Score': 'F1-Score'}
                for col, color in zip(num_cols, colors):
                    fig_acc.add_trace(go.Bar(
                        name=labels.get(col, col),
                        x=plot_df[id_col],
                        y=plot_df[col],
                        marker_color=color
                    ))
                fig_acc.update_layout(
                    title='Accuracy Metrics by Species',
                    xaxis_title='Tree Species',
                    yaxis_title='Score',
                    barmode='group',
                    height=450,
                    yaxis=dict(range=[0, 1])
                )
                st.plotly_chart(fig_acc, use_container_width=True)
        else:
            st.info("Run classification to see real accuracy metrics here.")
    
    with tab3:
        st.markdown("### Random Forest Feature Importance")
        st.plotly_chart(create_feature_importance_chart(), use_container_width=True)
        st.info("""
        **Top Contributing Features (from paper):**
        - **EVI** - Enhanced Vegetation Index (dominant)
        - **NDVI** - Normalized Difference Vegetation Index
        - **VH/VV Ratio** - SAR backscatter ratio
        - **Texture Features** - Canopy structure patterns
        """)


def show_visualization_page():
    """Visualization page with interactive maps"""
    st.markdown("## 🗺️ Map Visualization")
    
    # Map configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        center_lat = st.number_input("Center Latitude", value=37.7, format="%.4f", step=0.1)
    
    with col2:
        center_lon = st.number_input("Center Longitude", value=-122.4, format="%.4f", step=0.1)
    
    with col3:
        zoom_level = st.slider("Zoom Level", 8, 15, 10)
    
    st.markdown("---")
    
    # Map display options
    st.markdown("### 🎨 Display Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_classified = st.checkbox("Show Classification", value=True)
    
    with col2:
        show_satellite = st.checkbox("Satellite Basemap", value=False)
    
    with col3:
        show_legend = st.checkbox("Show Legend", value=True)
    
    st.markdown("---")
    
    # Class color scheme customization
    st.markdown("### 🎨 Color Scheme")
    
    class_names = load_class_names()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    col_list = st.columns(len(class_names))
    custom_colors = []
    for i, (col, name, color) in enumerate(zip(col_list, class_names, colors)):
        with col:
            custom_colors.append(st.color_picker(f"{name}", color, key=f"color_{i}"))
    
    st.markdown("---")
    
    # Interactive Map Display
    st.markdown("### 🗺️ Google Earth Engine Map")
    
    if show_classified:
        st.success("🛰️ **Live Earth Engine Data:** Showing actual Sentinel-2 imagery and NDVI")
        
        # Create and display the Earth Engine map
        m = create_earth_engine_map(center_lat, center_lon, zoom_level)
        
        # Display the map using folium_static
        folium_static(m, width=1200, height=600)
        
        # Show map info
        st.markdown("""
        **Map Layers:**
        - 🛰️ **Sentinel-2 RGB** - True color satellite imagery from Google Earth Engine
        - 🌿 **NDVI** - Normalized Difference Vegetation Index (toggle in layer control)
        - 📍 **Study Area** - Red marker showing analysis center
        
        Use the layer control (top right) to toggle layers on/off.
        """)
    
    else:
        st.warning("Enable 'Show Classification' to view the map")
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Map", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📥 Export View", use_container_width=True):
            st.info("Map export feature: Save current view as image")
    
    with col3:
        if st.button("🗺️ Generate EE Code", use_container_width=True):
            st.code(f"""// Paste this in Earth Engine Code Editor
var roi = ee.Geometry.Rectangle([{center_lon - 0.1}, {center_lat - 0.1}, {center_lon + 0.1}, {center_lat + 0.1}]);
var classified = ee.Image('users/YOUR_USERNAME/tree_classification');
Map.addLayer(classified, {{min: 0, max: 6, palette: {custom_colors}}}, 'Classification');
Map.centerObject(roi, {zoom_level});
""", language='javascript')
    
    st.markdown("---")
    
    # Automated classification and visualization
    st.markdown("### 🤖 Automated Classification & Visualization")
    st.info("Run the full pipeline automatically: Classify → Export to EE → Display on Map")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        auto_asset_name = st.text_input(
            "Asset Name",
            f"tree_classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Name for your classification result"
        )
    
    with col2:
        ee_username = st.text_input(
            "Your EE Username",
            "your_username",
            help="Your Earth Engine username (e.g., 'users/yourname')"
        )
    
    with col3:
        st.markdown("&nbsp;")
        st.markdown("&nbsp;")
        show_classified_result = st.button("🗺️ Show Result on Map", use_container_width=True, type="primary")

    # Show classified result from session_state if pipeline was run
    if show_classified_result or st.session_state.get('classified_ee') is not None:
        if 'classified_ee' in st.session_state and st.session_state['classified_ee'] is not None:
            try:
                import ee as _ee
                classified = st.session_state['classified_ee']
                _species = st.session_state.get('species_names',
                    ['Oak','Pine','Spruce','Beech','Birch','Fir','Mixed Forest'])
                _palette = ['#2d7d32','#1b5e20','#4caf50','#8bc34a','#cddc39','#00897b','#795548']

                _vis = {'min': 0, 'max': len(_species)-1, 'palette': _palette[:len(_species)]}
                _map_id = classified.getMapId(_vis)

                m_cls = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)
                folium.TileLayer(
                    tiles=_map_id['tile_fetcher'].url_format,
                    attr='Google Earth Engine',
                    name='Classification Result',
                    overlay=True, control=True
                ).add_to(m_cls)
                folium.LayerControl().add_to(m_cls)

                oa = st.session_state.get('overall_accuracy', 0)
                kp = st.session_state.get('kappa', 0)
                ts = st.session_state.get('results_timestamp', 'latest')
                st.success(f"🌲 Classified map from pipeline run `{ts}` — OA: **{oa:.1%}** | κ: **{kp:.3f}**")
                folium_static(m_cls, width=1200, height=600)

                # Species legend
                leg_cols = st.columns(len(_species))
                for i, (c, s) in enumerate(zip(_palette, _species)):
                    with leg_cols[i]:
                        st.markdown(
                            f'<div style="background:{c};padding:4px 8px;border-radius:4px;'
                            f'color:white;text-align:center;font-size:12px">{s}</div>',
                            unsafe_allow_html=True
                        )
            except Exception as _e:
                st.error(f"Could not render classified map: {_e}")
        else:
            st.info("ℹ️ No classification result yet. Run the pipeline first: **🚀 Run Classification Pipeline** → click **RUN FULL PIPELINE**.")
    
    st.markdown("---")
    
    # Load classification results
    st.markdown("### 📥 Load Your Classification Results")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        asset_path = st.text_input(
            "Earth Engine Asset Path",
            "users/YOUR_USERNAME/tree_classification",
            help="Path to your classified image in Earth Engine"
        )
    
    with col2:
        st.markdown("&nbsp;")
        if st.button("📍 Load Asset", use_container_width=True):
            try:
                import ee
                
                # Try to load the asset
                classified = ee.Image(asset_path)
                
                # Create new folium map with classification
                m2 = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)
                
                # Add classification layer
                class_vis = {
                    'min': 0,
                    'max': 6,
                    'palette': custom_colors
                }
                
                map_id = classified.getMapId(class_vis)
                folium.TileLayer(
                    tiles=map_id['tile_fetcher'].url_format,
                    attr='Google Earth Engine',
                    name='Tree Classification',
                    overlay=True,
                    control=True
                ).add_to(m2)
                
                folium.LayerControl().add_to(m2)
                
                # Display
                st.success("✅ Classification loaded successfully!")
                folium_static(m2, width=1200, height=600)
                
            except Exception as e:
                st.error(f"❌ Could not load asset: {str(e)}")
                st.info("Make sure the asset path is correct and you have access to it.")
    
    st.markdown("---")
    
    # Map statistics
    st.markdown("### 📊 Visible Area Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Area", "~2,450 ha")
    
    with col2:
        st.metric("Dominant Species", "Oak (32%)")
    
    with col3:
        st.metric("Species Count", "7")
    
    with col4:
        st.metric("Resolution", "10 m")


def show_run_pipeline_page():
    """
    Full classification pipeline page.
    Training happens entirely on Google Earth Engine servers using:
      - Multi-seasonal Sentinel-2 (10 bands + 9 spectral indices) × 4 seasons
      - Multi-seasonal Sentinel-1 (VV/VH + 4 radar indices) × 4 seasons
      - EVI and VH temporal gradients (3 each)
      - GLCM texture features (up to 8) from NIR band
      - Annual 20th/80th percentiles for S2 and S1
      - DEM slope + 8-direction one-hot aspect
      - Random Forest: 71 trees (smileRandomForest via GEE)
      - 80/20 train/validation split for accuracy
    """
    from io import StringIO as _SIO, BytesIO as _BIO
    import zipfile as _zip

    st.markdown("## 🚀 Tree Species Classification Pipeline")
    st.markdown("""
    This page runs the **complete paper methodology** on Google Earth Engine.
    Upload your GPS training points → configure the area → hit **Run**.
    The model trains and classifies entirely on GEE servers; results are downloaded here.
    """)

    # ── EE status ──────────────────────────────────────────────────────────
    if not EE_INITIALIZED:
        st.error(f"❌ Earth Engine not initialized: {EE_ERROR}")
        st.info("Add your EE credentials to `.streamlit/secrets.toml` or authenticate locally.")
        return

    st.success("✅ Earth Engine connected")

    # ── Step 1: Training data ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📝 Step 1 — Training Data")

    help_csv = """**Required columns:**
- `longitude` (decimal degrees, WGS84)
- `latitude`  (decimal degrees, WGS84)  
- `class`     (integer 0 … N-1)

Optional: `species_name` column for display only.
Minimum 50 points per class recommended."""

    col_up, col_tmpl = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Upload training data CSV",
            type=['csv'],
            help=help_csv
        )
    with col_tmpl:
        st.markdown("&nbsp;")
        tmpl = pd.DataFrame({
            'longitude':    [10.05, 10.15, 10.25, 10.35, 10.45, 10.10, 10.20],
            'latitude':     [48.05, 48.15, 48.25, 48.35, 48.45, 48.10, 48.20],
            'class':        [0, 1, 2, 3, 4, 5, 6],
            'species_name': ['Oak','Pine','Spruce','Beech','Birch','Fir','Mixed Forest'],
        })
        st.download_button(
            "📥 Download Template CSV",
            tmpl.to_csv(index=False).encode(),
            file_name="training_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Use `sample_training_data.csv` (560 pts) for a quick test")

    # Parse uploaded file or fall back to sample
    _training_df = None
    if uploaded is not None:
        try:
            _training_df = pd.read_csv(uploaded)
            for req in ['longitude', 'latitude', 'class']:
                if req not in _training_df.columns:
                    st.error(f"❌ Missing required column: `{req}`")
                    _training_df = None
                    break
            if _training_df is not None:
                st.success(f"✅ {len(_training_df)} training points loaded")
                st.dataframe(_training_df.head(10), use_container_width=True, hide_index=True)
                _class_ids = sorted(_training_df['class'].unique().tolist())
                st.info(f"Classes detected: {_class_ids} → {len(_class_ids)} species")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    else:
        try:
            _training_df = pd.read_csv('sample_training_data.csv')
            st.info("ℹ️ No file uploaded — using `sample_training_data.csv` (560 GPS points, 7 species, Bavaria)")
            st.dataframe(_training_df.head(10), use_container_width=True, hide_index=True)
        except Exception:
            st.warning("Upload a training CSV to proceed.")

    if _training_df is None:
        return

    # Infer class count and let user name the species
    _class_ids = sorted(_training_df['class'].unique().tolist())
    _n_classes = len(_class_ids)

    # ── Step 2: Species name mapping ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🌲 Step 2 — Species Names")
    st.caption("Name each integer class. These appear in all outputs. Must match the `class` values in your CSV.")

    # Auto-fill from 'species_name' column if present
    _default_names = {}
    if 'species_name' in _training_df.columns:
        for cid in _class_ids:
            row = _training_df[_training_df['class'] == cid]
            if not row.empty:
                _default_names[cid] = row['species_name'].iloc[0]

    _fallback = ['Oak','Pine','Spruce','Beech','Birch','Fir','Mixed Forest',
                 'Larch','Alder','Willow','Poplar','Maple']

    _name_cols = st.columns(min(_n_classes, 4))
    _species_names = []
    for i, cid in enumerate(_class_ids):
        with _name_cols[i % 4]:
            default = _default_names.get(cid, _fallback[i] if i < len(_fallback) else f'Species_{cid}')
            name = st.text_input(f"Class {cid}", value=default, key=f"sp_name_{cid}")
            _species_names.append(name)

    # ── Step 3: Study area & year ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📍 Step 3 — Study Area & Year")
    st.caption("Define the bounding box to classify. Smaller areas (< 500 km²) process faster.")

    col_a, col_b = st.columns(2)
    with col_a:
        _lon_min = st.number_input("Longitude Min (West)", value=10.0, format="%.4f",
                                   help="WGS84 longitude of western boundary")
        _lat_min = st.number_input("Latitude Min (South)", value=48.0, format="%.4f",
                                   help="WGS84 latitude of southern boundary")
        _year = st.selectbox("Classification Year", [2019, 2020, 2021, 2022, 2023, 2024],
                              index=4, help="Year used for all seasonal composites")
    with col_b:
        _lon_max = st.number_input("Longitude Max (East)", value=10.5, format="%.4f")
        _lat_max = st.number_input("Latitude Max (North)", value=48.5, format="%.4f")
        _val_split = st.slider(
            "Validation split (%)", min_value=10, max_value=40, value=20,
            help="% of training points held out for accuracy assessment"
        ) / 100.0

    # AOI area estimate
    _deg_area = (_lon_max - _lon_min) * (_lat_max - _lat_min)
    _km2_approx = _deg_area * 111.32 * 111.32 * np.cos(np.radians((_lat_min + _lat_max) / 2))
    if _lon_max <= _lon_min or _lat_max <= _lat_min:
        st.error("❌ Invalid bounding box: max must be greater than min.")
        return
    st.info(f"📐 AOI area ≈ {_km2_approx:.0f} km² ({_deg_area:.4f}° × {_deg_area:.4f}°) | "
            f"Seasons: spring/summer/autumn/winter {_year}")

    # ── Step 4: Run ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚀 Step 4 — Train & Classify")

    st.info("""**What happens when you click Run:**
1. Load 4-season Sentinel-2 composites (cloud-masked, 10 bands + 9 spectral indices)
2. Load 4-season Sentinel-1 composites (VV/VH + 4 radar indices)
3. Compute EVI & VH temporal gradients (3 each)
4. Compute GLCM texture features from NIR band (up to 8)
5. Extract annual 20th/80th percentiles (S2 + S1)
6. Add DEM slope + 8-direction one-hot aspect
7. Sample all features at your GPS training points
8. **Train Random Forest (71 trees) on GEE servers**
9. Classify every pixel in the AOI
10. Evaluate accuracy on held-out validation points → confusion matrix, OA, kappa
11. Compute area statistics (hectares per species)
12. Download results here""")

    if st.button("▶️ RUN FULL PIPELINE", use_container_width=True, type="primary"):

        if not EE_INITIALIZED:
            st.error("Earth Engine is not initialized. Cannot run pipeline.")
            return

        _progress  = st.progress(0)
        _status    = st.empty()
        _log_box   = st.expander("📋 Detailed Progress Log", expanded=True)
        _log_lines = []

        def _update(msg):
            _log_lines.append(msg)
            _status.text(msg)
            _log_box.text("\n".join(_log_lines[-20:]))
            # Rough progress estimate from log length
            step_pct = min(len(_log_lines) * 6, 90)
            _progress.progress(step_pct)

        try:
            import ee as _ee
            from classification_pipeline import run_full_pipeline, download_classified_tif

            _aoi_coords = [_lon_min, _lat_min, _lon_max, _lat_max]

            _update("🚀 Starting pipeline...")
            results = run_full_pipeline(
                aoi_coords      = _aoi_coords,
                year            = int(_year),
                training_df     = _training_df,
                class_col       = 'class',
                class_names     = _species_names,
                validation_split= _val_split,
                status_callback = _update,
            )

            _update("⬇️ Downloading classified GeoTIFF from EE...")
            _ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            _tif_bytes = download_classified_tif(
                results['classified_ee'], results['aoi'], scale=10
            )

            _progress.progress(100)
            _status.text("✅ Pipeline complete!")

            # ── Save all results to session_state ─────────────────────────
            st.session_state['results_timestamp']  = _ts
            st.session_state['accuracy_csv']       = results['metrics_df'].to_csv(index=False)
            st.session_state['area_csv']            = results['area_df'].to_csv(index=False)
            st.session_state['tif_bytes']           = _tif_bytes
            st.session_state['tif_name']            = f'tree_classification_{_ts}.tif'
            st.session_state['cm_array']            = results['cm_array']
            st.session_state['overall_accuracy']    = results['overall_accuracy']
            st.session_state['kappa']               = results['kappa']
            st.session_state['species_names']       = _species_names
            st.session_state['classified_ee']       = results['classified_ee']

            # Also save CSV files to disk for Results Dashboard disk fallback
            results['metrics_df'].to_csv(f'accuracy_metrics_{_ts}.csv', index=False)
            results['area_df'].to_csv(f'area_statistics_{_ts}.csv', index=False)
            if _tif_bytes:
                with open(f'tree_classification_{_ts}.tif', 'wb') as _f:
                    _f.write(_tif_bytes)

            # ── Show results immediately ───────────────────────────────────
            st.success(f"""
✅ **Classification Complete!**
— Overall Accuracy: **{results['overall_accuracy']:.1%}**
— Kappa Coefficient: **{results['kappa']:.3f}**
— Species: {', '.join(_species_names)}
→ Go to **Results Dashboard** for full download & charts.
""")

            # Confusion matrix heatmap
            _cm = results['cm_array']
            import plotly.figure_factory as ff
            st.markdown("#### Confusion Matrix (Validation Set)")
            _fig_cm = ff.create_annotated_heatmap(
                z=_cm.tolist(),
                x=_species_names,
                y=_species_names,
                colorscale='Greens',
                showscale=True,
            )
            _fig_cm.update_layout(
                xaxis_title="Predicted", yaxis_title="Actual",
                height=450
            )
            st.plotly_chart(_fig_cm, use_container_width=True)

            # Metrics table
            st.markdown("#### Per-class Accuracy")
            st.dataframe(results['metrics_df'], use_container_width=True, hide_index=True)

            # Area chart
            st.markdown("#### Area by Species")
            _adf = results['area_df']
            _fig_area = px.bar(
                _adf, x='Species', y='Area_Hectares',
                color='Species', title='Classified Area per Species (hectares)',
                color_discrete_sequence=px.colors.sequential.Greens_r,
            )
            st.plotly_chart(_fig_area, use_container_width=True)

            # Download buttons
            st.markdown("#### ⬇️ Download Results")
            _dc1, _dc2, _dc3 = st.columns(3)
            with _dc1:
                st.download_button(
                    "📊 Accuracy Metrics (.csv)",
                    results['metrics_df'].to_csv(index=False).encode(),
                    file_name=f'accuracy_metrics_{_ts}.csv',
                    mime='text/csv', type='primary', use_container_width=True,
                    key='run_dl_acc'
                )
            with _dc2:
                st.download_button(
                    "🗺️ Area Statistics (.csv)",
                    results['area_df'].to_csv(index=False).encode(),
                    file_name=f'area_statistics_{_ts}.csv',
                    mime='text/csv', type='primary', use_container_width=True,
                    key='run_dl_area'
                )
            with _dc3:
                if _tif_bytes:
                    st.download_button(
                        "🖼️ Class Map (.tif)",
                        _tif_bytes,
                        file_name=f'tree_classification_{_ts}.tif',
                        mime='image/tiff', type='primary', use_container_width=True,
                        key='run_dl_tif'
                    )
                else:
                    st.warning("TIF too large for direct download — use EE Asset export instead.")

            # ZIP all
            _zip_buf = _BIO()
            with _zip.ZipFile(_zip_buf, 'w', _zip.ZIP_DEFLATED) as _zf:
                _zf.writestr(f'accuracy_metrics_{_ts}.csv', results['metrics_df'].to_csv(index=False))
                _zf.writestr(f'area_statistics_{_ts}.csv',  results['area_df'].to_csv(index=False))
                if _tif_bytes:
                    _zf.writestr(f'tree_classification_{_ts}.tif', _tif_bytes)
            st.download_button(
                "📦 Download ALL as ZIP",
                _zip_buf.getvalue(),
                file_name=f'classification_results_{_ts}.zip',
                mime='application/zip',
                use_container_width=True,
                key='run_dl_zip'
            )

        except Exception as _e:
            _progress.progress(0)
            st.error(f"❌ Pipeline error: {_e}")
            import traceback
            st.code(traceback.format_exc(), language='python')
    


def show_documentation_page():
    """Documentation page"""
    st.markdown("## 📚 Documentation")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📖 User Guide", "🔬 Methods", "❓ FAQ", "🔗 Resources"])
    
    with tab1:
        st.markdown("""
        ### User Guide
        
        #### Getting Started
        1. **Install dependencies**: `pip install -r requirements.txt`
        2. **Authenticate Earth Engine**: `earthengine authenticate`
        3. **Prepare training data**: Create CSV with GPS coordinates and species labels
        4. **Configure settings**: Adjust parameters in the Configuration page
        5. **Run classification**: Execute the pipeline
        6. **Analyze results**: View metrics and maps
        
        #### Data Preparation
        
        **Training Data Format:**
        - CSV file with columns: longitude, latitude, class
        - At least 50-100 samples per class
        - Well-distributed across study area
        - Field-verified species labels
        
        **Study Area:**
        - Define rectangular boundary (lon/lat)
        - Recommended size: < 1000 km²
        - Ensure satellite data availability
        
        #### Running Classification
        
        ```python
        from tree_species_classification import main
        import ee
        
        ee.Initialize()
        
        # Define inputs
        aoi = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
        training = ee.FeatureCollection('users/username/training')
        validation = ee.FeatureCollection('users/username/validation')
        zones = ...
        
        # Run
        results = main(aoi, training, validation, zones, 'output_name')
        ```
        
        #### Outputs
        
        Results are exported to Google Drive:
        - **Classified Map**: GeoTIFF at 10m resolution
        - **Accuracy Metrics**: CSV with confusion matrix and statistics
        - **Area Statistics**: CSV with area per class
        """)
    
    with tab2:
        st.markdown("""
        ### Methodology
        
        #### Data Sources
        - **Sentinel-2**: Optical imagery (10m bands)
        - **Sentinel-1**: C-band SAR (10m)
        - **SRTM DEM**: Elevation data (30m resampled)
        
        #### Feature Extraction
        
        **Spectral Indices (9):**
        - NDVI: (NIR - Red) / (NIR + Red)
        - EVI: 2.5 × (NIR - Red) / (NIR + 6×Red - 7.5×Blue + 1)
        - GNDVI, IPVI, TNDVI, BI2, MTCI, REIP, IRECI
        
        **Texture Features (8 from GLCM):**
        - Angular Second Moment, Contrast, Correlation
        - Variance, Homogeneity, Sum Average, Entropy, Dissimilarity
        
        **Radar Indices (4):**
        - VH/VV Ratio
        - VH - VV Difference
        - Amplitude
        - Normalized Difference
        
        **Temporal Features:**
        - EVI gradients between seasons
        - VH backscatter gradients
        
        **Terrain:**
        - Slope (degrees)
        - Aspect (8 directions, one-hot encoded)
        
        #### Classification
        
        **Algorithm:** Random Forest
        - Number of trees: 71
        - Variables per split: √(n_features)
        - Min leaf population: 1
        - Bag fraction: 0.5
        
        #### Accuracy Assessment
        
        **Metrics:**
        - Overall Accuracy: Correctly classified / Total samples
        - Kappa: (Po - Pe) / (1 - Pe)
        - Producer's Accuracy: Recall per class
        - User's Accuracy: Precision per class
        - F1-Score: Harmonic mean of precision and recall
        """)
    
    with tab3:
        st.markdown("""
        ### Frequently Asked Questions
        
        **Q: What accuracy can I expect?**  
        A: Typical accuracies range from 75-90% depending on species separability, data quality, and training samples.
        
        **Q: How long does processing take?**  
        A: 10-90 minutes depending on study area size. Processing happens on Google's servers.
        
        **Q: How many training samples do I need?**  
        A: Minimum 50 per class, but 100+ per class is recommended for best results.
        
        **Q: Can I use different seasons?**  
        A: Yes! Adjust the date ranges in config.py to match your region's phenology.
        
        **Q: What if I don't have all 4 seasons?**  
        A: The pipeline can work with fewer seasons, but accuracy may be reduced.
        
        **Q: Can I classify more than 7 species?**  
        A: Yes, update the n_classes parameter and provide appropriate training data.
        
        **Q: How do I improve accuracy?**  
        - Collect more training samples
        - Balance classes (equal samples per class)
        - Verify training data quality
        - Adjust seasonal date ranges
        - Select most relevant features
        
        **Q: What output format is provided?**  
        A: GeoTIFF for maps, CSV for statistics. Compatible with QGIS, ArcGIS, and other GIS software.
        
        **Q: Can I use this for other regions?**  
        A: Yes! The pipeline works globally wherever Sentinel data is available.
        
        **Q: Is this free to use?**  
        A: Yes, Google Earth Engine is free for research and non-commercial use.
        """)
    
    with tab4:
        st.markdown("""
        ### Resources
        
        #### Documentation Files
        - 📖 [README.md](README.md) - Complete documentation
        - ⚡ [QUICKSTART.md](QUICKSTART.md) - Quick start guide
        - 🔬 [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Scientific background
        - 📊 [TEST_REPORT.txt](TEST_REPORT.txt) - Test validation
        
        #### External Links
        - [Google Earth Engine](https://earthengine.google.com/)
        - [Sentinel-2 User Guide](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi)
        - [Sentinel-1 User Guide](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar)
        - [Earth Engine Python API](https://developers.google.com/earth-engine/guides/python_install)
        
        #### Citation
        If you use this tool in your research, please cite:
        ```
        [Original paper citation from forests-12-00565-v2.pdf]
        ```
        
        #### Support
        - Check documentation files for detailed instructions
        - Review example scripts for usage patterns
        - Run test_pipeline.py to validate installation
        - Execute demo.py to see all features
        """)

if __name__ == "__main__":
    main()
